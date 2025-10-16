import uvicorn
import sys
import os

# Ensure the correct path is in the sys.path for importing project-root modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
