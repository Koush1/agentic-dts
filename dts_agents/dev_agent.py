from dotenv import load_dotenv
from agent import Agent
from agent_tools import AgentTools

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
            "You are an expert Data Plane Development Kit Test Suite (DTS) developer.\n"
            "EFFICIENT TOOL USE GUIDELINES:\n"
            "1. Always query `vector_search` first.\n"
            "2. Be efficient with tool calls, only use when necessary and extract"
            "as much information as possible from each call."
        )

    def tools(self):
        # dev specific tools
        dev_tools = [self.tool_instance.vector_search, self.tool_instance.generate_patch] # , self.tool_instance.read_file
        return dev_tools + self._custom_tools
