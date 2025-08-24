from app.src.orchestration.integrate_web_search import integrate_web_search
from app.src.orchestration.orchestrated_codegen import CodeGenUnit
from app.utils.constants import CONSOLE_WIDTH, UI_MESSAGES
from app.src.config.permissions import permission_manager
from app.src.config.agent_factory import AgentFactory
from app.src.helpers.valid_dir import validate_dir_name
from app.utils.ascii_art import ASCII_ART
from app.src.config.base import BaseAgent
from app.src.cli.flags import ArgsParser
from app.src.config.ui import AgentUI
from rich.console import Console
import textwrap
import sys
import os


class CLI:
    """Command-line interface for the project generation system."""

    def __init__(
        self,
        stream: bool = True,
        config: dict = None,
        api_key: str = None,
        general_model_name: str = None,
        codegen_model_name: str = None,
        brainstormer_model_name: str = None,
        web_searcher_model_name: str = None,
        general_api_key: str = None,
        codegen_api_key: str = None,
        brainstormer_api_key: str = None,
        web_searcher_api_key: str = None,
        general_temperature: float = None,
        codegen_temperature: float = None,
        brainstormer_temperature: float = None,
        web_searcher_temperature: float = None,
        general_system_prompt: str = None,
        codegen_system_prompt: str = None,
        brainstormer_system_prompt: str = None,
        web_searcher_system_prompt: str = None,
    ):
        self.stream = stream
        self.config = config
        self.console = Console(width=CONSOLE_WIDTH)
        self.ui = AgentUI(self.console)

        self.general_agent: BaseAgent = AgentFactory.create_agent(
            agent_type="general",
            config={
                "model_name": general_model_name,
                "api_key": general_api_key or api_key,
                "temperature": general_temperature,
                "system_prompt": general_system_prompt,
            },
        )
        self.default_web_searcher_agent: BaseAgent = AgentFactory.create_agent(
            agent_type="web_searcher",
            config={
                "model_name": web_searcher_model_name,
                "api_key": web_searcher_api_key or api_key,
                "temperature": web_searcher_temperature,
                "system_prompt": web_searcher_system_prompt,
            },
        )

        self._validate_config(
            api_key=api_key,
            codegen_model=codegen_model_name,
            brainstormer_model=brainstormer_model_name,
            web_searcher_model=web_searcher_model_name,
            general_model=general_model_name,
            codegen_api_key=codegen_api_key,
            brainstormer_api_key=brainstormer_api_key,
            web_searcher_api_key=web_searcher_api_key,
            general_api_key=general_api_key,
        )
        self._setup_coding_config(
            api_key=api_key,
            codegen_model=codegen_model_name,
            brainstormer_model=brainstormer_model_name,
            web_searcher_model=web_searcher_model_name,
            codegen_api_key=codegen_api_key,
            brainstormer_api_key=brainstormer_api_key,
            web_searcher_api_key=web_searcher_api_key,
            codegen_temp=codegen_temperature,
            brainstormer_temp=brainstormer_temperature,
            web_searcher_temp=web_searcher_temperature,
            codegen_prompt=codegen_system_prompt,
            brainstormer_prompt=brainstormer_system_prompt,
            web_searcher_prompt=web_searcher_system_prompt,
        )

    def _validate_config(
        self,
        api_key,
        codegen_model,
        brainstormer_model,
        web_searcher_model,
        general_model,
        codegen_api_key,
        brainstormer_api_key,
        web_searcher_api_key,
        general_api_key,
    ):
        """Validate required configuration for coding."""

        if not api_key and not all(
            [
                codegen_api_key,
                brainstormer_api_key,
                web_searcher_api_key,
                general_api_key,
            ]
        ):
            raise ValueError(
                "API key must be provided either as 'api_key' or individual agent API keys"
            )

        if not all(
            [codegen_model, brainstormer_model, web_searcher_model, general_model]
        ):
            raise ValueError("Model names must be provided for all agents in coding")

    def _setup_coding_config(
        self,
        api_key,
        codegen_model,
        brainstormer_model,
        web_searcher_model,
        codegen_api_key,
        brainstormer_api_key,
        web_searcher_api_key,
        codegen_temp,
        brainstormer_temp,
        web_searcher_temp,
        codegen_prompt,
        brainstormer_prompt,
        web_searcher_prompt,
    ):
        """Setup configuration for coding."""

        self.model_names = {
            "code_gen": codegen_model,
            "brainstormer": brainstormer_model,
            "web_searcher": web_searcher_model,
        }

        self.api_keys = {
            "code_gen": codegen_api_key or api_key,
            "brainstormer": brainstormer_api_key or api_key,
            "web_searcher": web_searcher_api_key or api_key,
        }

        self.temperatures = {
            "code_gen": codegen_temp or 0,
            "brainstormer": brainstormer_temp or 0.7,
            "web_searcher": web_searcher_temp or 0,
        }

        self.system_prompts = {
            "code_gen": codegen_prompt,
            "brainstormer": brainstormer_prompt,
            "web_searcher": web_searcher_prompt,
        }

    def start_chat(self, *args):
        """Start the main chat interface."""

        try:
            active_dir, initial_prompt = self._setup_environment(args)

            self.ui.logo(ASCII_ART)
            self.ui.help()

            cwd_note = f"ALWAYS place your work inside {active_dir} unless stated otherwise by the user.\n"

            # making the project generation a command for the general agent
            self.general_agent.register_command(
                "/project", lambda: self.launch_coding_units()
            )

            # giving the general agent access to the web with a separate web searcher agent
            integrate_web_search(self.general_agent, self.default_web_searcher_agent)

            self.general_agent.start_chat(
                starting_msg=initial_prompt,
                initial_prompt_suffix=cwd_note,
                show_welcome=False,
            )

        except KeyboardInterrupt:
            self.ui.goodbye()
        except Exception as e:
            self.ui.error(f"An unexpected error occurred: {e}")

    def launch_coding_units(self, initial_prompt: str = None, active_dir: str = None):
        """Start the agent units that create full projects from scratch."""

        self._display_model_config()
        if self.ui.confirm(UI_MESSAGES["change_models"], default=False):
            self._update_models()

        try:
            if active_dir is None:
                active_dir = self._setup_directory()

            self.ui.tmp_msg("Initializing agents...", duration=1)
            codegen_unit_success = self._run_codegen_unit(
                initial_prompt=initial_prompt, working_dir=active_dir
            )

            if not codegen_unit_success:
                self.ui.error(
                    "Code generation workflow failed to complete successfully"
                )
                sys.exit(1)

        except KeyboardInterrupt:
            self.ui.goodbye()
        except Exception as e:
            self.ui.error(f"An unexpected error occurred: {e}")

    def _setup_environment(self, user_args: list[str] = None) -> str:
        """Setup working environment and configuration."""

        active_dir = None
        initial_prompt = None

        if user_args:
            parsed_args = ArgsParser.get_args(
                ui=self.ui,
                user_args=list(user_args),
            )

            if parsed_args.wd:
                if not validate_dir_name(parsed_args.wd):
                    self.ui.error(f"Invalid directory name: {parsed_args.wd}")
                    sys.exit(1)
                active_dir = parsed_args.wd

            if parsed_args.allow_all_tools:
                permission_manager.always_allow = True

            if parsed_args.msg:
                initial_prompt = parsed_args.msg

            if parsed_args.create_project:
                self.ui.logo(ASCII_ART)
                self.launch_coding_units(
                    initial_prompt=initial_prompt, active_dir=active_dir
                )
                sys.exit(0)

        if active_dir is None:
            active_dir = self._setup_directory()

        return active_dir, initial_prompt

    def _setup_directory(self) -> str:
        """Setup working directory with user interaction."""

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
                    self.ui.error("Failed to create directory")

            self.ui.status_message(
                title=UI_MESSAGES["titles"]["directory_updated"],
                message=f"Now working in {active_dir}",
                style="success",
            )

        return active_dir

    def _display_model_config(self):
        """Display current model configuration."""

        models_msg = f"""
            Brainstormer: [{self.ui._style("secondary")}]{self.model_names["brainstormer"]}[/{self.ui._style("secondary")}]
            Web Searcher: [{self.ui._style("secondary")}]{self.model_names["web_searcher"]}[/{self.ui._style("secondary")}]
            Coding:       [{self.ui._style("secondary")}]{self.model_names["code_gen"]}[/{self.ui._style("secondary")}]
        """
        models_msg = textwrap.dedent(models_msg)

        self.ui.status_message(
            title=UI_MESSAGES["titles"]["current_models"],
            message=models_msg,
            style="primary",
        )

    def _update_models(self):
        """Update model configuration based on user input."""

        agent_types = ["brainstormer", "web_searcher", "code_gen"]
        display_names = ["Brainstormer", "Web Searcher", "Coding"]

        for agent_type, display_name in zip(agent_types, display_names):
            new_model = self.ui.get_input(
                message=UI_MESSAGES["model_change_prompt"].format(display_name),
                default=self.model_names[agent_type],
            )
            self.model_names[agent_type] = new_model

    def _run_codegen_unit(self, working_dir: str, initial_prompt: str = None) -> bool:
        """Execute the coding workflow with proper error handling."""

        try:
            agents = AgentFactory.create_coding_agents(
                model_names=self.model_names,
                api_keys=self.api_keys,
                temperatures=self.temperatures,
                system_prompts=self.system_prompts,
            )

            codegen_unit = CodeGenUnit(
                code_gen_agent=agents["code_gen"],
                web_searcher_agent=agents["web_searcher"],
                brainstormer_agent=agents["brainstormer"],
            )

            return codegen_unit.run(
                prompt=initial_prompt,
                config=self.config,
                stream=self.stream,
                show_welcome=False,
                working_dir=working_dir,
            )

        except Exception as e:
            self.ui.error(f"Failed to initialize coding workflow: {e}")
            return False
