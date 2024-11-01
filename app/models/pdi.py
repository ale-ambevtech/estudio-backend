from enum import Enum

from pydantic import BaseModel

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


class PDIShapeDetectionParameters(BaseModel):
    shape: PDIShapeDetectionShape
    min_area: int
    max_area: int


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
