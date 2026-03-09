from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active websocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept websocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected websocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time logs"""
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)