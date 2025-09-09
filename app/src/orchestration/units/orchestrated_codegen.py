from app.src.orchestration.units.base_unit import BaseUnit
from app.src.config.exception_handler import AgentExceptionHandler
from app.src.orchestration.integrate_web_search import integrate_web_search
from app.utils.constants import UI_MESSAGES, CONTINUE_MESSAGE
from app.utils.ascii_art import ASCII_ART
from pathlib import Path
import uuid


PROMPTS_DIR = Path(__file__).resolve().parents[3]


class CodeGenUnit(BaseUnit):
    """Orchestrates multiple agents for complete project generation."""

    def __init__(self, code_gen_agent, web_searcher_agent, brainstormer_agent):
        agents = {
            "code_gen": code_gen_agent,
            "web_searcher": web_searcher_agent,
            "brainstormer": brainstormer_agent,
        }
        super().__init__(agents)

    def _validate_agents(self):
        """Validate that all required agents are present."""

        required_agents = ["code_gen", "web_searcher", "brainstormer"]
        for agent_name in required_agents:
            if agent_name not in self.agents or self.agents[agent_name] is None:
                raise ValueError(f"Missing required agent: {agent_name}")

    def run(
        self,
        prompt: str = None,
        recursion_limit: int = 100,
        config: dict = None,
        stream: bool = False,
        show_welcome: bool = True,
        working_dir: str = None,
    ) -> bool:
        """Execute the complete project generation workflow."""

        try:
            self._enhance_agents()

            if show_welcome:
                self.ui.logo(ASCII_ART)
                self.ui.help()

            working_dir = working_dir or self._setup_working_directory()

            user_input = (
                prompt
                or self.ui.get_input(
                    message=UI_MESSAGES["project_prompt"],
                    cwd=working_dir,
                ).strip()
            )

            return self._execute_generation_workflow(
                working_dir, user_input, recursion_limit, config, stream
            )

        except KeyboardInterrupt:
            self.ui.session_interrupted()
            return True
        except Exception as e:
            self.ui.error(f"Workflow execution failed: {e}")
            return False

    def _execute_generation_workflow(
        self,
        working_dir: str,
        user_input: str,
        recursion_limit: int,
        config: dict,
        stream: bool,
    ) -> bool:
        """Execute the main generation workflow steps."""

        brainstorming_thread_id = str(uuid.uuid4())
        code_generation_thread_id = str(uuid.uuid4())

        # Step 1: Context Engineering
        self._run_brainstorming_phase(
            working_dir=working_dir,
            user_input=user_input,
            recursion_limit=recursion_limit,
            config=config,
            stream=stream,
            thread_id=brainstorming_thread_id,
        )

        # Step 2: Optional additional context
        if not self._handle_additional_context(
            working_dir=working_dir,
            recursion_limit=recursion_limit,
            config=config,
            thread_id=brainstorming_thread_id,
        ):
            return False

        # Step 3: Code Generation
        self._run_code_generation_phase(
            working_dir=working_dir,
            user_input=user_input,
            recursion_limit=recursion_limit,
            stream=stream,
            thread_id=code_generation_thread_id,
        )

        # Step 4: Interactive coding session
        return self._run_interactive_session(
            recursion_limit=recursion_limit, thread_id=code_generation_thread_id
        )

    def _run_brainstorming_phase(
        self,
        working_dir: str,
        user_input: str,
        recursion_limit: int,
        config: dict,
        stream: bool,
        thread_id: str,
    ) -> bool:
        """Execute the brainstorming and context engineering phase."""

        brainstormer_prompt = self._create_brainstormer_prompt(user_input, working_dir)
        configuration = config or self._create_agent_config(thread_id, recursion_limit)

        AgentExceptionHandler.handle_agent_exceptions(
            operation=lambda: self.agents["brainstormer"].invoke(
                message=brainstormer_prompt,
                config=configuration,
                stream=stream,
                quiet=not stream,
                propagate_exceptions=True,
            ),
            ui=self.ui,
            propagate=False,
            continue_on_limit=True,
            retry_operation=lambda: self.agents["brainstormer"].invoke(
                message=CONTINUE_MESSAGE,
                config=configuration,
                stream=stream,
                quiet=not stream,
                propagate_exceptions=True,
            ),
        )

    def _run_code_generation_phase(
        self,
        working_dir: str,
        user_input: str,
        recursion_limit: int,
        stream: bool,
        thread_id: str,
    ) -> bool:
        """Execute the code generation phase."""

        self.ui.status_message(
            title=UI_MESSAGES["titles"]["generation_starting"],
            message="The CodeGen Agent is now generating code based on the context provided.",
            style="success",
        )

        codegen_prompt = self._create_codegen_prompt(user_input, working_dir)
        configuration = self._create_agent_config(thread_id, recursion_limit)

        AgentExceptionHandler.handle_agent_exceptions(
            operation=lambda: self.agents["code_gen"].invoke(
                message=codegen_prompt,
                config=configuration,
                stream=stream,
                quiet=not stream,
                propagate_exceptions=True,
            ),
            ui=self.ui,
            propagate=False,
            continue_on_limit=True,
            retry_operation=lambda: self.agents["code_gen"].invoke(
                message=CONTINUE_MESSAGE,
                config=configuration,
                stream=stream,
                quiet=not stream,
                propagate_exceptions=True,
            ),
        )

    def _handle_additional_context(
        self,
        working_dir: str,
        recursion_limit: int,
        config: dict,
        thread_id: str,
    ) -> bool:
        """Handle optional additional context gathering."""

        usr_answer = self.ui.get_input(
            message=UI_MESSAGES["add_context"],
            default="y",
            choices=["y", "n"],
            show_choices=True,
            cwd=working_dir,
            model=getattr(self.agents["brainstormer"], "model_name", "Brainstormer"),
        )

        if usr_answer in ["yes", "y", "yeah"]:
            self.ui.status_message(
                title=UI_MESSAGES["titles"]["brainstormer_ready"],
                message="Type '/exit' or press Ctrl+C to continue to code generation",
                style="accent",
            )

            configuration = config or self._create_agent_config(
                thread_id, recursion_limit
            )

            exited_safely = self.agents["brainstormer"].start_chat(
                config=configuration, show_welcome=False
            )

            if not exited_safely:
                if self.ui.confirm(
                    "Something went wrong during the brainstorming process. Do you wish to continue anyway?",
                    default=True,
                ):
                    return True
                else:
                    self.ui.goodbye()
                    return False

        return True

    def _run_interactive_session(
        self,
        recursion_limit: int,
        thread_id: str,
    ) -> bool:
        """Run the interactive coding session."""

        self.ui.status_message(
            title=UI_MESSAGES["titles"]["codegen_ready"],
            message="Starting interactive coding session with the coding agent...",
            style="accent",
        )

        configuration = self._create_agent_config(thread_id, recursion_limit)
        exited_safely = self.agents["code_gen"].start_chat(
            config=configuration, show_welcome=False
        )

        if not exited_safely:
            self.ui.error("The interactive coding session did not exit safely")
            return False

        return True

    def _create_brainstormer_prompt(self, user_input: str, working_dir: str) -> str:
        """Create the brainstormer prompt with context engineering steps."""

        ces_file_path = PROMPTS_DIR / "prompts" / "context_engineering_steps.txt"

        with open(str(ces_file_path), "r") as file:
            context_engineering_steps = file.read()

        return (
            f"\n\nIMPORTANT: Place your entire work inside {working_dir}\n\n"
            + context_engineering_steps
            + "\n\n# User input:\n"
            + user_input
            + f"\n\nIMPORTANT: Place your entire work inside {working_dir}"
        )

    def _create_codegen_prompt(self, user_input: str, working_dir: str) -> str:
        """Create the code generation prompt."""

        codegen_file_path = PROMPTS_DIR / "prompts" / "codegen_start.txt"

        with open(str(codegen_file_path), "r") as file:
            codegen_start = file.read()

        return (
            f"\n\nIMPORTANT: Place your entire work inside {working_dir}\n\n"
            + codegen_start
            + "\n\n# The original input that the user gave:\n"
            + user_input
            + f"\n\nIMPORTANT: Place your entire work inside {working_dir}"
        )

    def _enhance_agents(self):
        """Integrate web search capabilities into agents."""

        try:
            integrate_web_search(
                agent=self.agents["code_gen"],
                web_searcher=self.agents["web_searcher"],
            )
            integrate_web_search(
                agent=self.agents["brainstormer"],
                web_searcher=self.agents["web_searcher"],
            )
        except Exception as e:
            error_msg = f"Failed to integrate web search capabilities: {e}"
            self.ui.error(error_msg)
            raise RuntimeError(error_msg)
