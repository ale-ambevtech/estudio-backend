import cv2
import numpy as np
import pytest

from app.models.geometry import ROI, Point, Size
from app.models.pdi import (
    AspectRatio,
    PDIShapeDetectionParameters,
    PDIShapeDetectionShape,
    RectangleType,
)
from app.services.pdi_service import PDIService


@pytest.fixture
def sample_roi():
    return ROI(position=Point(x=0, y=0), size=Size(width=200, height=200))


@pytest.fixture
def rectangle_frame():
    """Creates a frame with a clear rectangle for testing."""
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.rectangle(frame, (50, 50), (150, 150), (255, 255, 255), -1)
    return frame


@pytest.fixture
def circle_frame():
    """Creates a frame with a clear circle for testing."""
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(frame, (100, 100), 50, (255, 255, 255), -1)
    return frame


@pytest.fixture
def triangle_frame():
    """Creates a frame with a clear triangle for testing."""
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    pts = np.array([[100, 50], [50, 150], [150, 150]], np.int32)
    cv2.fillPoly(frame, [pts], (255, 255, 255))
    return frame


def test_rectangle_detection(rectangle_frame, sample_roi):
    """Test rectangle detection with a clear white rectangle."""
    params = PDIShapeDetectionParameters(
        shape=PDIShapeDetectionShape.RECTANGLE,
        min_area=1000,
        max_area=15000,
    )

    pdi_service = PDIService()
    boxes = pdi_service.process_frame_shape_detection(
        frame=rectangle_frame,
        roi=sample_roi,
        params=params,
        timestamp=1000,
    )

    assert len(boxes) == 1
    x, y, w, h = boxes[0]
    assert 45 <= x <= 55  # Allow for small variations
    assert 45 <= y <= 55
    assert 95 <= w <= 105
    assert 95 <= h <= 105


def test_circle_detection(circle_frame, sample_roi):
    """Test circle detection with a clear white circle."""
    params = PDIShapeDetectionParameters(
        shape=PDIShapeDetectionShape.CIRCLE,
        min_area=5000,
        max_area=15000,
    )

    pdi_service = PDIService()
    boxes = pdi_service.process_frame_shape_detection(
        frame=circle_frame,
        roi=sample_roi,
        params=params,
        timestamp=2000,
    )

    assert len(boxes) == 1
    x, y, w, h = boxes[0]
    # Centro do círculo em (100,100) com raio 50
    assert 45 <= x <= 55
    assert 45 <= y <= 55
    assert 95 <= w <= 105  # Diâmetro ~100
    assert 95 <= h <= 105


def test_triangle_detection(triangle_frame, sample_roi):
    """Test triangle detection with a clear white triangle."""
    params = PDIShapeDetectionParameters(
        shape=PDIShapeDetectionShape.TRIANGLE,
        min_area=5000,
        max_area=15000,
    )

    pdi_service = PDIService()
    boxes = pdi_service.process_frame_shape_detection(
        frame=triangle_frame,
        roi=sample_roi,
        params=params,
        timestamp=3000,
    )

    assert len(boxes) == 1
    x, y, w, h = boxes[0]
    # Triângulo com base 100 e altura 100
    assert 45 <= x <= 55
    assert 45 <= y <= 55
    assert 95 <= w <= 105
    assert 95 <= h <= 105


def test_custom_rectangle_ratio(rectangle_frame, sample_roi):
    """Test rectangle detection with custom aspect ratio."""
    params = PDIShapeDetectionParameters(
        shape=PDIShapeDetectionShape.RECTANGLE,
        rectangle_type=RectangleType.CUSTOM,
        custom_ratio=AspectRatio(min_ratio=0.8, max_ratio=1.2),
        min_area=5000,
        max_area=15000,
    )

    pdi_service = PDIService()
    boxes = pdi_service.process_frame_shape_detection(
        frame=rectangle_frame,
        roi=sample_roi,
        params=params,
        timestamp=4000,
    )

    assert len(boxes) == 1  # Deve detectar o retângulo quadrado


def test_no_detection_wrong_shape(rectangle_frame, sample_roi):
    """Test that triangle detection finds nothing in a frame with only rectangles."""
    params = PDIShapeDetectionParameters(
        shape=PDIShapeDetectionShape.TRIANGLE,
        min_area=1000,
        max_area=15000,
    )

    # Criar uma imagem com um retângulo claro
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.rectangle(frame, (50, 50), (150, 150), (255, 255, 255), -1)

    pdi_service = PDIService()
    boxes = pdi_service.process_frame_shape_detection(
        frame=frame,
        roi=sample_roi,
        params=params,
        timestamp=5000,
    )

    # Não deve detectar triângulos em uma imagem com apenas retângulos
    assert len(boxes) == 0


def test_no_detection_small_area(rectangle_frame, sample_roi):
    """Test that nothing is detected when min_area is too high."""
    params = PDIShapeDetectionParameters(
        shape=PDIShapeDetectionShape.RECTANGLE,
        min_area=50000,  # Área muito grande
        max_area=100000,
    )

    pdi_service = PDIService()
    boxes = pdi_service.process_frame_shape_detection(
        frame=rectangle_frame,
        roi=sample_roi,
        params=params,
        timestamp=6000,
    )

    assert len(boxes) == 0


@pytest.fixture
def wide_rectangle_frame():
    """Creates a frame with a wide rectangle for testing."""
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.rectangle(frame, (25, 75), (175, 125), (255, 255, 255), -1)
    return frame


def test_wide_rectangle_detection(wide_rectangle_frame, sample_roi):
    """Test detection of wide rectangles."""
    params = PDIShapeDetectionParameters(
        shape=PDIShapeDetectionShape.RECTANGLE,
        rectangle_type=RectangleType.HORIZONTAL,
        min_area=5000,
        max_area=15000,
    )

    pdi_service = PDIService()
    boxes = pdi_service.process_frame_shape_detection(
        frame=wide_rectangle_frame,
        roi=sample_roi,
        params=params,
        timestamp=7000,
    )

    assert len(boxes) == 1
    x, y, w, h = boxes[0]
    assert w > h * 1.5  # Garante que é um retângulo horizontal
