import time
import subprocess
from config import config

class WorkspaceManager:
    repo_path = config.repo_path
    workspace_path = config.repo_path.parent.parent / "tmp-workspace"
    tmp_branch = "tmp-agent-workspace"

    def __enter__(self):
        subprocess.run(
            ["git", "worktree", "add", self.workspace_path, "-b", self.tmp_branch],
            cwd=self.repo_path
        )
        while not self.workspace_path.exists():
            time.sleep(1)

        return self.workspace_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.run(
            ["git", "worktree", "remove", self.workspace_path, "--force"],
            cwd=self.repo_path
        )
        subprocess.run(
            ["git", "branch", "-D", self.tmp_branch],
            cwd=self.repo_path
        )