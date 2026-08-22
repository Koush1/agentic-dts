from indexer import *
import chromadb.utils.embedding_functions as ef
from indexer import update_codebase, crawl
from vector_store import VectorStore

def main():
    default_ef = ef.DefaultEmbeddingFunction()
    store = VectorStore(db_path="./chroma_db", embedding_function=default_ef)

    repo_path = update_codebase()
    chunks = crawl(repo_path)

    logging.info(f"Indexing {len(chunks)} chunks into local vector store")
    store.to_vector_store(chunks)
    logging.info("Indexing complete")

    # print("\nTesting retrieval:")
    # results = store.query("TRex traffic generator", n_results=3)
    #
    # for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
    #     print(f"\n[Found Symbol: {meta['symbol_name']} in {meta['file_path']}]")
    #     print(doc[:150] + "...")

if __name__ == "__main__":
    main()