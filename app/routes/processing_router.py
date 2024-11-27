from pathlib import Path
from typing import List

import cv2
from fastapi import APIRouter, HTTPException

from ..models.geometry import ROI
from ..models.pdi import (
    PDIColorSegmentationParameters,
    PDIFunction,
    PDIFunctionType,
    PDIShapeDetectionParameters,
    ProcessVideoRequest,
)
from ..services.pdi_service import PDIService
from ..services.video_manager import VideoManager

router = APIRouter(tags=["Video Processing"])


async def process_video_frame(
    timestamp: int, roi: ROI, pdi_functions: List[PDIFunction]
):
    """
    Process a single video frame with the given PDI functions
    """
    video_path = VideoManager.get_current_video_path()
    if not video_path:
        raise HTTPException(
            status_code=422,
            detail=[{"msg": "No video loaded. Please upload a video first."}],
        )

    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise HTTPException(
            status_code=422,
            detail=[{"msg": "Could not read frame at specified timestamp"}],
        )

    results = []
    pdi_service = PDIService()

    for pdi_function in pdi_functions:
        if pdi_function.function == PDIFunctionType.COLOR_SEGMENTATION:
            params = PDIColorSegmentationParameters(**pdi_function.parameters)
            bounding_boxes = pdi_service.process_frame_color_segmentation(
                frame=frame, roi=roi, params=params, timestamp=timestamp
            )
            results.append(
                {"function": pdi_function.function, "bounding_boxes": bounding_boxes},
            )
        elif pdi_function.function == PDIFunctionType.SHAPE_DETECTION:
            params = PDIShapeDetectionParameters(**pdi_function.parameters)
            bounding_boxes = pdi_service.process_frame_shape_detection(
                frame=frame, roi=roi, params=params, timestamp=timestamp
            )
            results.append(
                {"function": pdi_function.function, "bounding_boxes": bounding_boxes},
            )

    return results


@router.post(
    "/process",
    summary="Apply PDI functions to a video region of interest",
)
async def process_video(request: ProcessVideoRequest):
    """
    Process a video region with specified PDI functions
    """
    results = await process_video_frame(
        timestamp=request.timestamp,
        roi=request.roi,
        pdi_functions=request.pdi_functions,
    )
    return {"results": results}


@router.post(
    "/process/debug",
    summary="Process video frame with debug visualization",
    operation_id="process_video_debug",
    response_model=dict,
)
async def process_video_debug(request: ProcessVideoRequest):
    """
    Process current video frame with debug visualization.
    Saves intermediate processing steps as images and returns results.
    """
    results = await process_video_frame(
        timestamp=request.timestamp,
        roi=request.roi,
        pdi_functions=request.pdi_functions,
    )

    video_path = VideoManager.get_current_video_path()
    if not video_path:
        raise HTTPException(
            status_code=422,
            detail="No video loaded. Please upload a video first.",
        )

    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_MSEC, request.timestamp)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to read frame at timestamp {request.timestamp}ms",
        )

    pdi_service = PDIService()
    debug_frame = pdi_service.draw_debug_boxes(
        frame=frame,
        results=results,
        roi=request.roi,
    )

    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)
    cv2.imwrite(str(debug_dir / f"debug_{request.timestamp}.jpg"), debug_frame)

    return {"results": results}
