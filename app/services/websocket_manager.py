import asyncio
from typing import Any, Dict, List

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Connect a new WebSocket client
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket client
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_metadata(self, message: Dict[str, Any]):
        """
        Broadcast metadata to all connected clients with timeout
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await asyncio.wait_for(connection.send_json(message), timeout=5.0)
            except asyncio.TimeoutError:
                print("Timeout broadcasting to client")
                disconnected.append(connection)
            except Exception as e:
                print(f"Error broadcasting to client: {str(e)}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
