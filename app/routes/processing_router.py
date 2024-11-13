import cv2
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import numpy as np
import json

from ..models.pdi import (
    PDIColorSegmentationParameters,
    PDIFunctionType,
    PDIShapeDetectionParameters,
    ProcessVideoRequest,
)
from ..services.pdi_service import PDIService
from ..services.video_manager import VideoManager

router = APIRouter(tags=["Video Processing"])


@router.post(
    "/process",
    summary="Apply PDI functions to a video region of interest",
)
async def process_video(request: ProcessVideoRequest):
    """
    Process a video region with specified PDI functions
    """
    video_path = VideoManager.get_current_video_path()
    if not video_path:
        raise HTTPException(
            status_code=422,
            detail=[{"msg": "No video loaded. Please upload a video first."}],
        )

    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_MSEC, request.timestamp)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise HTTPException(
            status_code=422,
            detail=[{"msg": "Could not read frame at specified timestamp"}],
        )

    results = []
    pdi_service = PDIService()

    for pdi_function in request.pdi_functions:
        if pdi_function.function == PDIFunctionType.COLOR_SEGMENTATION:
            params = PDIColorSegmentationParameters(**pdi_function.parameters)
            bounding_boxes = pdi_service.process_frame_color_segmentation(
                frame=frame, roi=request.roi, params=params, timestamp=request.timestamp
            )
            results.append(
                {"function": pdi_function.function, "bounding_boxes": bounding_boxes},
            )
        elif pdi_function.function == PDIFunctionType.SHAPE_DETECTION:
            params = PDIShapeDetectionParameters(**pdi_function.parameters)
            bounding_boxes = pdi_service.process_frame_shape_detection(
                frame=frame, roi=request.roi, params=params, timestamp=request.timestamp
            )
            results.append(
                {"function": pdi_function.function, "bounding_boxes": bounding_boxes},
            )

    return {"results": results}


@router.post(
    "/process/debug",
    summary="Apply PDI functions and return debug visualization",
)
async def process_video_debug(request: ProcessVideoRequest):
    """
    Process a video region with specified PDI functions and return debug visualization
    """
    video_path = VideoManager.get_current_video_path()
    if not video_path:
        raise HTTPException(
            status_code=422,
            detail=[{"msg": "No video loaded. Please upload a video first."}],
        )

    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_MSEC, request.timestamp)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise HTTPException(
            status_code=422,
            detail=[{"msg": "Could not read frame at specified timestamp"}],
        )

    results = []
    pdi_service = PDIService()

    for pdi_function in request.pdi_functions:
        if pdi_function.function == PDIFunctionType.COLOR_SEGMENTATION:
            params = PDIColorSegmentationParameters(**pdi_function.parameters)
            bounding_boxes = pdi_service.process_frame_color_segmentation(
                frame=frame, roi=request.roi, params=params, timestamp=request.timestamp
            )
            results.append(
                {
                    "function": pdi_function.function.value,
                    "bounding_boxes": bounding_boxes,
                }
            )
        elif pdi_function.function == PDIFunctionType.SHAPE_DETECTION:
            params = PDIShapeDetectionParameters(**pdi_function.parameters)
            bounding_boxes = pdi_service.process_frame_shape_detection(
                frame=frame, roi=request.roi, params=params, timestamp=request.timestamp
            )
            results.append(
                {
                    "function": pdi_function.function.value,
                    "bounding_boxes": bounding_boxes,
                }
            )

    # Draw debug visualization
    debug_frame = pdi_service.draw_debug_boxes(frame, results, request.roi)

    # Encode the frame as JPEG
    _, buffer = cv2.imencode(".jpg", debug_frame)
    jpg_bytes = buffer.tobytes()

    # Convert results to JSON string for header
    results_json = json.dumps(results)

    return Response(
        content=jpg_bytes,
        media_type="image/jpeg",
        headers={
            "X-Results": results_json,
            "Access-Control-Expose-Headers": "X-Results",
        },
    )
