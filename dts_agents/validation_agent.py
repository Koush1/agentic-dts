from typing import Callable
from agent import Agent
from agent_tools import AgentTools
from workspace import WorkspaceManager

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
            "You are an expert Data Plane Development Kit Test Suite (DTS) verifier.\n"
            "When given a relative file path and code snippet, your goal is to validate "
            "it using the `validate_code` tool.\n"
            "Always invoke the `validate_code` tool to check syntax and formatting, "
            "and then explain the result back to the user.\n"
            "CRITICAL: Ensure every response ends in the following format:"
            "VERDICT: PASS or VERDICT: FAIL based on the result of the validate_code tool."
        )

    def tools(self) -> list[Callable]:
        # validations specific tools
        validation_tools = [self.tool_instance.validate_code]
        return validation_tools + self._custom_tools
