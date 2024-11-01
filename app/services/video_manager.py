import os
from datetime import UTC, datetime
from pathlib import Path

import aiofiles
import cv2
from fastapi import HTTPException, UploadFile

from ..models.video import VideoMetadata


class VideoManager:
    UPLOAD_DIR = Path("uploads/videos")
    _current_video: VideoMetadata | None = None
    _current_video_path: Path | None = None

    @staticmethod
    async def save_video(file: UploadFile) -> VideoMetadata:
        """
        Save an uploaded video file and return its metadata.

        Args:
            file: UploadFile object containing the video file.

        Returns:
            VideoMetadata: Metadata of the saved video.

        Raises:
            HTTPException: If the video file is invalid or cannot be processed.

        Examples:
            >>> import asyncio
            >>> import io
            >>> from fastapi import UploadFile
            >>> async def test_save():

            ...     content = b"video content"
            ...     file = UploadFile(
            ...         filename="test.mp4",
            ...         file=io.BytesIO(content)
            ...     )
            ...     try:
            ...         metadata = await VideoManager.save_video(file)
            ...         print(metadata.filename == "test.mp4")
            ...     except HTTPException:
            ...         print("Error saving video")

            True
        """
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file provided",
            )

        await VideoManager.cleanup_current_video()

        VideoManager.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        extension = file.filename.split(".")[-1]
        filename = f"current_video.{extension}"
        file_path = VideoManager.UPLOAD_DIR / filename

        try:
            async with aiofiles.open(file_path, "wb") as out_file:
                content = await file.read()
                await out_file.write(content)

            cap = cv2.VideoCapture(str(file_path))
            if not cap.isOpened():
                raise HTTPException(
                    status_code=400,
                    detail="Invalid video file or unsupported format",
                )

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if fps <= 0 or frame_count <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid video file: could not determine video properties",
                )

            duration = frame_count / fps
            cap.release()

            VideoManager._current_video_path = file_path
            VideoManager._current_video = VideoMetadata(
                id="current",
                filename=file.filename,
                file_size=file_path.stat().st_size,
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                uploaded_at=datetime.now(UTC),
            )

            return VideoManager._current_video

        except Exception as e:
            if file_path.exists():
                os.remove(file_path)
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"Error processing video: {str(e)}",
            ) from e

    @classmethod
    async def cleanup_current_video(cls) -> None:
        """
        Removes the current video file if it exists.

        Examples:
            >>> import asyncio
            >>> async def test_cleanup():
            ...     await VideoManager.cleanup_current_video()
            ...     assert VideoManager.get_current_video() is None
            ...     assert VideoManager.get_current_video_path() is None
            >>> asyncio.run(test_cleanup())
        """
        if cls._current_video_path and cls._current_video_path.exists():
            os.remove(cls._current_video_path)
            cls._current_video = None
            cls._current_video_path = None

    @classmethod
    def get_current_video(cls) -> VideoMetadata | None:
        """
        Retrieves metadata of the current video.

        Returns:
            VideoMetadata | None: Metadata of the current video or None if no video exists.

        Examples:
            >>> metadata = VideoManager.get_current_video()
            >>> assert metadata is None or isinstance(metadata, VideoMetadata)
        """
        return cls._current_video

    @classmethod
    def get_current_video_path(cls) -> Path | None:
        """
        Retrieves the file path of the current video.

        Returns:
            Path | None: Path to the current video file or None if no video exists.

        Examples:
            >>> path = VideoManager.get_current_video_path()
            >>> assert path is None or isinstance(path, Path)
        """
        return cls._current_video_path
