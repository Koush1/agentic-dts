from typing import Callable
from .agent import Agent
from .agent_tools import AgentTools
from .workspace import WorkspaceManager

class ValidationAgent(Agent):

    def __init__(
        self,
        repo_path: str | None = None,
        custom_tools: list | None = None,
    ):
        self.repo_path = repo_path
        self.tool_instance = AgentTools(WorkspaceManager.workspace_path)
        self._custom_tools = custom_tools or []
        super().__init__()

    def system_instruction(self) -> str:
        return (
            """You are an expert Data Plane Development Kit Test Suite (DTS) verifier.\n"
            "When given a relative file path and code snippet, your goal is to validate "
            "it using the `validate_code` tool.\n"
            "Always invoke the `validate_code` tool to check syntax and formatting, "
            "and then explain the result back to the user.\n"
            "CRITICAL: Ensure every response ends in VERDICT: PASS/FAIL based on the result of the validate_code tool."
            "If the validate_code tool ran properly then there should be a PASS, else a FAIL."""
        )

        "You are an expert Data Plane Development Kit Test Suite (DTS) code verifier and systems architect.\n\n"
        "Your objective is to perform a rigorous peer review of code changes made by the development agent. "
        "Since you do not have execution tools, rely on deep analytical reasoning to inspect the patch.\n\n"
        "### Review Checklist\n"
        "1. **Logical Correctness:** Verify control flow, branch exclusivity (e.g., proper use of `if/elif`), and state transitions.\n"
        "2. **Framework Safety:** Ensure proper handling of testbed resources, traffic generator bindings, and context cleanups.\n"
        "3. **DPDK/DTS Conventions:** Check that architecture patterns match existing framework conventions.\n"
        "4. **Regression Risk:** Evaluate whether the change introduces unintended side effects in adjacent execution states.\n\n"
        "### Response Structure\n"
        "- Provide a concise code review highlighting strengths, potential risks, or structural correctness.\n"
        "- Conclude your entire response with a clear evaluation tag on its own line: `VERDICT: PASS` (or `VERDICT: FAIL`)."



    def tools(self) -> list[Callable]:
        # validations specific tools
        validation_tools = [self.tool_instance.read_file, self.tool_instance.validate_code]
        return validation_tools + self._custom_tools
