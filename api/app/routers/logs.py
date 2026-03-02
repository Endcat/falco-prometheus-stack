from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Body, HTTPException
from typing import List, Dict, Any
from api.app.services.websocket_manager import websocket_manager
import logging

router = APIRouter()
logger = logging.getLogger("LogsRouter")

@router.websocket("/ws/{container_id}")
async def websocket_endpoint(websocket: WebSocket, container_id: str):
    await websocket_manager.connect(websocket, container_id)
    try:
        while True:
            # Keep connection alive, maybe receive commands from client later
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, container_id)

@router.post("/internal/ingest")
async def ingest_logs(logs: List[Dict[str, Any]] = Body(...)):
    """
    Internal endpoint for logs-ingestor to push logs.
    These logs are then broadcasted via WebSocket.
    """
    if not logs:
        return {"status": "ok", "count": 0}
    
    # Broadcast asynchronously
    await websocket_manager.broadcast_batch(logs)
    
    return {"status": "ok", "count": len(logs)}
