import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models.websocket import (
    WebSocketMessage,
    WebSocketResponse,
    WebSocketResponseData,
)
from ..routes.processing_router import process_video_frame
from ..services.video_manager import VideoManager
from ..services.websocket_manager import WebSocketManager

router = APIRouter(tags=["WebSocket"])
manager = WebSocketManager()


@router.websocket("/ws/metadata")
async def websocket_metadata(websocket: WebSocket):
    """
    WebSocket endpoint for real-time video processing and metadata synchronization
    """
    await manager.connect(websocket)
    try:
        while True:
            try:
                message_data = await websocket.receive_json()
                message = WebSocketMessage.model_validate(message_data)

                current_video = VideoManager.get_current_video()
                if not current_video:
                    await websocket.send_json(
                        WebSocketResponse(
                            type="error", message="No video loaded"
                        ).model_dump(mode="json")
                    )
                    continue

                results = await process_video_frame(
                    timestamp=message.timestamp,
                    roi=message.roi,
                    pdi_functions=message.pdi_functions,
                )

                response = WebSocketResponse(
                    type="metadata_sync",
                    data=WebSocketResponseData(
                        marker_id=message.marker_id,
                        timestamp=message.timestamp,
                        video_id=current_video.id,
                        results=results,
                    ),
                )

                await manager.broadcast_metadata(response.model_dump(mode="json"))

            except asyncio.TimeoutError:
                print("Timeout waiting for message")
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)
    finally:
        manager.disconnect(websocket)
