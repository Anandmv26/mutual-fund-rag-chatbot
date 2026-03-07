import os
import sys
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.utils import embedding_functions

# Shared constants
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
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Optimized Embedding Function (FastEmbed for speed)
        try:
            from fastembed import TextEmbedding
            class FastEmbedEF:
                def __init__(self):
                    # Cache in a hidden local folder
                    self.model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
                def __call__(self, input: List[str]) -> List[List[float]]:
                    return [list(vec) for vec in self.model.embed(input)]
            self.ef = FastEmbedEF()
        except ImportError:
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )

        self.collection = self.client.get_collection(
            name=collection_name,
            embedding_function=self.ef,
        )

    def search(
        self,
        query: str,
        top_k: int = 4,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        query_params = {
            "query_texts": [query],
            "n_results": min(top_k, self.collection.count()),
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

    @property
    def count(self) -> int:
        return self.collection.count()
