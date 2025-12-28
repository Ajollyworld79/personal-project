import os
import uvicorn

if __name__ == "__main__":
    # Get port from environment variable or default to 8000
    # Railway sets PORT automatically
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on 0.0.0.0:{port}")
    uvicorn.run("app.app:app", host="0.0.0.0", port=port)
