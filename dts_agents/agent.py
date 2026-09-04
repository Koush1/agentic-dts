import inspect
import logging
import json
from abc import ABC, abstractmethod
from openai import OpenAI
from config import config
from typing import Any, Callable

class Agent(ABC):
    def __init__(self,
        api_key: str | None = None,
        base_url: str| None = None,
        model_name: str | None = None,
        temperature: float | None = None,
        max_turns: int | None = None,
    ):

        self.model_name = model_name or config.deepthought_model_name
        self.temperature = temperature or config.default_temp
        self.max_turns = max_turns or config.max_turns

        self.client = OpenAI(
            api_key=api_key or config.deepthought_api_key,
            base_url=base_url or config.deepthought_base_url,
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
            if param_name in ("self", "cls"):
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
            cleaned_args = {k: v for k, v in args.items() if k not in ("self", "cls")}
            res = tool_func(**cleaned_args)
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
