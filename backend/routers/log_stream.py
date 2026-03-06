from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging

from backend.services.log_processor import get_processor

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    processor = get_processor()

    async def send_to_client(data):
        try:
            await websocket.send_text(json.dumps(data))
        except Exception:
            pass

    processor.register_callback(send_to_client)

    logger.info("WebSocket client connected")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")