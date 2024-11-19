from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any

from ..services.video_manager import VideoManager
from ..services.websocket_manager import WebSocketManager
from ..services.pdi_service import PDIService
from ..models.pdi import (
    PDIColorSegmentationParameters,
    PDIFunctionType,
    PDIShapeDetectionParameters,
)
from ..models.websocket import WebSocketMessage, WebSocketResponse
import cv2

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
            data = await websocket.receive_json()
            message = WebSocketMessage.parse_obj(data)

            current_video = VideoManager.get_current_video()
            if not current_video:
                await websocket.send_json(
                    {"type": "error", "message": "No video loaded"}
                )
                continue

            # Process video frame if frame_info is provided
            processing_results = []
            if message.frame_info and message.frame_info.markings:
                video_path = VideoManager.get_current_video_path()
                cap = cv2.VideoCapture(str(video_path))
                cap.set(cv2.CAP_PROP_POS_MSEC, message.timestamp)
                ret, frame = cap.read()
                cap.release()

                if ret:
                    pdi_service = PDIService()
                    for marking in message.frame_info.markings:
                        roi = {
                            "x": marking.x,
                            "y": marking.y,
                            "width": marking.width,
                            "height": marking.height,
                        }
                        
                        for function in message.frame_info.functions:
                            if function == PDIFunctionType.COLOR_SEGMENTATION:
                                params = PDIColorSegmentationParameters(
                                    **message.frame_info.parameters.get("color_segmentation", {})
                                )
                                results = pdi_service.process_frame_color_segmentation(
                                    frame=frame,
                                    roi=roi,
                                    params=params,
                                    timestamp=message.timestamp
                                )
                                processing_results.append({
                                    "function": function,
                                    "bounding_boxes": results
                                })
                            elif function == PDIFunctionType.SHAPE_DETECTION:
                                params = PDIShapeDetectionParameters(
                                    **message.frame_info.parameters.get("shape_detection", {})
                                )
                                results = pdi_service.process_frame_shape_detection(
                                    frame=frame,
                                    roi=roi,
                                    params=params,
                                    timestamp=message.timestamp
                                )
                                processing_results.append({
                                    "function": function,
                                    "bounding_boxes": results
                                })

            # Broadcast results
            response = WebSocketResponse(
                type="metadata_sync",
                data={
                    "timestamp": message.timestamp,
                    "video_id": current_video.id,
                    "frame_info": message.frame_info,
                    "processing_results": processing_results
                }
            )
            await manager.broadcast_metadata(response.dict())

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)
