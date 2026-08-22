from indexer import *

if __name__ == "__main__":
    dts_dir = update_codebase(target_repo="dpdk")

    chunks = crawl(dts_dir)
    print(f"Total chunks ready for ChromaDB: {len(chunks)}")
    if chunks:
        print(f"Sample Chunk: {chunks[0]}")