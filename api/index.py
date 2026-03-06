import os
import sys

# Ensure the project root and specific app sub-directories are discoverable
# by Vercel's serverless runtime.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Phase3_Backend_API", "api"))

# Absolute path correction for local data and model access in serverless env
# Vercel serverless functions have a read-only filesystem except /tmp
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["DATABASE_PATH"] = os.path.join(ROOT_DIR, "data", "chroma")
os.environ["RAW_DATA_PATH"] = os.path.join(ROOT_DIR, "data", "raw")

# Note: We must ensure ChromaDB and Sentence-Transformers fit in Vercel's 250MB limit.
# If this fails, consider using a lighter-weight embedding solution for production.
from main import app
