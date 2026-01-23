#!/usr/bin/env python3
"""Startup script for the Student Learning Agent."""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    import uvicorn

    print("Starting Student Learning Agent...")
    print(f"API docs: http://localhost:8000/docs")
    print(f"Health check: http://localhost:8000/health")
    print()

    uvicorn.run(
        "app.main:app",  # Use import string instead of app object
        host="0.0.0.0",
        port=8000,
        reload=True
    )
