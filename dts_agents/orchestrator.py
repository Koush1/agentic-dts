import subprocess
from config import config
from pathlib import Path
from .dev_agent import DevAgent
from .question_agent import QuestionAgent
from .validation_agent import ValidationAgent

class AgentOrchestrator:

    def __init__(self,
        dev_agent: DevAgent | None,
        validation_agent: ValidationAgent | None,
        question_agent: QuestionAgent | None,
        workspace_path: Path,
        max_tries: int = 5
    ):
        self.dev_agent = dev_agent
        self.validation_agent = validation_agent
        self.question_agent = question_agent
        self.workspace_path = workspace_path
        self.max_tries = max_tries

    def run_pipeline(self, init_prompt: str, mode: str):

        runs = 1
        curr_prompt = init_prompt

        if mode == "code":
            while runs < self.max_tries:

                patch = self.dev_agent.run_turn(curr_prompt)
                print("\n[Orchestrator] Dev Agent finished. Sending to Validation Agent...")

                valid = self.validation_agent.run_turn(prompt=patch)
                print(f"\n[Validation Agent Feedback]:\n{valid}\n")

                if "VERDICT: PASS" in valid:
                    try:
                        subprocess.run(
                            ["git", "add", "-N", "."],
                            cwd=self.workspace_path,
                            capture_output=True,
                            check=True
                        )

                        diff_output = subprocess.run(
                            ["git", "diff", "HEAD"],
                            cwd=self.workspace_path,
                            capture_output=True,
                            check=True,
                        )

                        patch_text = diff_output.stdout
                        if not patch_text:
                            print("\n[-] WARNING: The agent passed validation, but no code changes were found.")
                        else:

                            config.output_path.mkdir(parents=True, exist_ok=True)
                            with open(f"{config.output_path}/generated_patch.patch", "wb") as patch_file:
                                patch_file.write(patch_text)

                            print("\n[+] SUCCESS! Patch available at agentic-dts/output")

                        return patch_text

                    except subprocess.CalledProcessError as e:
                        print(f"\n[-] ERROR: Git diff execution failed: {e}")

                curr_prompt = (
                    "Your previous attempt failed.\n"
                    f"Original request: {init_prompt}\n"
                    f"Validator feedback: {valid}\n"
                    f"Please try again"
                )
                runs += 1

            return "Max tries reached."

        else:
            answer = self.question_agent.run_turn(curr_prompt)
            return answer
