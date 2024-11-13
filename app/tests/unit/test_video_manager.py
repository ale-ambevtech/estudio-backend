import io
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi import UploadFile

from app.services.video_manager import VideoManager


def create_test_video(width: int = 64, height: int = 64) -> bytes:
    """Creates a valid test video file in memory with specified dimensions."""
    fps = 30.0
    seconds = 1

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("temp.mp4", fourcc, fps, (width, height))

    try:
        for _ in range(int(fps * seconds)):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.rectangle(
                frame,
                (width // 3, height // 3),
                (2 * width // 3, 2 * height // 3),
                (255, 255, 255),
                -1,
            )
            out.write(frame)
    finally:
        out.release()

    with open("temp.mp4", "rb") as f:
        content = f.read()

    Path("temp.mp4").unlink()
    return content


@pytest.mark.asyncio
async def test_save_video(cleanup_uploads):
    """Test saving a video file."""
    # Create test video content
    video_content = create_test_video(64, 64)
    file = UploadFile(filename="test.mp4", file=io.BytesIO(video_content))

    # Save the video
    metadata = await VideoManager.save_video(file)

    # Verify metadata
    assert metadata is not None
    assert metadata.filename == "test.mp4"
    assert metadata.width == 64
    assert metadata.height == 64
    assert metadata.fps == 30.0
    assert VideoManager.get_current_video() == metadata
    assert VideoManager.get_current_video_path().exists()


@pytest.mark.asyncio
async def test_cleanup_current_video(cleanup_uploads):
    """Test cleaning up the current video."""
    # First save a video
    video_content = create_test_video(64, 64)
    file = UploadFile(filename="test.mp4", file=io.BytesIO(video_content))
    await VideoManager.save_video(file)

    # Verify video exists
    assert VideoManager.get_current_video() is not None
    assert VideoManager.get_current_video_path().exists()

    # Cleanup
    await VideoManager.cleanup_current_video()

    # Verify cleanup
    assert VideoManager.get_current_video() is None
    current_path = VideoManager.get_current_video_path()
    assert current_path is None or not current_path.exists()


@pytest.mark.asyncio
async def test_save_video_with_resize(cleanup_uploads):
    """Test saving and auto-resizing a large video file."""
    # Create a test video with dimensions larger than max
    width, height = 1280, 720  # Larger than max dimensions
    video_content = create_test_video(width, height)
    file = UploadFile(filename="test.mp4", file=io.BytesIO(video_content))

    # Save the video
    metadata = await VideoManager.save_video(file)

    # Verify metadata and resizing
    assert metadata is not None
    assert metadata.width <= VideoManager.MAX_WIDTH
    assert metadata.height <= VideoManager.MAX_HEIGHT
    # Verify aspect ratio is maintained
    original_ratio = 1280 / 720
    new_ratio = metadata.width / metadata.height
    assert abs(original_ratio - new_ratio) < 0.01
