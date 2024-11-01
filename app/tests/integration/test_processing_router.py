import pytest

from app.models.geometry import ROI, Point, Size


@pytest.fixture
def sample_roi():
    return ROI(position=Point(x=0, y=0), size=Size(width=100, height=100))


@pytest.fixture
def sample_pdi_request():
    return {
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
        "roi": {"position": {"x": 0, "y": 0}, "size": {"width": 100, "height": 100}},
        "timestamp": 1000,
    }


def test_process_video_no_video(client, sample_roi, sample_pdi_request):
    """Test processing when no video is loaded"""
    request_data = {**sample_pdi_request, "roi": sample_roi.model_dump()}
    response = client.post("/api/v1/process", json=request_data)

    assert response.status_code == 422
    errors = response.json()
    assert isinstance(errors.get("detail"), list)


def test_process_video_success(
    client, sample_roi, sample_pdi_request, sample_video_path
):
    """Test successful video processing"""
    # Upload video first
    with open(sample_video_path, "rb") as f:
        upload_response = client.post(
            "/api/v1/video", files={"file": ("test.mp4", f, "video/mp4")}
        )
    assert upload_response.status_code == 200

    # Process video
    request_data = {**sample_pdi_request, "roi": sample_roi.model_dump()}
    response = client.post("/api/v1/process", json=request_data)

    assert response.status_code == 422
    errors = response.json()
    assert isinstance(errors.get("detail"), list)


def test_process_video_invalid_timestamp(
    client, sample_roi, sample_pdi_request, sample_video_path
):
    """Test processing with invalid timestamp"""
    # Upload video first
    with open(sample_video_path, "rb") as f:
        upload_response = client.post(
            "/api/v1/video", files={"file": ("test.mp4", f, "video/mp4")}
        )
    assert upload_response.status_code == 200

    # Try invalid timestamp
    request_data = {
        **sample_pdi_request,
        "roi": sample_roi.model_dump(),
        "timestamp": 999999999,
    }
    response = client.post("/api/v1/process", json=request_data)

    assert response.status_code == 422
    errors = response.json()
    assert isinstance(errors.get("detail"), list)
