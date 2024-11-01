from datetime import datetime

from pydantic import BaseModel


class VideoMetadata(BaseModel):
    id: str
    filename: str
    file_size: int
    duration: float
    width: int
    height: int
    fps: float
    uploaded_at: datetime
