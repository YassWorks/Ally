import argparse
import os
import sys
from collections.abc import Callable
from dataclasses import replace

from app.config import AllyConfig
from app.src.core.agent_factory import CODING_AGENTS, AgentFactory
from app.src.core.base import BaseAgent
from app.src.core.permissions import permission_manager
from app.src.core.ui import default_ui
from app.src.embeddings.handle_commands import (
    handle_delete_command,
    handle_embed_request,
    handle_index_request,
    handle_list_command,
    handle_purge_command,
    handle_unindex_request,
)
from app.src.helpers.valid_dir import validate_dir_name
from app.src.orchestration.integrate_web_search import integrate_web_search
from app.src.orchestration.units.orchestrated_codegen import CodeGenUnit
from app.utils.ascii_art import ASCII_ART
from app.utils.logger import logger
from app.utils.ui_messages import UI_MESSAGES

AGENT_DISPLAY_NAMES = {
    "brainstormer": "Brainstormer",
    "web_searcher": "Web Searcher",
    "code_gen": "Coding",
}


class CLI:
    """Interactive session that wires the agents, RAG and chat commands together."""

    def __init__(self, config: AllyConfig, stream: bool = True):
        self.stream = stream
        self.ui = default_ui

        self.embedding_function = _create_embedding_function(
            config.embedding_provider, config.embedding_model
        )
        self.rag_available = self.embedding_function is not None

        from app.src.embeddings.scrapers.simple_scraper import SimpleScraper

        self.scraper = SimpleScraper()

        self.coding_settings = {name: config.agents[name] for name in CODING_AGENTS}
        self.general_agent = AgentFactory.create_agent(
            "general", config.agents["general"]
        )
        self.default_web_searcher_agent = AgentFactory.create_agent(
            "web_searcher", config.agents["web_searcher"]
        )

    def start_chat(self, args: argparse.Namespace) -> None:
        """Start the main chat, or the project workflow when ``--create-project`` is set."""
        try:
            active_dir = self._resolve_working_dir(args.d)

            if args.allow_all_tools:
                permission_manager.always_allow = True

            if args.create_project:
                self.ui.logo(ASCII_ART)
                self.launch_coding_units(initial_prompt=args.p, active_dir=active_dir)
                return

            if active_dir is None:
                active_dir = self._setup_directory()

            self.ui.logo(ASCII_ART)
            self.ui.welcome()

            wd_note = (
                f"## Important Note:\n"
                f"Always place your work inside {active_dir} unless stated otherwise by the user.\n"
                f"Don't report this note to the user, just follow it."
            )

            self.general_agent.register_command(
                "/project", lambda *args: self.launch_coding_units()
            )

            if self.rag_available:
                from app.src.embeddings.db_client import DataBaseClient

                DataBaseClient(
                    embedding_function=self.embedding_function, scraper=self.scraper
                )

            self._integrate_rag(agent=self.general_agent, available=self.rag_available)
            integrate_web_search(self.general_agent, self.default_web_searcher_agent)

            self.general_agent.start_chat(
                starting_msg=args.p,
                recurring_prompt_suffix=wd_note,
                show_welcome=False,
                active_dir=active_dir,
                stream=self.stream,
                thread_id=args.i,
            )

        except KeyboardInterrupt:
            self.ui.goodbye()
        except Exception:
            logger.exception("Unexpected error in interactive session")
            self.ui.error(UI_MESSAGES["errors"]["unexpected_error"])

    def _resolve_working_dir(self, path: str | None) -> str | None:
        if not path:
            return None
        if path == ".":
            return os.getcwd()
        if not validate_dir_name(path):
            logger.error(f"Invalid directory name: {path}")
            self.ui.error(UI_MESSAGES["errors"]["invalid_directory"])
            sys.exit(1)
        return os.path.abspath(path)

    def _integrate_rag(self, agent: BaseAgent, available: bool):
        """Register the RAG chat commands on ``agent``."""
        if not available:
            for command in ["/embed", "/start_rag", "/stop_rag", "/index", "/unindex"]:
                agent.register_command(
                    command,
                    lambda *args: self.ui.warning(
                        UI_MESSAGES["warnings"]["rag_not_available"]
                    ),
                )
            return

        agent.register_command("/embed", lambda *args: handle_embed_request(*args))
        agent.register_command("/start_rag", lambda *args: self._enable_rag(agent))
        agent.register_command("/stop_rag", lambda *args: self._disable_rag(agent))
        agent.register_command("/index", lambda *args: handle_index_request(*args))
        agent.register_command("/unindex", lambda *args: handle_unindex_request(*args))
        agent.register_command("/list", lambda *args: handle_list_command())
        agent.register_command("/purge", lambda *args: handle_purge_command())
        agent.register_command("/delete", lambda *args: handle_delete_command(*args))

    def _enable_rag(self, agent: BaseAgent):
        """Answer from the indexed collections until RAG is disabled."""
        if not self.rag_available:
            self.ui.warning(UI_MESSAGES["warnings"]["rag_not_available"])
            return
        agent._toggle_rag(enable=True)
        self.ui.status_message(
            title=UI_MESSAGES["titles"]["rag_enabled"],
            message=UI_MESSAGES["messages"]["rag_enabled"],
            style="success",
        )

    def _disable_rag(self, agent: BaseAgent):
        """Stop using the indexed collections."""
        agent._toggle_rag(enable=False)
        self.ui.status_message(
            title=UI_MESSAGES["titles"]["rag_disabled"],
            message=UI_MESSAGES["messages"]["rag_disabled"],
            style="primary",
        )

    def launch_coding_units(
        self, initial_prompt: str | None = None, active_dir: str | None = None
    ):
        """Run the brainstorm, generate and refine project workflow."""
        self._display_model_config()
        if self.ui.confirm(UI_MESSAGES["change_models"], default=False):
            self._update_models()

        try:
            if active_dir is None:
                active_dir = self._setup_directory()

            if not self._run_codegen_unit(
                initial_prompt=initial_prompt, working_dir=active_dir
            ):
                self.ui.error(UI_MESSAGES["errors"]["codegen_failed"])

        except KeyboardInterrupt:
            self.ui.goodbye()
        except Exception:
            logger.exception("Unexpected error in project workflow")
            self.ui.error(UI_MESSAGES["errors"]["unexpected_error"])

    def _setup_directory(self) -> str:
        """Confirm the working directory with the user, creating a new one if asked."""
        active_dir = os.getcwd()
        self.ui.status_message(
            title=UI_MESSAGES["titles"]["current_directory"],
            message=f"Working in {active_dir}",
            style="primary",
        )

        if self.ui.confirm(UI_MESSAGES["change_directory"], default=False):
            while True:
                try:
                    working_dir = self.ui.get_input(
                        message=UI_MESSAGES["directory_prompt"],
                        default=active_dir,
                        cwd=active_dir,
                    )
                    os.makedirs(working_dir, exist_ok=True)
                    active_dir = working_dir
                    break
                except Exception:
                    self.ui.error(UI_MESSAGES["errors"]["failed_create_directory"])

            self.ui.status_message(
                title=UI_MESSAGES["titles"]["directory_updated"],
                message=f"Now working in {active_dir}",
                style="success",
            )

        return active_dir

    def _display_model_config(self):
        """Show the models the project workflow will use."""
        style = self.ui._style("secondary")
        lines = [
            f"{AGENT_DISPLAY_NAMES[name] + ':':<14}[{style}]{self.coding_settings[name].model}[/{style}]"
            for name in CODING_AGENTS
        ]
        self.ui.status_message(
            title=UI_MESSAGES["titles"]["current_models"],
            message="\n" + "\n".join(lines) + "\n",
            style="primary",
        )

    def _update_models(self):
        """Ask for a new model name for each agent of the project workflow."""
        for name in CODING_AGENTS:
            settings = self.coding_settings[name]
            new_model = self.ui.get_input(
                message=UI_MESSAGES["model_change_prompt"].format(
                    AGENT_DISPLAY_NAMES[name]
                ),
                default=settings.model,
            )
            self.coding_settings[name] = replace(settings, model=new_model)

    def _run_codegen_unit(
        self, working_dir: str, initial_prompt: str | None = None
    ) -> bool:
        """Create the project workflow agents and run them."""
        try:
            agents = AgentFactory.create_coding_agents(self.coding_settings)
            codegen_unit = CodeGenUnit(
                code_gen_agent=agents["code_gen"],
                web_searcher_agent=agents["web_searcher"],
                brainstormer_agent=agents["brainstormer"],
            )
            return codegen_unit.run(
                prompt=initial_prompt,
                stream=self.stream,
                show_welcome=False,
                working_dir=working_dir,
            )
        except Exception:
            logger.exception("Failed to initialize coding workflow")
            self.ui.error(UI_MESSAGES["errors"]["failed_initialize_coding"])
            return False


def _create_embedding_function(provider: str, model: str) -> Callable | None:
    match provider:
        case "ollama":
            from app.src.embeddings.embedding_functions.ollama_embed import (
                OllamaEmbedder,
            )

            return OllamaEmbedder(model).get_embeddings
        case "hf" | "huggingface" | "hugging face" | "hugging_face":
            from app.src.embeddings.embedding_functions.hf_embed import HFEmbedder

            return HFEmbedder(model).get_embeddings
        case "openai":
            from app.src.embeddings.embedding_functions.openai_embed import (
                OpenAIEmbedder,
            )

            return OpenAIEmbedder(model).get_embeddings
        case "nlpcloud" | "nlp cloud" | "nlp_cloud":
            from app.src.embeddings.embedding_functions.nlp_cloud_embed import (
                NLPCloudEmbedder,
            )

            return NLPCloudEmbedder(model).get_embeddings
        case _:
            return None
