from dotenv import load_dotenv
from .agent import Agent
from .agent_tools import AgentTools

load_dotenv()

class DevAgent(Agent):

    def __init__(
            self,
            workspace_path: str | None = None,
            custom_tools: list | None = None,
    ):

        self.repo_path = workspace_path
        self.tool_instance = AgentTools(workspace_path=workspace_path)
        self._custom_tools = custom_tools or []
        super().__init__()

    def system_instruction(self) -> str:
        return (
            "You are an expert Data Plane Development Kit (DPDK) Test Suite (DTS) developer.\n\n"
            "EFFICIENT TOOL USE GUIDELINES:\n"
            "1. SCOUT: Use `vector_search` ONLY to find relevant file paths, classes, or to understand architectural context. Do not use it to read entire files.\n"
            "2. INSPECT: Once you know the target file path, use `read_file` to pull the exact source code into your context.\n"
            "3. SURGERY: To modify an existing file, use `edit_file`. Your `old_contents` argument MUST match the file's current text exactly (including all indentation and spacing).\n"
            "4. CREATION: Only use `write_file` if you are creating a brand new file from scratch.\n"
            "5. FRUGALITY: Be highly frugal with tool calls. Plan your actions and extract as much information as possible from a single call to avoid loops.\n"
            "6. FINAL RESPONSE: When your code changes are successfully saved to the workspace, output a brief conversational explanation of your fix. Do NOT output raw diffs, patches, or massive code blocks in your final chat response."
        )

    def tools(self):
        # dev specific tools
        dev_tools = [
            self.tool_instance.vector_search,
            self.tool_instance.edit_file,
            self.tool_instance.write_file,
            self.tool_instance.read_file
        ]
        return dev_tools + self._custom_tools
