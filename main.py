"""DocQuery Application Server Entry Point

Run locally with:
    python main.py
or:
    uvicorn main:app --reload --port 8000
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )