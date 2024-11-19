from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, model_serializer

from ..models.geometry import ROI
from ..models.pdi import PDIFunction


class WebSocketMessage(BaseModel):
    timestamp: int
    roi: ROI
    pdi_functions: List[PDIFunction]


class WebSocketResponseData(BaseModel):
    timestamp: int
    video_id: str
    results: List[Dict[str, Any]]

    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "video_id": self.video_id,
            "results": [
                {k: str(v) if isinstance(v, Enum) else v for k, v in result.items()}
                for result in self.results
            ],
        }


class WebSocketResponse(BaseModel):
    type: str  # 'metadata_sync' | 'error'
    data: Optional[WebSocketResponseData] = None
    message: Optional[str] = None

    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data.model_dump() if self.data else None,
            "message": self.message,
        }
