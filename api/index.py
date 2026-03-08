import os
import sys

# Bridge to the FastAPI application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Phase3_Backend_API", "api"))

# Vercel-Specific: Adjust root path and data path before importing the app
if os.environ.get("VERCEL"):
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ["RAW_DATA_PATH"] = os.path.join(root_dir, "data", "raw")
    print(f"[DEBUG] Vercel RAW_DATA_PATH set to: {os.environ['RAW_DATA_PATH']}")

from main import app

if os.environ.get("VERCEL"):
    app.root_path = "/api"
