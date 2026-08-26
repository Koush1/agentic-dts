import ast
import logging
import subprocess
from pathlib import Path

import chromadb.utils.embedding_functions as ef
from chromadb import EmbeddingFunction
from dts_index.vector_store import VectorStore


class AgentTools:

    default_ef: EmbeddingFunction
    vector_store: VectorStore
    repo_path: Path

    def __init__(self, db_path = "../dts_index/chroma_db", repo_path = "../dts_index/dpdk"):
        self.default_ef = ef.DefaultEmbeddingFunction()
        self.vector_store = VectorStore(db_path=db_path, embedding_function=self.default_ef)
        self.repo_path = Path(repo_path)

    def vector_search(self, query: str, n_results: int = 4) -> str:
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

    def validate_code(self, rel_file_path: str, code_block: str) -> dict:
        dts_root = Path(self.repo_path).resolve()
        dpdk_root = dts_root.parent if dts_root.name == "dts" else dts_root
        target_path = dts_root / rel_file_path
        script_path = dpdk_root / "devtools" / "dts-check-format.sh"

        result = {}
        try:
            ast.parse(code_block)
        except SyntaxError as e:
            result["valid"] = False
            result["errors"] = f"Syntax error on line {e.lineno}: {e.msg}"
            return result
        except Exception as e:
            result["valid"] = False
            result["errors"] = f"Parsing error: {e!s}"

        orig_text = target_path.read_text() if target_path.exists() else None
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(code_block)

            res = subprocess.run(
                ["poetry", "run", str(script_path.resolve())],
                cwd=self.repo_path,
                shell=True,
                capture_output=True,
                text=True
            )

            if res.returncode != 0:
                errors = res.stdout.strip() or res.stderr.strip()
                return {
                    "valid": False,
                    "errors": f"DTS check format script violation:\n{errors}"
                }

            return {"valid": True, "errors": []}

        finally:
            if orig_text:
                target_path.write_text(orig_text)
            elif target_path.exists():
                target_path.unlink()

    def read_file(self, rel_filepath: str, start_line: int | None = None, end_line: int | None = None) -> str:

        full_path = (self.repo_path / rel_filepath).resolve()
        if not full_path.exists():
            logging.error(f"File: {full_path} does not exist")
            return f"File {full_path} not found"

        lines = full_path.read_text().splitlines()
        starting = start_line - 1 if start_line else 0
        ending = end_line if end_line else len(lines)
        selected_lines = lines[starting:ending]
        return "\n".join(
            [f"{i+1}: {line}" for i, line in enumerate(selected_lines, start=start_line+1)]
        )

    def generate_patch(self, patch_name: str):
        patch_file = Path(patch_name).with_suffix(".patch")
        patch_path = self.repo_path / patch_file
        try:
            subprocess.run(["git", "add", "-N", "."],
                 cwd=self.repo_path,
                 capture_output=True,
                 check=True
            )
            diff_output = subprocess.run(["git", "diff", "HEAD"],
                  cwd=self.repo_path,
                  capture_output=True,
                  text=True,
                  check=True,
            )

            diff_contents = diff_output.stdout.strip()
            if not diff_contents:
                return {
                    "success": False,
                    "error": "No changes found to generate patch"
                }

            patch_path.write_text(diff_contents)
            return {
                "success": True,
                "patch_path": str(patch_path.resolve()),
                "patch_content": diff_contents
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Git diff execution failed: {e}",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write patch file: {e!s}",
            }


if __name__ == "__main__":
     from dts_index.indexer import update_codebase

     # 1. Sync repository (clones dts + devtools)
     dpdk_path = update_codebase()

     # 2. Instantiate tools pointing to the synced dpdk root
     tools = AgentTools(repo_path=dpdk_path)
     print(tools.generate_patch("testPatch"))
#
#     # 3. Test Vector Search
#     print("=== TESTING VECTOR SEARCH ===")
#     search_results = tools.vector_search("rx_split test suite", n_results=2)
#     print(search_results)
#     print("\n" + "=" * 40 + "\n")
#
#     # 4. Test File Reader
#     print("=== TESTING READ FILE ===")
#     test_rel_path = "README.md"
#
#     # Read entire file (first few lines)
#     print("--- Full Read (Lines 1-5) ---")
#     print(tools.read_file(test_rel_path, start_line=1, end_line=5))
#
#     # Read line slice
#     print("\n--- Slice Read (Lines 3-6) ---")
#     print(tools.read_file(test_rel_path, start_line=3, end_line=6))
#
#     # Non-existent file check
#     print("\n--- Non-Existent File Check ---")
#     print(tools.read_file("non_existent_file.py"))
#     print("\n" + "=" * 40 + "\n")
#
#     # 5. Test Linter Validation with a dummy code snippet
#     print("=== TESTING CODE VALIDATION ===")
#     sample_code = '''def dummy_func(param: int) -> bool:
#     """A valid dummy test function."""
#     return param > 0
#     '''
#     # Relative path from dpdk root to a test file in dts
#     target_file = "tests/TestSuite_buffer_scatter.py"
#     validation_result = tools.validate_code(
#         rel_file_path=target_file, code_block=sample_code
#     )
#     if validation_result.get("valid"):
#         print("GOOD")
#     else:
#         last_key, last_value = next(reversed(validation_result.items()))
#         print("Validation Output:", last_value[:500])