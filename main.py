import re
import time
import shutil
from pathlib import Path
from config import config
from dts_index import indexer
from dts_agents.dev_agent import DevAgent
from dts_agents.validation_agent import ValidationAgent
from dts_agents.orchestrator import AgentOrchestrator
from dts_agents.workspace import WorkspaceManager
from dts_index.vector_store import VectorStore

import chromadb.utils.embedding_functions as embedding_funcs

# testing prompt: theres an issue in dts where i cant run functional and performance tests back to back, diagnose and fix the issue
if __name__ == "__main__":
    print("=== Initiating DTS-Helper ===\n")
    print("Updating Vector Database...")
    time.sleep(1)

    #rebuild vector store
    db_dir = Path(config.vector_store_path)
    if db_dir.exists():
        shutil.rmtree(db_dir)

    repo_path = indexer.update_codebase()
    chunks = indexer.crawl(repo_path=repo_path)
    vector_store = VectorStore(
        db_path=config.vector_store_path,
        embedding_function=embedding_funcs.DefaultEmbeddingFunction()
    )
    vector_store.to_vector_store(chunks=chunks)

    while True:

        with WorkspaceManager() as ws_path:

            prompt = input("Please enter a prompt. I can answer any questions you have, or make requested code changes.\n"
                           "To exit the tool, please enter \'q\'\n")

            if prompt.lower() == 'q':
                print("Exiting, goodbye!")
                break

            print(f"\n[+] Sandbox created at: {ws_path}")

            dev_agent = DevAgent(workspace_path=ws_path)
            val_agent = ValidationAgent()

            orchestrator = AgentOrchestrator(
                dev_agent=dev_agent,
                validation_agent=val_agent,
                max_tries=3,
                workspace_path=WorkspaceManager.workspace_path
            )

            print(f"\n[+] Sending Prompt to Orchestrator: \n    '{prompt}'")
            final_response = orchestrator.run_pipeline(prompt)
            match = re.search(r'```python\n(.*?)\n```', final_response, re.DOTALL | re.IGNORECASE)

            if match:
                code_snippet = match.group(1).strip()

                target_file = ws_path / "dts/tests/TestSuite_virtio_throughput.py"

                print(f"\n[+] Extracted {len(code_snippet)} characters of Python code.")

                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(code_snippet)
                print(f"[+] Code successfully written to sandbox: {target_file.name}")

                print("\n[+] Generating Patch...")
                patch_result = dev_agent.tool_instance.generate_patch("virtio_throughput_suite")

                if patch_result.get("success"):
                    print("\n[+] SUCCESS! Here is the generated patch:\n")
                    print("-" * 40)
                    print(patch_result.get("patch_content"))
                    print("-" * 40)
                else:
                    print(f"\n[-] Patch generation failed: {patch_result.get('error')}")

            else:
                print(
                    "\n[-] Error: Orchestrator failed to produce a valid ```python markdown block after all attempts.")
                print("Final Raw Response:\n", final_response)

        print("\n=== Test Complete (Sandbox Destroyed) ===")