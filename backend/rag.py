# backend/rag.py
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Initialize Chroma client & collection
client = chromadb.Client(Settings(anonymized_telemetry=False))
collection = client.get_or_create_collection("qa_kb")

# Load embedding model (small & fast)
# This downloads automatically the first time
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def split_text(text: str, chunk_size: int = 800, overlap: int = 200) -> List[str]:
    """
    Simple character-based chunker.
    """
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


def add_document(doc_text: str, metadata: Dict):
    """
    Split document into chunks and add to Chroma collection.
    """
    chunks = split_text(doc_text)
    if not chunks:
        return

    base_id = metadata.get("source", "doc")
    ids = [f"{base_id}_{i}" for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        metadatas=[metadata] * len(chunks),
        ids=ids,
    )


def query_knowledge_base(query: str, n_results: int = 5) -> List[Dict]:
    """
    Retrieve top-k most relevant chunks for a query.
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    return [
        {"text": doc, "metadata": meta}
        for doc, meta in zip(docs, metas)
    ]
