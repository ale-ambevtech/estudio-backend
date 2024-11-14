import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket


def test_websocket_connection(client):
    with client.websocket_connect("/api/v1/ws/metadata") as websocket:
        # Envie uma mensagem simples para testar a conexão
        websocket.send_json({"timestamp": 1000})
        response = websocket.receive_json()

        # Verifica se recebemos uma resposta (mesmo que seja de erro)
        assert response is not None
        assert "type" in response


def test_websocket_invalid_message(client):
    with client.websocket_connect("/api/v1/ws/metadata") as websocket:
        # Send invalid message
        websocket.send_json({"invalid": "message"})
        response = websocket.receive_json()

        assert response["type"] == "error"
        assert "Invalid message format" in response["message"]


def test_websocket_no_video(client):
    with client.websocket_connect("/api/v1/ws/metadata") as websocket:
        # Send message without loading video
        websocket.send_json({"timestamp": 1000})
        response = websocket.receive_json()

        assert response["type"] == "error"
        assert "No video loaded" in response["message"]


@pytest.mark.asyncio
async def test_websocket_valid_sync(client, sample_video_path):
    # First upload a video
    with open(sample_video_path, "rb") as f:
        response = client.post(
            "/api/v1/video", files={"file": ("test.mp4", f, "video/mp4")}
        )
    assert response.status_code == 200

    # Then test WebSocket sync
    with client.websocket_connect("/api/v1/ws/metadata") as websocket:
        message = {
            "timestamp": 1000,
            "frame_info": {
                "markings": [{"x": 0, "y": 0, "width": 100, "height": 100}],
                "functions": ["detection"],
            },
        }
        websocket.send_json(message)
        response = websocket.receive_json()

        assert response["type"] == "metadata_sync"
        assert response["data"]["timestamp"] == 1000
        assert "video_id" in response["data"]
        assert "frame_info" in response["data"]
