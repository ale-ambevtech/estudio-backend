import io
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi import UploadFile

from app.services.video_manager import VideoManager


def create_test_video() -> bytes:
    """Creates a valid test video file in memory."""
    # Criar um vídeo sintético
    width, height = 64, 64
    fps = 30.0
    seconds = 1

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("temp.mp4", fourcc, fps, (width, height))

    try:
        for _ in range(int(fps * seconds)):
            # Criar um frame com um padrão simples
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.rectangle(frame, (20, 20), (40, 40), (255, 255, 255), -1)
            out.write(frame)
    finally:
        out.release()

    # Ler o arquivo gerado
    with open("temp.mp4", "rb") as f:
        content = f.read()

    # Limpar o arquivo temporário
    Path("temp.mp4").unlink()

    return content


@pytest.mark.asyncio
async def test_save_video(cleanup_uploads):
    # Criar um arquivo de vídeo válido
    video_content = create_test_video()
    file = UploadFile(filename="test.mp4", file=io.BytesIO(video_content))

    metadata = await VideoManager.save_video(file)

    assert metadata is not None
    assert metadata.filename == "test.mp4"
    assert metadata.width == 64
    assert metadata.height == 64
    assert metadata.fps == 30.0
    assert VideoManager.get_current_video() == metadata
    assert VideoManager.get_current_video_path().exists()


@pytest.mark.asyncio
async def test_cleanup_current_video(cleanup_uploads):
    # Criar um arquivo de vídeo válido
    video_content = create_test_video()
    file = UploadFile(filename="test.mp4", file=io.BytesIO(video_content))

    await VideoManager.save_video(file)
    await VideoManager.cleanup_current_video()

    assert VideoManager.get_current_video() is None
    assert VideoManager.get_current_video_path() is None
