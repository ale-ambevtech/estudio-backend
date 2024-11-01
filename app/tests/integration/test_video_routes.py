from pathlib import Path

import pytest
from fastapi import UploadFile


def test_upload_video_success(client, sample_video_path, cleanup_uploads):
    """Test successful video upload."""
    with open(sample_video_path, "rb") as f:
        files = {"file": ("sample.mp4", f, "video/mp4")}
        response = client.post("/api/v1/video", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "sample.mp4"
    assert data["width"] == 64
    assert data["height"] == 64
    assert data["fps"] == 30.0


def test_upload_invalid_extension(client, cleanup_uploads):
    """Test upload with invalid file extension."""
    content = b"not a video file"
    files = {"file": ("test.txt", content, "text/plain")}

    response = client.post("/api/v1/video", files=files)

    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]
