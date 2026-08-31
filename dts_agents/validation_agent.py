from typing import Callable
from agent import Agent
from agent_tools import AgentTools

class ValidationAgent(Agent):

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
            "You are an expert Data Plane Development Kit Test Suite (DTS) verifier.\n"
            "When given a relative file path and code snippet, your goal is to validate "
            "it using the `validate_code` tool.\n"
            "Always invoke the `validate_code` tool to check syntax and formatting, "
            "and then explain the result back to the user."
        )

    def tools(self) -> list[Callable]:
        # validations specific tools
        validation_tools = [self.tool_instance.validate_code]
        return validation_tools + self._custom_tools


# if __name__ == "__main__":
#     import os
#
#     print("=== Executing ValidationAgent via LLM API Endpoint ===")
#
#     # 1. Instantiate the agent (picks up API key & endpoint from config or kwargs)
#     agent = ValidationAgent()
#
#     # 2. Construct a prompt containing target file path and code snippet
#     target_rel_path = "framework/test_run.py"
#     code_to_validate = '''def verify_port_configuration(port_id: int) -> bool:
#     """Verifies port setup for traffic generator."""
#     if port_id < 0:
#         return False
#     return True
# '''
#
#     prompt = (
#         f"Please validate the following code block for the file '{target_rel_path}':\n\n"
#         f"```python\n{code_to_validate}\n```"
#     )
#
#     print(f"Prompt Sent to Agent:\n{prompt}\n")
#     print("--- Running turn (Model calling tool via API) ---")
#
#     # 3. Call run_turn: The model will issue a tool_call to validate_code, receive the output, and respond.
#     final_response = agent.run_turn(prompt)
#
#     print("\n=== Agent Final Output ===")
#     print(final_response)
#
#     print("\n=== Message History Traces ===")
#     for idx, msg in enumerate(agent.messages):
#         role = msg.get("role")
#         tool_calls = msg.get("tool_calls")
#         content = msg.get("content")
#         print(f"[{idx}] Role: {role}")
#         if tool_calls:
#             print(f"    Tool Calls: {tool_calls}")
#         if content:
#             print(f"    Content: {content[:150]}..." if len(str(content)) > 150 else f"    Content: {content}")