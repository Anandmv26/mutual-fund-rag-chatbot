import os
import sys

# Ensure the project root and specific app sub-directories are discoverable
# by Vercel's serverless runtime.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Phase3_Backend_API", "api"))

# Absolute path correction for bundled data inside the api/data folder
API_DIR = os.path.dirname(os.path.abspath(__file__))
# On Vercel, the files are in /var/task/api/data
os.environ["DATABASE_PATH"] = os.path.join(API_DIR, "data", "chroma")
os.environ["RAW_DATA_PATH"] = os.path.join(API_DIR, "data", "raw")
os.environ["ANONYMIZED_TELEMETRY"] = "False"

print(f"DEBUG: Vercel Path Configured - DB: {os.environ['DATABASE_PATH']}")

# Note: We must ensure ChromaDB and Sentence-Transformers fit in Vercel's 250MB limit.
# If this fails, consider using a lighter-weight embedding solution for production.
from main import app
