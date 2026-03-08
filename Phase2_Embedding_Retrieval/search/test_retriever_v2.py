import os
import sys

# Ensure imports work from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from retriever import Retriever

def test_in_memory_retriever():
    print("STARTING: In-Memory Retriever Test (Solution 2)...")
    
    # Initialize retriever
    try:
        retriever = Retriever()
        print(f"LOADED: Total Documents: {retriever.count}")
        
        if retriever.count == 0:
            print("FAILED: No documents loaded. Check your data/raw directory.")
            return

        # Test Search 1: Specific Fund Name
        query_1 = "Tell me about Quant Small Cap Fund"
        results_1 = retriever.search(query_1)
        print(f"QUERY_1: {query_1}")
        if results_1 and "Quant Small Cap" in results_1[0]["text"]:
            print(f"PASSED: Found fund correctly. Top result score: {results_1[0].get('score'):.4f}")
        else:
            print("FAILED: Could not find specific fund or match was poor.")

        # Test Search 2: Quantitative Attribute
        query_2 = "Which fund has high risk?"
        results_2 = retriever.search(query_2)
        print(f"QUERY_2: {query_2}")
        if results_2:
            top_res = results_2[0]
            print(f"DEBUG: Top result: {top_res['metadata']['fund_name']} (Score: {top_res.get('score', 0):.4f})")
            print(f"PASSED: Found results. Top match: {top_res['metadata']['fund_name']}")
        else:
            print("FAILED: No results for qualitative query.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_in_memory_retriever()
