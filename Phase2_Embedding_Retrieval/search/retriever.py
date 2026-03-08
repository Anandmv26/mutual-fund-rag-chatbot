import os
import sys
import json
import glob
from typing import List, Dict, Any, Optional

IMPORT_ERROR = None
try:
    import numpy as np
    from fastembed import TextEmbedding
except ImportError as e:
    IMPORT_ERROR = str(e)
    # Fail gracefully locally if libs are missing
    np = None
    TextEmbedding = None
except Exception as e:
    IMPORT_ERROR = f"Unexpected error: {str(e)}"
    np = None
    TextEmbedding = None

# Prioritize environment variable (set by index.py on Vercel)
RAW_DATA_PATH = os.getenv("RAW_DATA_PATH", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "raw"
))

class Retriever:
    """Hyper-fast In-Memory semantic search over local JSON files.
    Solution 2: Optimized for Serverless (Vercel) with zero disk/database overhead.
    """

    def __init__(self, raw_data_dir: str = RAW_DATA_PATH):
        self.raw_data_dir = raw_data_dir
        self.corpus: List[Dict[str, Any]] = []
        self.embeddings = None
        self.model = None
        self.init_error = None
        
        # Load documents from JSON files
        self._load_documents()
        
        # Initialize ML model (Cached in /tmp for Vercel)
        if TextEmbedding:
            cache_dir = "/tmp/fastembed" if os.environ.get("VERCEL") else None
            try:
                self.model = TextEmbedding(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    cache_dir=cache_dir
                )
                self._generate_embeddings()
            except Exception as e:
                self.init_error = f"Model Init Error: {str(e)}"
                print(f"[ERROR] Failed to load FastEmbed: {e}")
        else:
            self.init_error = "TextEmbedding class is None (Import failed but no error caught)"

    def _load_documents(self):
        """Read all JSON files and format them for search."""
        if not os.path.exists(self.raw_data_dir):
            # Try exploring parent directories if not found (Vercel monorepo quirk)
            alt_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
            if os.path.exists(alt_path):
                self.raw_data_dir = alt_path
            else:
                return

        json_paths = glob.glob(os.path.join(self.raw_data_dir, "*.json"))
        for path in json_paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Create a searchable text representation (Key-Value style)
                    searchable_items = [f"{k.replace('_', ' ').capitalize()}: {v}" 
                                        for k, v in data.items() if v]
                    text_content = ". ".join(searchable_items)
                    
                    # Metadata for RAG
                    self.corpus.append({
                        "id": os.path.basename(path),
                        "text": text_content,
                        "metadata": {
                            "fund_name": data.get("fund_name", ""),
                            "source_url": data.get("source_url", ""),
                            "raw_file": path
                        }
                    })
            except Exception as e:
                print(f"[ERROR] Failed to load {path}: {e}")

    def _generate_embeddings(self):
        """Warm up the cache by embedding all documents now."""
        if not self.corpus or not self.model or np is None:
            return
            
        texts = [doc["text"] for doc in self.corpus]
        # FastEmbed generates an iterator; convert to matrix
        self.embeddings = np.array(list(self.model.embed(texts)))

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Find most similar documents. Fallback to Keyword Search if ML fails."""
        results = []
        
        # 1. Try Semantic Search (High Quality)
        if self.model is not None and self.embeddings is not None and np is not None:
            try:
                query_vec = np.array(list(self.model.embed([query])))[0]
                norm_corpus = np.linalg.norm(self.embeddings, axis=1)
                norm_query = np.linalg.norm(query_vec)
                if norm_query > 0:
                    similarities = np.dot(self.embeddings, query_vec) / (norm_corpus * norm_query)
                    top_indices = np.argsort(similarities)[::-1][:top_k]
                    for idx in top_indices:
                        score = float(similarities[idx])
                        if score > 0.1:
                            doc = self.corpus[idx]
                            results.append({
                                "id": doc["id"], "text": doc["text"], "metadata": doc["metadata"],
                                "score": score, "distance": 1.0 - score
                            })
                    return results
            except Exception as e:
                print(f"[RECOVERY] Semantic search failed, falling back to keywords: {e}")

        # 2. Fallback: Keyword Search (Reliable on Vercel)
        query_words = set(query.lower().split())
        keyword_results = []
        for doc in self.corpus:
            text = doc["text"].lower()
            fund_name = doc["metadata"].get("fund_name", "").lower()
            
            # High weight for fund name matches
            name_score = 0.5 if any(word in fund_name for word in query_words) else 0.0
            # Basic word overlap
            overlap = len(query_words.intersection(set(text.split()))) / max(1, len(query_words))
            
            score = name_score + (overlap * 0.5)
            if score > 0:
                keyword_results.append({
                    "id": doc["id"], "text": doc["text"], "metadata": doc["metadata"],
                    "score": score, "distance": 1.0 - score
                })
        
        # Sort by score descending
        keyword_results.sort(key=lambda x: x["score"], reverse=True)
        return keyword_results[:top_k]

    @property
    def count(self) -> int:
        return len(self.corpus)
