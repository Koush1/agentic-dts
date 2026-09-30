# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Koushik Bhargav Nimoji

import os
import shutil
import time
import subprocess
from config import config

class WorkspaceManager:
    repo_path = config.repo_path
    workspace_path = config.repo_path.parent.parent / "tmp-workspace"
    tmp_branch = f"tmp-agent-workspace-{int(time.time())}"

    def __enter__(self):

        subprocess.run(["git", "worktree", "prune"], check=False)
        if os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

        res = subprocess.run(
            ["git", "worktree", "add", "-f", "-b", self.tmp_branch, self.workspace_path],
            cwd=self.repo_path
        )
        while not self.workspace_path.exists():
            time.sleep(1)

        if res.returncode != 0:
            raise RuntimeError(f"Failed to create workspace: {res.stderr}")

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