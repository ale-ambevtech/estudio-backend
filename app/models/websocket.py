from typing import Dict, List, Optional
from pydantic import BaseModel


class FrameMarking(BaseModel):
    x: int
    y: int
    width: int
    height: int


class FrameInfo(BaseModel):
    markings: List[FrameMarking]
    functions: List[str]
    parameters: Optional[Dict[str, str]] = None


class WebSocketMessage(BaseModel):
    timestamp: int
    frame_info: Optional[FrameInfo] = None


class WebSocketResponseData(BaseModel):
    timestamp: int
    video_id: str
    frame_info: Optional[FrameInfo] = None
    processing_results: Optional[List[Dict[str, str]]] = None


class WebSocketResponse(BaseModel):
    type: str  # 'metadata_sync' | 'error'
    data: Optional[WebSocketResponseData] = None
    message: Optional[str] = None
