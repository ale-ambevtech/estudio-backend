from fastapi import APIRouter, HTTPException, UploadFile

from ..models.video import VideoMetadata
from ..services.video_manager import VideoManager

router = APIRouter(tags=["Video Management"])

ALLOWED_EXTENSIONS = {"mp4", "avi", "mov"}


@router.post(
    "/video",
    summary="Upload a new video file",
    response_model=VideoMetadata,
)
async def upload_video(file: UploadFile) -> VideoMetadata:
    """
    Upload a new video file, replacing any existing one.
    Returns the metadata of the saved video.
    """
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Use: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    try:
        video_metadata = await VideoManager.save_video(file)
        return video_metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/video",
    summary="Get current video metadata",
    response_model=VideoMetadata | None,
)
async def get_current_video() -> VideoMetadata | None:
    """
    Get metadata of the currently loaded video
    """
    return VideoManager.get_current_video()
