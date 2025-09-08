from app.src.orchestration.integrate_web_search import integrate_web_search
from app.src.orchestration.units.orchestrated_codegen import CodeGenUnit
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
        provider: str = None,
        provider_per_model: dict[str, str] = None,
        models: dict[str, str] = None,
        api_key: str = None,
        api_key_per_model: dict[str, str] = None,
        temperatures: dict[str, float] = None,
        system_prompts: dict[str, str] = None,
        stream: bool = True,
    ):
        self.stream = stream
        self.console = Console(width=CONSOLE_WIDTH)
        self.ui = AgentUI(self.console)

        models = models or {}
        api_key_per_model = api_key_per_model or {}
        temperatures = temperatures or {}
        system_prompts = system_prompts or {}
        provider_per_model = provider_per_model or {}

        try:
            self.general_agent: BaseAgent = AgentFactory.create_agent(
                agent_type="general",
                config={
                    "model_name": models.get("general"),
                    "api_key": api_key_per_model.get("general") or api_key,
                    "temperature": temperatures.get("general"),
                    "system_prompt": system_prompts.get("general"),
                    "provider": provider_per_model.get("general") or provider,
                },
            )
            self.default_web_searcher_agent: BaseAgent = AgentFactory.create_agent(
                agent_type="web_searcher",
                config={
                    "model_name": models.get("web_searcher"),
                    "api_key": api_key_per_model.get("web_searcher") or api_key,
                    "temperature": temperatures.get("web_searcher"),
                    "system_prompt": system_prompts.get("web_searcher"),
                    "provider": provider_per_model.get("web_searcher") or provider,
                },
            )
        except Exception as e:
            self.ui.error(f"Failed to initialize default agents: {e}")

        try:
            self._validate_config(
                api_key=api_key,
                models=models,
                api_key_per_model=api_key_per_model,
            )
        except ValueError as ve:
            self.ui.error(f"Configuration error: {ve}")
            sys.exit(1)
        except Exception as e:
            self.ui.error(f"Failed to validate configuration: {e}")
            sys.exit(1)
        
        try:
            self._setup_coding_config(
                api_key=api_key,
                models=models,
                api_key_per_model=api_key_per_model,
                temperatures=temperatures,
                system_prompts=system_prompts,
                provider=provider,
                provider_per_model=provider_per_model,
            )
        except ValueError as ve:
            self.ui.error(f"Configuration error: {ve}")
            sys.exit(1)
        except Exception as e:
            self.ui.error(f"Failed to setup coding configuration: {e}")
            sys.exit(1)

    def _validate_config(
        self,
        api_key,
        models,
        api_key_per_model,
    ):
        """Validate required configuration for coding."""

        if not api_key and not all(
            [
                api_key_per_model.get("code_gen"),
                api_key_per_model.get("brainstormer"),
                api_key_per_model.get("web_searcher"),
                api_key_per_model.get("general"),
            ]
        ):
            raise ValueError(
                "API key must be provided either as 'api_key' or individual agent API keys"
            )

        if not all(
            [
                models.get("code_gen"),
                models.get("brainstormer"),
                models.get("web_searcher"),
                models.get("general"),
            ]
        ):
            raise ValueError("Model names must be provided for all agents in coding")

    def _setup_coding_config(
        self,
        api_key,
        models,
        api_key_per_model,
        temperatures,
        system_prompts,
        provider,
        provider_per_model,
    ):
        """Setup configuration for coding."""

        self.model_names = {
            "code_gen": models.get("code_gen"),
            "brainstormer": models.get("brainstormer"),
            "web_searcher": models.get("web_searcher"),
        }

        self.api_keys = {
            "code_gen": api_key_per_model.get("code_gen") or api_key,
            "brainstormer": api_key_per_model.get("brainstormer") or api_key,
            "web_searcher": api_key_per_model.get("web_searcher") or api_key,
        }

        self.temperatures = {
            "code_gen": temperatures.get("code_gen") or 0,
            "brainstormer": temperatures.get("brainstormer") or 0.7,
            "web_searcher": temperatures.get("web_searcher") or 0,
        }

        self.system_prompts = {
            "code_gen": system_prompts.get("code_gen"),
            "brainstormer": system_prompts.get("brainstormer"),
            "web_searcher": system_prompts.get("web_searcher"),
        }

        self.providers = {
            "code_gen": provider_per_model.get("code_gen") or provider,
            "brainstormer": provider_per_model.get("brainstormer") or provider,
            "web_searcher": provider_per_model.get("web_searcher") or provider,
        }

    def start_chat(self, *args):
        """Start the main chat interface."""

        try:
            active_dir, initial_prompt = self._setup_environment(args)
            
            self.ui.logo(ASCII_ART)
            self.ui.help()

            wd_note = f"## IMPORTANT\nALWAYS place your work inside {active_dir} unless stated otherwise by the user.\n"

            # making the project generation a command for the general agent
            self.general_agent.register_command(
                "/project", lambda: self.launch_coding_units()
            )

            # giving the general agent access to the web with a separate web searcher agent
            integrate_web_search(self.general_agent, self.default_web_searcher_agent)

            self.general_agent.start_chat(
                starting_msg=initial_prompt,
                initial_prompt_suffix=wd_note,
                show_welcome=False,
                active_dir=active_dir,
                stream=self.stream,
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

            self.ui.tmp_msg("Initializing agents...", duration=0.5)
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

            if parsed_args.d:
                if parsed_args.d == '.':
                    parsed_args.d = os.getcwd()
                elif not validate_dir_name(parsed_args.d):
                    self.ui.error(f"Invalid directory name: {parsed_args.d}")
                    sys.exit(1)
                active_dir = parsed_args.d

            if parsed_args.allow_all_tools:
                permission_manager.always_allow = True

            if parsed_args.p:
                initial_prompt = parsed_args.p

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
                providers=self.providers,
            )

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

        except Exception as e:
            self.ui.error(f"Failed to initialize coding workflow: {e}")
            return False
