import subprocess
import logging
from pathlib import Path
from ast_parser import CodeChunk, parse_file

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def update_codebase(target_repo: str = "dpdk"):
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

def crawl(repo_path: Path) -> list[CodeChunk]:

    repo_path = Path.resolve(repo_path)
    if not repo_path.exists():
        logging.error("The provided filepath does not exist")

    exclude_parse = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        ".mypy_cache",
        ".pytest_cache",
        "build",
        "dist",
    }

    all_chunks = []
    processed_files = 0
    failed_files = 0
    for file in repo_path.rglob("*.py"):

        if any(part in exclude_parse for part in file.parts):
            continue

        try:
            chunks = parse_file(file)
            if chunks:
                all_chunks.extend(chunks)
                processed_files += 1

        except Exception as e:
            logging.error(f"Unable to parse file {file}: {e}")
            failed_files += 1

    logging.info(f"Parsing completed. {processed_files} files processed, {failed_files} failed to process.")
    return all_chunks
