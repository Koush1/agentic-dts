from config import config
from .agent import Agent
from typing import Callable
from pathlib import Path
from .agent_tools import AgentTools

class QuestionAgent(Agent):

    def __init__(self):
        self.repo_path: Path = config.repo_path
        self.tool_instance = AgentTools(workspace_path=config.repo_path)
        super().__init__()

    def system_instruction(self) -> str:
        return (
            "You are a Data Plane Development Kit Test Suite expert."
            "Your job is to accurately answer and questions asked."
            "EFFICIENT TOOL USE GUIDELINE:"
            "1. Always query vector_search first when you need information"
            "2. IF the information provided by vector_search is insufficient"
            "or you need to read a whole file, only then use the read_file tool."
        )

    def tools(self) -> list[Callable]:
        #question answering specific tools
        question_tools = [
            self.tool_instance.vector_search,
            self.tool_instance.read_file
        ]
        return question_tools
