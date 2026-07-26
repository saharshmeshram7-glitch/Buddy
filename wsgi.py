import sys
import os

# Add "Backend code" directory to path
backend_path = os.path.join(os.path.dirname(__file__), "Backend code")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
