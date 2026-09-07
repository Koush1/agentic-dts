from pathlib import Path
from .dev_agent import DevAgent
from .validation_agent import ValidationAgent

class AgentOrchestrator:

    def __init__(self,
        dev_agent: DevAgent,
        validation_agent: ValidationAgent,
        workspace_path: Path,
        max_tries: int = 5
    ):
        self.dev_agent = dev_agent
        self.validation_agent = validation_agent
        self.workspace_path = workspace_path
        self.max_tries = max_tries

    def isolate_patch(self):
        pass


    def run_pipeline(self, init_prompt: str):

        runs = 1
        curr_prompt = init_prompt
        while runs < self.max_tries:
            patch = self.dev_agent.run_turn(curr_prompt)
            valid = self.validation_agent.run_turn(prompt=patch)

            if "VERDICT: PASS" in valid:
                return patch

            curr_prompt = (
                "Your previous attempt failed.\n"
                f"Original request: {init_prompt}\n"
                f"Validator feedback: {valid}\n"
                f"Please try again"
            )
            runs += 1

        return "Max tries reached."
