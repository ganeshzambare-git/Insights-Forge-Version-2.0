"""
Insight Forge V2 — Local Server Entrypoint.

Starts the Uvicorn server with Windows asyncio event loop compatibility.
"""

import asyncio
import sys
import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    if sys.platform == "win32":
        asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(server.serve())
