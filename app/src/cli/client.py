from app.src.config.agent_factory import AgentFactory
from app.src.orchestration.orchestrated_codegen import CodeGenUnit
from app.src.config.ui import AgentUI
from app.utils.ascii_art import ASCII_ART
from app.utils.constants import CONSOLE_WIDTH, UI_MESSAGES
from rich.console import Console
import sys
import os
import textwrap


class CLI:
    """Command-line interface for the project generation system."""

    def __init__(
        self,
        mode: str = "coding",
        stream: bool = True,
        config: dict = None,
        api_key: str = None,
        codegen_model_name: str = None,
        brainstormer_model_name: str = None,
        web_searcher_model_name: str = None,
        codegen_api_key: str = None,
        brainstormer_api_key: str = None,
        web_searcher_api_key: str = None,
        codegen_temperature: float = None,
        brainstormer_temperature: float = None,
        web_searcher_temperature: float = None,
        codegen_system_prompt: str = None,
        brainstormer_system_prompt: str = None,
        web_searcher_system_prompt: str = None,
    ):
        self.mode = mode
        self.stream = stream
        self.config = config
        self.console = Console(width=CONSOLE_WIDTH)
        self.ui = AgentUI(self.console)

        if mode == "coding":
            self._validate_coding_config(
                api_key=api_key,
                codegen_model=codegen_model_name,
                brainstormer_model=brainstormer_model_name,
                web_searcher_model=web_searcher_model_name,
                codegen_api_key=codegen_api_key,
                brainstormer_api_key=brainstormer_api_key,
                web_searcher_api_key=web_searcher_api_key,
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

    def _validate_coding_config(
        self,
        api_key,
        codegen_model,
        brainstormer_model,
        web_searcher_model,
        codegen_api_key,
        brainstormer_api_key,
        web_searcher_api_key,
    ):
        """Validate required configuration for coding mode."""
        
        if not api_key and not all(
            [codegen_api_key, brainstormer_api_key, web_searcher_api_key]
        ):
            raise ValueError(
                "API key must be provided either as 'api_key' or individual agent API keys"
            )

        if not all([codegen_model, brainstormer_model, web_searcher_model]):
            raise ValueError(
                "Model names must be provided for all agents in coding mode"
            )

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
        """Setup configuration for coding mode."""
        
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

    def start_chat(self):
        """Start the main chat interface."""
        
        self.ui.logo(ASCII_ART)
        self.ui.help()

        try:
            active_dir = self._setup_environment()

            if self.mode != "coding":
                return

            self.ui.tmp_msg("Initializing agents...", duration=1)
            codegen_unit_success = self._run_codgen_unit(active_dir)

            if not codegen_unit_success:
                self.ui.error(
                    "Code generation workflow failed to complete successfully"
                )
                sys.exit(1)

        except KeyboardInterrupt:
            self.ui.goodbye()
        except Exception as e:
            self.ui.error(f"An unexpected error occurred: {e}")

    def _setup_environment(self) -> str:
        """Setup working environment and configuration."""
        
        active_dir = self._setup_directory()

        if self.mode == "coding":
            self._display_model_config()
            if self.ui.confirm(UI_MESSAGES["change_models"], default=False):
                self._update_models()

        return active_dir

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

    def _run_codgen_unit(self, working_dir: str) -> bool:
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
                config=self.config,
                stream=self.stream,
                show_welcome=False,
                working_dir=working_dir,
            )

        except Exception as e:
            self.ui.error(f"Failed to initialize coding workflow: {e}")
            return False
