import asyncio

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket


@pytest.fixture
def sample_ws_message():
    return {
        "marker_id": "test-marker-1",
        "timestamp": 500,
        "roi": {"position": {"x": 0, "y": 0}, "size": {"width": 100, "height": 100}},
        "pdi_functions": [
            {
                "function": "color_segmentation",
                "parameters": {
                    "lower_color": {"r": 255, "g": 0, "b": 0},
                    "upper_color": {"r": 255, "g": 0, "b": 0},
                    "min_area": 100,
                    "max_area": 2000,
                },
                "output_type": "bounding_box",
            }
        ],
    }


@pytest.mark.asyncio
async def test_websocket_no_video(client: TestClient, sample_ws_message):
    websocket = client.websocket_connect("/api/v1/ws/metadata")
    with websocket as ws:
        ws.send_json(sample_ws_message)
        response = ws.receive_json()

        assert response["type"] == "error"
        assert "No video loaded" in response["message"]


@pytest.mark.asyncio
async def test_websocket_valid_processing(
    client: TestClient, sample_ws_message, sample_video_path
):
    """
    Test WebSocket processing with a valid video frame
    """
    # Upload video first
    with open(sample_video_path, "rb") as f:
        response = client.post(
            "/api/v1/video", files={"file": ("test.mp4", f, "video/mp4")}
        )
    assert response.status_code == 200

    # Test WebSocket processing
    websocket = client.websocket_connect("/api/v1/ws/metadata")
    with websocket as ws:
        ws.send_json(sample_ws_message)
        response = ws.receive_json()

        assert response["type"] == "metadata_sync"
        assert response["data"]["timestamp"] == sample_ws_message["timestamp"]
        assert "video_id" in response["data"]
        assert "results" in response["data"]
