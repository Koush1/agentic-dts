from dotenv import load_dotenv
from agent import Agent
from agent_tools import AgentTools

load_dotenv()

class DevAgent(Agent):

    def __init__(
            self,
            repo_path: str | None = None,
            custom_tools: list | None = None,
    ):

        self.repo_path = repo_path
        self.tool_instance = AgentTools()
        self._custom_tools = custom_tools or []
        super().__init__()

    def system_instruction(self) -> str:
        return (
            "You are an expert Data Plane Development Kit Test Suite (DTS) developer.\n"
            "EFFICIENT TOOL USE GUIDELINES:\n"
            "1. Always query `vector_search` first.\n"
            "2. Review the returned code snippets thoroughly. If they contain enough information "
            "to answer the user query, answer immediately without making extra tool calls.\n"
            "3. Only use `read_file` if vector snippets are truncated or lack necessary file context."
        )

    def tools(self):
        # dev specific tools
        dev_tools = [self.tool_instance.vector_search, self.tool_instance.read_file, self.tool_instance.generate_patch()]
        return dev_tools + self._custom_tools


# if __name__ == "__main__":
#     import logging
#
#     # Setup basic logging to monitor agent activity
#     logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
#
#     print("=== Initializing DevAgent MVP ===")
#
#     # Instantiate agent (reads DEEPTHOUGHT_API_KEY from .env automatically)
#     agent = DevAgent()
#
#     # 1. Inspect registered tools to verify automatic schema generation
#     print("\n=== Registered Tools & Schemas ===")
#     for tool_name, schema in zip(agent._tool_registry.keys(), agent._openai_tools_schema):
#         print(f"  • Tool: {tool_name}")
#         print(f"    Schema: {schema}\n")
#
#     # 2. Run a prompt designed to trigger a tool call
#     test_prompt = "Can you tell me everything i need to know about the traffic generators used in dts"
#     print(f"=== Running Agent Turn ===")
#     print(f"User Prompt: {test_prompt}\n")
#
#     try:
#         final_response = agent.run_turn(test_prompt)
#         print("=== Final Agent Output ===")
#         print(final_response)
#     except Exception as e:
#         print(f"❌ Error during execution: {e}")