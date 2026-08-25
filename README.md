# DPDK DTS Developer Assistant (`dts-agents`)

An autonomous, multi-agent developer tool designed to assist engineers working with the **DPDK DTS (Data Plane Development Kit Test Suite)** framework. Built with a local Retrieval-Augmented Generation (RAG) vector engine and a dual-agent "actor-critic" loop, this tool answers technical framework questions, drafts code modifications, validates AST structures, and outputs unified Git patch files (`.patch`) ready for submission.

---

## Key Features

* **Local Codebase Indexing:** Uses ChromaDB and AST parsing to crawl, chunk, and embed the `dpdk/dts` source tree on disk.
* **Semantic Code Search:** Queries local code vectors using lightweight ONNX embeddings without cloud API dependencies.
* **Multi-Agent Actor-Critic Architecture:**
  * **Developer Agent:** Performs multi-step retrieval, analyzes framework interfaces, and drafts code solutions iteratively.
  * **Validator Agent:** Inspects code drafts using AST syntax checks, type-hint enforcement, and docstring rules.
* **Automated Git Patch Generation:** Once validated, creates isolated diffs (`.patch`) against local repository clones.
* **100% Local & Offline Execution:** Runs locally via Ollama on Apple Silicon / local hardware.

---

## Architecture Overview

```text
                           ┌────────────────────────┐
                           │      User Request      │
                           └───────────┬────────────┘
                                       │
                           Is this a code modification?
                                     /   \
                                No  /     \  Yes
                                   /       \
                                  ▼         ▼
               ┌────────────────────┐     ┌──────────────────────────────────┐
               │  Developer Agent   │     │         Developer Agent          │
               │   (Query Mode)     │     │   (Drafting & Refinement Loop)   │
               └─────────┬──────────┘     └────────────────┬─────────────────┘
                         │                                 │
             Retrieves Context & Responds                  ├─► Queries ChromaDB
                         │                                 ├─► Generates Code Draft
                         ▼                                 └─► Evaluates Feedback
                   Direct Answer                                   │
                                                                   ▼
                                                   Passes Draft to Validator Agent
                                                                   │
                                                                   ▼
                                                  ┌──────────────────────────────────┐
                                                  │         Validator Agent          │
                                                  └────────────────┬─────────────────┘
                                                                   │
                                                     Executes AST & Style Checks
                                                                  / \
                                                             Fail/   \Pass
                                                                /     \
                                                               ▼       ▼
                                                     Feedback Sent   Generates .patch File
                                                     Back to Dev     & Returns to User