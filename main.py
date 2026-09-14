import time
import shutil
from pathlib import Path
from config import config
from dts_index import indexer
from dts_agents.dev_agent import DevAgent
from dts_agents.validation_agent import ValidationAgent
from dts_agents.orchestrator import AgentOrchestrator
from dts_agents.workspace import WorkspaceManager
from dts_agents.question_agent import QuestionAgent
from dts_index.vector_store import VectorStore

import chromadb.utils.embedding_functions as embedding_funcs

# question testing prompt - question: explain how traffic generators work in dts
# dev testing prompt - code: theres an issue in dts where i cant run functional and performance tests back to back, diagnose and fix the issue
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

        prompt = input("Please enter a prompt. Please lead your prompt with \'question:\' for and questions, "
                       "or lead with \'code:\' for any requested code changes. To exit the tool, please enter \'q\'\n")

        if prompt.lower() == "q":
            print("Exiting, goodbye!")
            break

        if prompt.lower().startswith("question:"):
            mode = "question"
            quest_agent = QuestionAgent()
            orchestrator = AgentOrchestrator(
                dev_agent=None,
                validation_agent=None,
                question_agent=quest_agent,
                max_tries=3,
                workspace_path=Path(config.repo_path)
            )

            final_response = orchestrator.run_pipeline(prompt, mode)
            print(final_response)
            continue


        elif prompt.lower().startswith("code:"):
            mode = "code"
            with WorkspaceManager() as ws_path:

                dev_agent = DevAgent(workspace_path=ws_path)
                val_agent = ValidationAgent()
                orchestrator = AgentOrchestrator(
                    dev_agent=dev_agent,
                    validation_agent=val_agent,
                    question_agent=None,
                    max_tries=3,
                    workspace_path=ws_path
                )

                print(f"\n[+] Sandbox created at: {ws_path}")
                print(f"\n[+] Sending Prompt to Orchestrator: \n    '{prompt}'")
                final_response = orchestrator.run_pipeline(prompt, mode)
                #print(f"\n[+] Final response: \n{final_response}")

                print("\n=== Completed: (Sandbox Destroyed) ===")
                continue

        else:
            print("Invalid prompt, please try again.")