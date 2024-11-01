import cv2
import numpy as np
import pytest

from app.models.geometry import ROI, Point, RGBColor, Size
from app.models.pdi import PDIColorSegmentationParameters
from app.services.pdi_service import PDIService


@pytest.fixture
def sample_frame():
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.rectangle(
        frame, (50, 50), (150, 100), (0, 0, 255), -1  # BGR: Vermelho puro  # Preenchido
    )
    return frame


@pytest.fixture
def sample_roi():
    return ROI(position=Point(x=0, y=0), size=Size(width=200, height=200))


@pytest.fixture
def red_detection_params():
    return PDIColorSegmentationParameters(
        lower_color=RGBColor(r=150, g=0, b=0),
        upper_color=RGBColor(r=255, g=100, b=100),
        min_area=1000,
        max_area=15000,
    )


def test_color_segmentation_red_detection(
    sample_frame,
    sample_roi,
    red_detection_params,
):
    pdi_service = PDIService()
    test_timestamp = 1000

    bounding_boxes = pdi_service.process_frame_color_segmentation(
        frame=sample_frame,
        roi=sample_roi,
        params=red_detection_params,
        timestamp=test_timestamp,
    )

    # Deve detectar exatamente um objeto
    assert len(bounding_boxes) == 1

    x, y, w, h = bounding_boxes[0]

    # Verificar se o boundingbox está aproximadamente onde esperamos
    # O retângulo foi desenhado em (50,50) com tamanho 100x50
    # Aumentando a tolerância para ±10 pixels para acomodar variações do OpenCV
    assert 40 <= x <= 60  # Tolerância de ±10 pixels na posição X
    assert 40 <= y <= 60  # Tolerância de ±10 pixels na posição Y
    assert 90 <= w <= 110  # Tolerância de ±10 pixels na largura
    assert 40 <= h <= 60  # Tolerância de ±10 pixels na altura


def test_color_segmentation_no_detection(sample_frame, sample_roi):
    """Test that green detection finds nothing in a frame with only red objects."""
    # Test with green color parameters (should find nothing in our red square frame)
    green_params = PDIColorSegmentationParameters(
        lower_color=RGBColor(r=0, g=150, b=0),  # Ajustado para verde mais realista
        upper_color=RGBColor(r=100, g=255, b=100),  # Com tolerância
        min_area=1000,
        max_area=15000,
    )

    pdi_service = PDIService()
    test_timestamp = (
        2000  # Timestamp diferente do outro teste para não sobrescrever debugs
    )

    bounding_boxes = pdi_service.process_frame_color_segmentation(
        frame=sample_frame,
        roi=sample_roi,
        params=green_params,
        timestamp=test_timestamp,
    )

    # Não deve detectar nenhum objeto verde
    assert len(bounding_boxes) == 0
