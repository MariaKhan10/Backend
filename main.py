import uvicorn
import os
from chatkit_server import app

if __name__ == "__main__":
    uvicorn.run(
    "chatkit_server:app",  # <-- module:variable format
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
    reload=True            # optional for local dev
)

