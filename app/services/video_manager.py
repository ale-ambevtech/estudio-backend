import os
from datetime import UTC, datetime
from pathlib import Path

import aiofiles
import cv2
from fastapi import HTTPException, UploadFile

from ..models.video import VideoMetadata


class VideoManager:
    UPLOAD_DIR = Path("uploads/videos")
    MAX_WIDTH = 640
    MAX_HEIGHT = 360
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
            >>> import numpy as np
            >>> import cv2
            >>> from fastapi import UploadFile
            >>> async def test_save():
            ...     # Create a minimal valid video file
            ...     width, height = 64, 64
            ...     fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            ...     out = cv2.VideoWriter("temp.mp4", fourcc, 30.0, (width, height))
            ...     frame = np.zeros((height, width, 3), dtype=np.uint8)
            ...     out.write(frame)
            ...     out.release()
            ...     # Read the video file
            ...     with open("temp.mp4", "rb") as f:
            ...         content = f.read()
            ...     import os
            ...     os.unlink("temp.mp4")  # Clean up
            ...     # Test the upload
            ...     file = UploadFile(filename="test.mp4", file=io.BytesIO(content))
            ...     try:
            ...         metadata = await VideoManager.save_video(file)
            ...         print(metadata.filename == "test.mp4")
            ...     except HTTPException as e:
            ...         print("Error saving video:", e.detail)
            >>> asyncio.run(test_save())
            True
        """
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file provided",
            )

        await VideoManager.cleanup_current_video()
        VideoManager.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Group file-related variables
        file_info = {
            "extension": file.filename.split(".")[-1],
            "temp_filename": f"temp_video.{file.filename.split('.')[-1]}",
        }
        temp_path = VideoManager.UPLOAD_DIR / file_info["temp_filename"]

        try:
            async with aiofiles.open(temp_path, "wb") as out_file:
                content = await file.read()
                await out_file.write(content)

            # Get video properties in one go
            cap = cv2.VideoCapture(str(temp_path))
            if not cap.isOpened():
                raise HTTPException(
                    status_code=400,
                    detail="Invalid video file or unsupported format",
                )

            video_props = {
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            }
            cap.release()

            if video_props["fps"] <= 0 or video_props["frame_count"] <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid video file: could not determine video properties",
                )

            final_filename = f"current_video.{file_info['extension']}"
            final_path = VideoManager.UPLOAD_DIR / final_filename

            # Resize if needed and get final dimensions
            if (
                video_props["width"] > VideoManager.MAX_WIDTH
                or video_props["height"] > VideoManager.MAX_HEIGHT
            ):
                final_dimensions = VideoManager._resize_video(temp_path, final_path)
            else:
                temp_path.rename(final_path)
                final_dimensions = (video_props["width"], video_props["height"])

            VideoManager._current_video_path = final_path
            VideoManager._current_video = VideoMetadata(
                id="current",
                filename=file.filename,
                file_size=final_path.stat().st_size,
                duration=video_props["frame_count"] / video_props["fps"],
                width=final_dimensions[0],
                height=final_dimensions[1],
                fps=video_props["fps"],
                uploaded_at=datetime.now(UTC),
            )

            return VideoManager._current_video

        except Exception as e:
            if temp_path.exists():
                os.remove(temp_path)
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"Error processing video: {str(e)}",
            ) from e
        finally:
            if temp_path.exists():
                os.remove(temp_path)

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

    @staticmethod
    def _resize_video(input_path: Path, output_path: Path) -> tuple[int, int]:
        """
        Resizes video maintaining aspect ratio within MAX dimensions.
        Returns the new width and height.
        """
        cap = cv2.VideoCapture(str(input_path))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Calculate new dimensions maintaining aspect ratio
        ratio = min(VideoManager.MAX_WIDTH / width, VideoManager.MAX_HEIGHT / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        # Create video writer with new dimensions
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (new_width, new_height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            resized_frame = cv2.resize(frame, (new_width, new_height))
            out.write(resized_frame)

        cap.release()
        out.release()

        return new_width, new_height
