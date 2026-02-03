from typing import List, Dict
from fastapi import WebSocket
import asyncio
import json
import logging
import time

logger = logging.getLogger("WebSocketManager")

class WebSocketManager:
    def __init__(self):
        # Store active connections: container_id -> List[WebSocket]
        # "all" key stores connections listening to everything
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, container_id: str = "all"):
        await websocket.accept()
        if container_id not in self.active_connections:
            self.active_connections[container_id] = []
        self.active_connections[container_id].append(websocket)
        logger.info(f"WebSocket connected for container: {container_id}. Active clients: {len(self.active_connections[container_id])}")

    def disconnect(self, websocket: WebSocket, container_id: str = "all"):
        if container_id in self.active_connections:
            if websocket in self.active_connections[container_id]:
                self.active_connections[container_id].remove(websocket)
                if not self.active_connections[container_id]:
                    del self.active_connections[container_id]
        logger.info(f"WebSocket disconnected for container: {container_id}")

    async def broadcast_batch(self, logs: List[Dict]):
        """
        Broadcast a batch of logs to relevant clients.
        """
        for log in logs:
            # Try multiple fields for container id
            output_fields = log.get('output_fields', {})
            container_id = (
                output_fields.get('container.name')
                or 'unknown'
            )
            if not container_id or container_id == "unknown":
                continue

            # Prepare frontend-friendly format (LogEvent)
            ts_val = log.get('time') or output_fields.get('evt.time') or output_fields.get('evt.time.iso8601')
                       
            import datetime
            timestamp = 0.0
            if isinstance(ts_val, str):
                try:
                    dt = datetime.datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                    timestamp = dt.timestamp()
                except:
                    timestamp = time.time()
            elif isinstance(ts_val, (int, float)):
                timestamp = ts_val if ts_val < 1e11 else ts_val / 1e9
            else:
                timestamp = time.time()

            rule = log.get('rule', 'unknown')
            priority = log.get('priority', 'unknown')
            source = log.get('source', 'unknown')
            output = json.dumps(output_fields, ensure_ascii=False) # Full output fields as string
            tags = json.dumps(log.get('tags', []))

            frontend_msg = {
                "timestamp": timestamp,
                "rule": rule,
                "priority": priority,
                "source": source,
                "output": output,
                "tags": tags,
                "container_id": container_id
            }
            
            message = json.dumps(frontend_msg)
            
            # Target specific listeners
            if container_id in self.active_connections:
                await self._send_to_group(self.active_connections[container_id], message)
            
            # Target global listeners
            if "all" in self.active_connections:
                await self._send_to_group(self.active_connections["all"], message)

    async def _send_to_group(self, connections: List[WebSocket], message: str):
        to_remove = []
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:
                to_remove.append(connection)
        
        for conn in to_remove:
            try:
                connections.remove(conn)
            except ValueError:
                pass

websocket_manager = WebSocketManager()
