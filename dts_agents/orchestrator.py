import subprocess
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
                        text=True,
                        check=True,
                    )

                    patch_text = diff_output.stdout.strip()
                    if not patch_text:
                        print("\n[-] WARNING: The agent passed validation, but no code changes were found.")
                    else:
                        print("\n[+] SUCCESS! Here is the generated patch:\n")
                        print("-" * 40)
                        print(patch_text)
                        print("-" * 40)

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
