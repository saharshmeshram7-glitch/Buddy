import sys
import os

# Add project root to path so we can find Frontend Code folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add "Backend code" directory to path
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Backend code")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app import app

# Vercel needs the app to be named 'app' or 'handler'
# This file is the serverless function entry point
