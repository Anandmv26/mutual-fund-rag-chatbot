import os
import sys

# Bridge to the FastAPI application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Phase3_Backend_API", "api"))

from main import app
