import sys
from pathlib import Path
import uvicorn

# Add current workspace to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if __name__ == "__main__":
    print("🚀 Starting Auto-Clipping FastAPI Server on http://0.0.0.0:8000 ...")
    print("📱 You can access this from your Android phone on the same Wi-Fi using your PC's IP address!")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
