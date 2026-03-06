"""
Phase 2 — Embedder
Takes processed text chunks and embeds them into ChromaDB using
the all-MiniLM-L6-v2 sentence-transformer model.

ChromaDB collection is persisted to data/chroma/ for later retrieval.
"""
import os
import sys
import shutil

import chromadb
from chromadb.utils import embedding_functions

# Allow importing processor from the same package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from processor import process_all  # noqa: E402

CHROMA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "chroma"
)
COLLECTION_NAME = "mutual_funds"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_chroma_client(persist_dir: str = CHROMA_DIR) -> chromadb.ClientAPI:
    """Create or connect to a persistent ChromaDB client."""
    os.makedirs(persist_dir, exist_ok=True)
    return chromadb.PersistentClient(path=persist_dir)


def get_embedding_function():
    """Return the sentence-transformer embedding function for ChromaDB."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )


def embed_and_store(
    persist_dir: str = CHROMA_DIR,
    collection_name: str = COLLECTION_NAME,
    rebuild: bool = False,
) -> int:
    """
    Process all raw fund JSONs → embed → store in ChromaDB.

    Args:
        persist_dir:      Path to ChromaDB persistence directory.
        collection_name:  Name of the ChromaDB collection.
        rebuild:          If True, delete existing collection and rebuild from scratch.

    Returns:
        Number of chunks stored.
    """
    client = get_chroma_client(persist_dir)
    ef = get_embedding_function()

    # Optionally wipe and recreate
    if rebuild:
        try:
            client.delete_collection(collection_name)
            print(f"🗑️  Deleted existing collection '{collection_name}'.")
        except Exception:
            pass  # Collection didn't exist

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},   # cosine similarity
    )

    # Process chunks
    chunks = process_all()
    if not chunks:
        print("⚠️  No chunks to embed.")
        return 0

    # Prepare batch data for ChromaDB
    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        # Create a deterministic ID: fund-slug + chunk-type
        fund_slug = (
            chunk["metadata"]["fund_name"]
            .lower()
            .replace(" ", "-")
            .replace(".", "")[:50]
        )
        chunk_type = chunk["metadata"]["chunk_type"]
        chunk_id = f"{fund_slug}__{chunk_type}"

        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])

    # Upsert (add or update) all chunks
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    print(f"✅ Embedded and stored {len(ids)} chunks in '{collection_name}'.")
    print(f"📂 ChromaDB persisted to: {persist_dir}")
    return len(ids)


# ---- CLI entry point ----
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Embed mutual fund data into ChromaDB")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete existing collection and rebuild from scratch",
    )
    args = parser.parse_args()

    count = embed_and_store(rebuild=args.rebuild)
    print(f"\n🎉 Done! Total chunks in vector store: {count}")
