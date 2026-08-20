from pathlib import Path
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def parse_codebase(target_repo: str = "dpdk"):
    repo_url = "git@github.com:DPDK/dpdk.git"
    branch = "next-dts-for-main"
    local_path = Path(target_repo).resolve()

    if not local_path.exists():
        logging.info(msg=f"{target_repo} repo not found, cloning...")
        try:
            subprocess.run(["git", "clone", "--depth", "1", "--sparse", "--branch", branch, repo_url, str(local_path)],
                           check=True)
            subprocess.run(
                ["git", "sparse-checkout", "set", "dts"],
                cwd=str(local_path),
                check=True,
            )
            logging.info(msg=f"Successfully cloned {target_repo}")
        except subprocess.CalledProcessError as e:
            logging.log(level=logging.ERROR, msg=f"Error cloning repo: {e}")

    else:
        logging.info(msg="DTS repo found, pulling latest changes...")
        try:
            subprocess.run(["git", "fetch", "origin"],
                            cwd=str(local_path),
                            check=True)
            subprocess.run(["git", "pull", "origin", "next-dts-for-main"],
                           cwd=str(local_path),
                           check=True)
            logging.info(msg=f"Changes pulled from {target_repo}")

        except subprocess.CalledProcessError as e:
            logging.log(level=logging.ERROR, msg=f"Error pulling from repo: {e}")

    return local_path / "dts"
