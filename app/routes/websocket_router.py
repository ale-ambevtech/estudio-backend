import cv2
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models.pdi import (
    PDIColorSegmentationParameters,
    PDIFunctionType,
    PDIShapeDetectionParameters,
)
from ..models.websocket import WebSocketMessage, WebSocketResponse
from ..services.pdi_service import PDIService
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
            message = WebSocketMessage.parse_obj(await websocket.receive_json())
            current_video = VideoManager.get_current_video()
            if not current_video:
                await websocket.send_json(
                    {"type": "error", "message": "No video loaded"}
                )
                continue

            processing_results = (
                await process_frame(message)
                if message.frame_info and message.frame_info.markings
                else []
            )

            # Broadcast results
            response = WebSocketResponse(
                type="metadata_sync",
                data={
                    "timestamp": message.timestamp,
                    "video_id": current_video.id,
                    "frame_info": message.frame_info,
                    "processing_results": processing_results,
                },
            )
            await manager.broadcast_metadata(response.dict())

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)


async def process_frame(message: WebSocketMessage) -> list:
    """Process video frame and return results"""
    video_path = VideoManager.get_current_video_path()
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_MSEC, message.timestamp)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return []

    pdi_service = PDIService()
    processing_results = []

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
                    timestamp=message.timestamp,
                )
                processing_results.append(
                    {"function": function, "bounding_boxes": results}
                )
            elif function == PDIFunctionType.SHAPE_DETECTION:
                params = PDIShapeDetectionParameters(
                    **message.frame_info.parameters.get("shape_detection", {})
                )
                results = pdi_service.process_frame_shape_detection(
                    frame=frame,
                    roi=roi,
                    params=params,
                    timestamp=message.timestamp,
                )
                processing_results.append(
                    {"function": function, "bounding_boxes": results}
                )

    return processing_results
