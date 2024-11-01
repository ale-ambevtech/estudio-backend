import io
import shutil
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.video_manager import VideoManager


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def cleanup_uploads():
    yield
    # Cleanup after each test
    await VideoManager.cleanup_current_video()
    if VideoManager.UPLOAD_DIR.exists():
        shutil.rmtree(VideoManager.UPLOAD_DIR)


def create_test_video() -> bytes:
    """Creates a valid test video file in memory."""
    width, height = 64, 64
    fps = 30.0
    seconds = 1

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("temp.mp4", fourcc, fps, (width, height))

    try:
        for _ in range(int(fps * seconds)):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.rectangle(frame, (20, 20), (40, 40), (255, 255, 255), -1)
            out.write(frame)
    finally:
        out.release()

    with open("temp.mp4", "rb") as f:
        content = f.read()

    Path("temp.mp4").unlink()
    return content


@pytest.fixture
def sample_video_path(tmp_path) -> Path:
    """Creates a sample video file for testing."""
    video_path = tmp_path / "sample.mp4"
    video_content = create_test_video()

    with open(video_path, "wb") as f:
        f.write(video_content)

    return video_path
