"""
Insight Forge V2 — Local Server Entrypoint.

Starts the Uvicorn server with Windows asyncio event loop compatibility.
"""

import asyncio
import sys
import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
