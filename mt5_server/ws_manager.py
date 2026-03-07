import asyncio
import json
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info(f"WS connected. Total: {len(self._connections)}")

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._connections.discard(ws)
        logger.info(f"WS disconnected. Total: {len(self._connections)}")

    async def broadcast(self, data: dict):
        if not self._connections:
            return
        message = json.dumps(data, default=str)
        dead = set()
        async with self._lock:
            conns = set(self._connections)
        for ws in conns:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        # Usuń martwe połączenia
        if dead:
            async with self._lock:
                self._connections -= dead


ws_manager = WebSocketManager()
