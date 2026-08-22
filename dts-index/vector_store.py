import chromadb
from chromadb import QueryResult
from chromadb import EmbeddingFunction
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from ast_parser import CodeChunk
import chromadb.utils.embedding_functions

class VectorStore:

    client: ClientAPI
    collection: Collection
    documents: list[str]
    metadatas: list[dict]
    ids: list[str]
    embedding_func: EmbeddingFunction

    def __init__(self, db_path: str, embedding_function: EmbeddingFunction):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection("dts_codebase", embedding_function=embedding_function)
        self.embedding_func = embedding_function

    def to_vector_store(self, chunks: list[CodeChunk]):

        documents = []
        metadatas = []
        ids = []
        for chunk in chunks:
            symbol = chunk.symbol_name or "module"

            doc = f"Symbol: {symbol}\nDocstring: {chunk.docstring}\nBody Code: {chunk.body_code}"
            documents.append(doc)

            metadata = {
                "symbol_name": symbol or "",
                "node_type": str(chunk.node_type.value),
                "file_path": str(chunk.file_path),
                "start_line": chunk.line_range[0],
                "end_line": chunk.line_range[1]
            }
            metadatas.append(metadata)

            id = f"{chunk.file_path}:{symbol}:{chunk.line_range[0]}"
            ids.append(id)

        self.documents = documents
        self.metadatas = metadatas
        self.ids = ids
        self.collection.upsert(ids=ids, metadatas=metadatas, documents=documents)

    def query(self, query_text: str, n_results: int = 5) -> QueryResult:
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )