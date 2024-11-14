from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any

from ..services.video_manager import VideoManager
from ..services.websocket_manager import WebSocketManager

router = APIRouter(tags=["WebSocket"])
manager = WebSocketManager()


@router.websocket("/ws/metadata")
async def websocket_metadata(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metadata synchronization
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            if not isinstance(data, dict) or "timestamp" not in data:
                await websocket.send_json(
                    {"type": "error", "message": "Invalid message format"}
                )
                continue

            current_video = VideoManager.get_current_video()
            if not current_video:
                await websocket.send_json(
                    {"type": "error", "message": "No video loaded"}
                )
                continue

            # Process and broadcast metadata
            response = {
                "type": "metadata_sync",
                "data": {
                    "timestamp": data["timestamp"],
                    "video_id": current_video.id,
                    "frame_info": data.get("frame_info", {}),
                },
            }
            await manager.broadcast_metadata(response)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)
