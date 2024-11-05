from pydantic import BaseModel


class RGBColor(BaseModel):
    r: int
    g: int
    b: int


class Point(BaseModel):
    x: int
    y: int


class Size(BaseModel):
    width: int
    height: int


class ROI(BaseModel):
    position: Point
    size: Size


class Line(BaseModel):
    start: Point
    end: Point


class Circle(BaseModel):
    x: int
    y: int
    r: int
    area: float
