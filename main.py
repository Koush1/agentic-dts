import re

from config import config
from dts_index import indexer
from dts_agents.dev_agent import DevAgent
from dts_agents.validation_agent import ValidationAgent
from dts_agents.orchestrator import AgentOrchestrator
from dts_agents.workspace import WorkspaceManager
from dts_index.vector_store import VectorStore

import chromadb.utils.embedding_functions as embedding_funcs


if __name__ == "__main__":
    print("=== Initiating DTS-Helper ===\n")

    repo_path = indexer.update_codebase()
    chunks = indexer.crawl(repo_path=repo_path)
    vector_store = VectorStore(
        db_path=config.vector_store_path,
        embedding_function=embedding_funcs.DefaultEmbeddingFunction
    )
    vector_store.to_vector_store(chunks=chunks)

    while True:

        with WorkspaceManager() as ws_path:

            prompt = input("Please enter a prompt. I can answer any questions you have, or make requested code changes.\n"
                           "To exit the tool, please enter \'q\'")

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
