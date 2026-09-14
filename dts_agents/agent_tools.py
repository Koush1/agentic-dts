import ast
import logging
import subprocess
from config import config
from pathlib import Path
import chromadb.utils.embedding_functions as ef
from chromadb import EmbeddingFunction
from config import config
from dts_index.vector_store import VectorStore


class AgentTools:

    default_ef: EmbeddingFunction
    vector_store: VectorStore
    repo_path: Path

    def __init__(self, workspace_path: Path):
        self.default_ef = ef.DefaultEmbeddingFunction()
        self.vector_store = VectorStore(db_path=config.vector_store_path, embedding_function=self.default_ef)
        self.repo_path = config.repo_path
        self.workspace_path = workspace_path

    def vector_search(self, query: str, n_results: int = 4) -> str:
        """TOOL: Searches the DPDK DTS codebase for relevant test suites or code snippets.
        Inspect the returned code snippets thoroughly and efficiently, be efficient.
        """
        data = self.vector_store.query(query_text=query, n_results=n_results)
        docs = data["documents"][0]
        metadatas = data["metadatas"][0]

        formatted_chunks = []
        for doc, metadata in zip(docs, metadatas):
            file_path = metadata.get("file_path") or "Unknown filepath"
            start_line = metadata.get("start_line") or "?"
            end_line = metadata.get("end_line") or "?"
            info_header = f"File: {file_path} (Lines {start_line}-{end_line})"
            chunk = f"{info_header}\n{doc}"
            formatted_chunks.append(chunk)

        return "\n\n---\n\n".join(formatted_chunks)

    def validate_code(self) -> dict:
        """TOOL: Runs the provided dts-check-format script to check for
        formatting/type hinting errors in the code."""
        script_path = config.repo_path.parent / "devtools" / "dts-check-format.sh"

        try:

            subprocess.run(
                ["poetry", "install"],
                cwd=self.workspace_path
            )

            res = subprocess.run(
                ["poetry", "run", str(script_path.resolve())],
                cwd=self.workspace_path,
                capture_output=True,
                text=True
            )
            # print(res.stdout.strip())
            # print(res.stderr.strip())

            if res.returncode != 0:
                errors = res.stdout.strip() or res.stderr.strip()
                return {
                    "valid": False,
                    "errors": f"DTS check format script violation:\n{errors}"
                }

            return {"valid": True, "errors": []}

        except subprocess.CalledProcessError as e:
            return {"valid": "INDETERMINATE", "errors": e}

    def write_file(self, rel_filepath: str, contents: str) -> str:
        """TOOL: Safely writes changes to a file in the workspace"""
        full_path = (self.workspace_path / rel_filepath).resolve()
        if not full_path.is_relative_to(self.workspace_path):
            return "ERROR: Access denied, path outside workspace"

        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w") as file:
            file.write(contents)

        return f"SUCCESS: Contents successfully written to : {rel_filepath}"

    def edit_file(self, rel_filepath: str, old_contents: str, new_contents: str) -> str:
        """TOOL: Safely edits a file in the workspace"""
        full_path = (self.workspace_path / rel_filepath).resolve()
        if not full_path.is_relative_to(self.workspace_path):
            return "ERROR: Access denied, path outside workspace"
        if not full_path.exists():
            return "ERROR: Filepath does not exist"

        with open(full_path, "r") as file:
            file_contents = file.read()

        if old_contents not in file_contents:
            return (
                "ERROR: old_contents not found in file.\n"
                "Ensure your indentation and spacing exactly match the original file"
            )

        new_file_contents = file_contents.replace(old_contents, new_contents)

        with open(full_path, "w") as file:
            file.write(new_file_contents)

        return f"SUCCESS: Successfully replaced code in {rel_filepath}"

    def read_file(
            self,
            rel_filepath: str,
            start_line: int | None = None,
            end_line: int | None = None
    ) -> str:
        """TOOL: Use to read the full contents of a file"""
        full_path = (self.workspace_path / rel_filepath).resolve()
        if not full_path.is_relative_to(self.workspace_path):
            return "ERROR: Access denied, path outside workspace"
        if not full_path.exists():
            logging.error(f"File: {full_path} does not exist")
            return f"File {full_path} not found"

        lines = full_path.read_text().splitlines()
        start_val = int(start_line) if start_line is not None else 1
        end_val = int(end_line) if end_line is not None else len(lines)
        starting = start_val - 1
        ending = end_val
        selected_lines = lines[starting:ending]
        return "\n".join(
            [f"{i}: {line}" for i, line in enumerate(selected_lines, start=start_val + 1)]
        )