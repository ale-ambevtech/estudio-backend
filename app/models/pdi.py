from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .geometry import ROI, RGBColor


class PDIFunctionType(Enum):
    COLOR_SEGMENTATION = "color_segmentation"
    SHAPE_DETECTION = "shape_detection"
    TEMPLATE_MATCHING = "template_matching"
    PEOPLE_DETECTION = "people_detection"


class PDIFunctionOutputType(Enum):
    BOUNDING_BOX = "bounding_box"
    COUNT = "count"
    BOOLEAN = "boolean"


class PDIColorSegmentationParameters(BaseModel):
    lower_color: RGBColor
    upper_color: RGBColor
    min_area: int
    max_area: int


class PDIShapeDetectionShape(Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"


class RectangleType(Enum):
    ANY = "any"
    SQUARE = "square"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    CUSTOM = "custom"


class AspectRatio(BaseModel):
    min_ratio: float = Field(ge=0.1, le=10.0)
    max_ratio: float = Field(ge=0.1, le=10.0)


class PDIShapeDetectionParameters(BaseModel):
    shape: PDIShapeDetectionShape
    rectangle_type: RectangleType = RectangleType.ANY
    min_area: int = 5000
    max_area: int = 100000
    custom_ratio: Optional[AspectRatio] = None


class PDITemplateMatchingParameters(BaseModel):
    template: str
    threshold: float


class PDIPeopleDetectionParameters(BaseModel):
    min_area: int
    max_area: int
    threshold: float


class PDIFunction(BaseModel):
    function: PDIFunctionType
    parameters: dict
    output_type: PDIFunctionOutputType


class ProcessVideoRequest(BaseModel):
    pdi_functions: list[PDIFunction]
    roi: ROI
    timestamp: int
