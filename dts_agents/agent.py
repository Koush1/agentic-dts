import inspect
from abc import ABC, abstractmethod
from openai import OpenAI
from typing import Any, Callable

class Agent(ABC):
    def __init__(self,
        api_key: str,
        base_url: str = "https://deepthought.usnh.edu/v1",
        model_name: str = "default",
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
