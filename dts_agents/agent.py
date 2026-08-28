import inspect
import logging
import json
from abc import ABC, abstractmethod
from openai import OpenAI
from typing import Any, Callable

class Agent(ABC):
    def __init__(self,
        api_key: str,
        base_url: str = "",
        model_name: str = "ets:aws:us.anthropic.claude-sonnet-4-6",
        temperature: float = 0.2,
        max_turns: int = 10,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_turns = max_turns

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        self.messages: list[dict[str, Any]] = []
        self._tool_registry: dict[str, Callable] = {}
        self._openai_tools_schema: list[dict[str, Any]] = []
        self._register_tools()

    @abstractmethod
    def system_instruction(self) -> str: ...

    @abstractmethod
    def tools(self) -> list[Callable]: ...

    def _build_openai_tool_schema(self, func: Callable) -> dict[str, Any]:
        sig = inspect.signature(func)
        properties = {}
        required = []

        for param_name, param_value in sig.parameters.items():
            if param_name == "self":
                continue

            param_type = "string"
            if param_value.annotation == int:
                param_type = "integer"
            elif param_value.annotation == bool:
                param_type = "boolean"
            elif param_value.annotation == dict:
                param_type = "object"

            properties[param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}"
            }

            if param_value.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": inspect.getdoc(func) or f"Executes {func.__name__}",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def _register_tools(self) -> None:
        self._tool_registry = {tool.__name__: tool for tool in self.tools()}
        self._openai_tools_schema = [self._build_openai_tool_schema(func_tool) for func_tool in self.tools()]

    def execute_tool(self, name: str, args: dict) -> Any:
        if name not in self._tool_registry:
            logging.error("Tool not found")
            return {"error": f"tool: {name} not registered"}

        tool_func = self._tool_registry[name]

        try:
            res = tool_func(**args)
            return res
        except Exception as e:
            return {"error": f"Error executing tool {name}: {e}"}

    def run_turn(self, prompt: str) -> str:
        if not self.messages:
            self.messages.append({
                "role": "system",
                "content": self.system_instruction()
            })

        self.messages.append({
            "role": "user",
            "content": prompt
        })

        turns = 0
        while turns < self.max_turns:

            turns += 1
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
                tools=self._openai_tools_schema,
                tool_choice="auto",
                temperature=self.temperature,
            )

            res_message = response.choices[0].message
            assistant_response = {
                "role": "assistant",
                "content": res_message.content
            }
            if res_message.tool_calls:
                assistant_response["tool_calls"] = [
                    {
                        "id": tlc.id,
                        "type": "function",
                        "function": {
                            "name": tlc.function.name,
                            "arguments": tlc.function.arguments
                        }
                    }
                    for tlc in res_message.tool_calls
                ]
            self.messages.append(assistant_response)

            if res_message.tool_calls:
                for tool_call in res_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    tool_res = self.execute_tool(name=tool_name, args=tool_args)
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_res)
                    })
                continue

            return res_message.content

        return f"Max iterations reached"


# if __name__ == "__main__":
#     import os
#
#     # 1. Define dummy sample tools
#     def generate_dts_patch(suite_name: str, test_cases: int = 1) -> dict:
#         """Generates a DPDK DTS patch for the specified test suite."""
#         return {
#             "status": "success",
#             "patch": f"--- a/dts/{suite_name}.py\n+++ b/dts/{suite_name}.py",
#         }
#
#     def run_dts_suite(suite_name: str, timeout: int = 30) -> str:
#         """Executes a DPDK DTS test suite on the target hardware setup."""
#         return f"DTS Suite {suite_name} passed cleanly in {timeout}s."
#
#     # 2. Implement concrete subclass
#     class TestDevAgent(Agent):
#
#         def system_instruction(self) -> str:
#             return "You are a DPDK DTS development expert. Keep all responses professional and brief."
#
#         def tools(self) -> list[Callable]:
#             return [generate_dts_patch, run_dts_suite]
#
#     # 3. Instantiate agent and register tools
#     api_key = os.getenv("DEEPTHOUGHT_API_KEY", "")
#     agent = TestDevAgent(api_key=api_key)
#     agent._register_tools()
#
#     print("=== Registered Tool Schemas ===")
#     for schema in agent._openai_tools_schema:
#         print(schema)
#
#     # 4. Local Tool Execution Test
#     print("\n=== Testing Direct Tool Execution ===")
#     exec_res = agent.execute_tool(
#         "generate_dts_patch",
#         {"suite_name": "pmd_bonded", "test_cases": 3},
#     )
#     print("Tool Output:", exec_res)
#
#     # 5. Model Turn Execution (If API Key is present)
#     if api_key == "":
#         print("\n=== Running Agent Turn via DeepThought Endpoint ===")
#         output = agent.run_turn(
#             "What tools do you have available for DPDK DTS? Are you able to call these tools? try out a tool call and let me know how it goes"
#         )
#         print("\nFinal Agent Output:\n", output)
#     else:
#         print(
#             "\n[Skipped live endpoint turn: Set DEEPTHOUGHT_API_KEY to test completion call]"
#         )
