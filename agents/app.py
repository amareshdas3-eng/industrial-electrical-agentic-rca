"""
FastAPI Server for Industrial Electrical Single-Line Diagram (SLD) Root Cause Analysis.
"""

from electrical_app import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)