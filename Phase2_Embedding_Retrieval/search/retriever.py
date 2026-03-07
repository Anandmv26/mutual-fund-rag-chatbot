"""
Phase 2 — Retriever
Wraps ChromaDB to provide semantic search over embedded mutual fund chunks.

Usage:
    from retriever import Retriever

    retriever = Retriever()
    results = retriever.search("best small cap fund returns")
"""
import os
import sys
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.utils import embedding_functions

# Shared constants (same as embedder.py)
CHROMA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "chroma"
)
COLLECTION_NAME = "mutual_funds"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class Retriever:
    """Semantic search over mutual fund chunks stored in ChromaDB."""

    def __init__(
        self,
        persist_dir: str = CHROMA_DIR,
        collection_name: str = COLLECTION_NAME,
    ):
        # Vercel Fix: Use absolute Vercel task root and writable /tmp
        if os.environ.get("VERCEL"):
            import shutil
            # Vercel bundles the /api folder; look there
            source_dir = "/var/task/api/data/chroma"
            tmp_dir = "/tmp/chroma_db"
            
            if not os.path.exists(tmp_dir):
                print(f"📦 Vercel start: Migrating DB from {source_dir} to {tmp_dir}")
                os.makedirs(tmp_dir, exist_ok=True)
                
                # Check if source exists in deployment
                if os.path.exists(source_dir):
                    for item in os.listdir(source_dir):
                        s = os.path.join(source_dir, item)
                        d = os.path.join(tmp_dir, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                else:
                    # Fallback for different Vercel structure
                    print(f"⚠️ Source not at {source_dir}, checking root /data")
                    alt_source = "/var/task/data/chroma"
                    if os.path.exists(alt_source):
                        shutil.copytree(alt_source, tmp_dir, dirs_exist_ok=True)
            
            persist_dir = tmp_dir

        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Use fastembed for query embedding to save 7GB+ of space on Vercel
        try:
            from fastembed import TextEmbedding
            # This is a dummy EF that satisfies Chroma's interface but uses our engine
            class FastEmbedEF:
                def __init__(self):
                    # Set cache_dir to /tmp for Vercel
                    self.model = TextEmbedding(
                        model_name="sentence-transformers/all-MiniLM-L6-v2", 
                        cache_dir="/tmp/fastembed"
                    )
                def __call__(self, input: List[str]) -> List[List[float]]:
                    return [list(vec) for vec in self.model.embed(input)]
            
            self.ef = FastEmbedEF()
            print("🚀 Using FastEmbed for search query (Vercel Optimized)")
        except ImportError:
            # Fallback for local dev if fastembed isn't installed
            print("⚠️ fastembed not found, falling back to SentenceTransformer (Default)")
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )

        self.collection = self.client.get_collection(
            name=collection_name,
            embedding_function=self.ef,
        )

    @property
    def count(self) -> int:
        """Return the number of chunks in the collection."""
        return self.collection.count()

    def search(
        self,
        query: str,
        top_k: int = 4,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for the most relevant chunks.

        Args:
            query:  The user's question in natural language.
            top_k:  Number of results to return (default 4).
            where:  Optional metadata filter dict for ChromaDB.
                    Example: {"fund_category": "Equity"}

        Returns:
            A list of result dicts, each containing:
              - text:       the chunk text
              - metadata:   all metadata fields
              - distance:   cosine distance (lower = more similar)
              - id:         ChromaDB document ID
        """
        query_params = {
            "query_texts": [query],
            "n_results": min(top_k, self.count),
        }
        if where:
            query_params["where"] = where

        raw = self.collection.query(**query_params)

        results = []
        for i in range(len(raw["ids"][0])):
            results.append({
                "id": raw["ids"][0][i],
                "text": raw["documents"][0][i],
                "metadata": raw["metadatas"][0][i],
                "distance": raw["distances"][0][i] if raw.get("distances") else None,
            })
        return results

    def search_by_fund(
        self,
        fund_name: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Retrieve all chunks for a specific fund by name."""
        return self.search(
            query=fund_name,
            top_k=top_k,
            where={"fund_name": fund_name},
        )

    def search_by_category(
        self,
        query: str,
        category: str,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """Search within a specific fund category (Equity/Debt/Hybrid)."""
        return self.search(
            query=query,
            top_k=top_k,
            where={"fund_category": category},
        )


# ---- CLI entry point for interactive testing ----
if __name__ == "__main__":
    retriever = Retriever()
    print(f"📊 Collection has {retriever.count} chunks.\n")

    test_queries = [
        "Which fund has the highest 1-year return?",
        "Tell me about small cap funds",
        "What is the expense ratio of HDFC Infrastructure Fund?",
        "Which debt funds are available?",
    ]

    for q in test_queries:
        print(f"🔍 Query: {q}")
        results = retriever.search(q, top_k=3)
        for j, r in enumerate(results):
            dist = f"{r['distance']:.4f}" if r["distance"] is not None else "N/A"
            print(f"   [{j + 1}] (dist={dist}) {r['metadata']['fund_name']} "
                  f"[{r['metadata']['chunk_type']}]")
            print(f"       {r['text'][:120]}...")
        print()
