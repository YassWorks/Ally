from app.src.core.ui import default_ui


class PermissionManager:
    def __init__(self):
        self.ui = default_ui
        self.always_allow = False
        self.always_allowed_tools = set()

    def get_permission(self, tool_name: str = None, **kwargs) -> bool:
        if self.always_allow:
            return True
        if tool_name in self.always_allowed_tools:
            return True

        message = f"\n[{self.ui._style('primary')}]Attempting to call [/{self.ui._style('primary')}]'{tool_name}'"
        self.ui.console.print(message)

        options = self._get_options(tool_name=tool_name)
        idx = self.ui.select_option(message="", options=options)

        if idx is None:
            self.ui.warning(
                "Could not ask for permission here, so the tool was not run. "
                "Start Ally with --allow-all-tools to run tools without asking."
            )
            return False
        if idx == 0:
            return True
        if idx == 2:
            self.always_allowed_tools.add(tool_name)
            return True
        if idx == 3:
            self.always_allow = True
            return True
        return False

    def _get_options(self, tool_name: str) -> list[str]:
        return [
            "Yes, allow once",
            "No, deny access (request modifications)",
            f"Yes, always allow this tool ({tool_name}) to run",
            "Yes, always allow all tools to run freely (USE AT YOUR OWN RISK)",
        ]


class PermissionDeniedException(Exception): ...


permission_manager = PermissionManager()
