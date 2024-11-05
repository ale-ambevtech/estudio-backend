from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from ..models.geometry import ROI, Circle
from ..models.pdi import (
    PDIColorSegmentationParameters,
    PDIShapeDetectionParameters,
    PDIShapeDetectionShape,
    RectangleType,
)


class ShapeDetectionResult:
    """Class to store intermediate detection results."""

    def __init__(self, frame: np.ndarray):
        self.debug_frame = frame.copy()
        self.bounding_boxes: List[Tuple[int, int, int, int]] = []
        self.detected_shapes = []


class PDIService:
    DEBUG_DIR = Path("debug")

    @staticmethod
    def _save_debug_image(
        step: int, name: str, image: np.ndarray, timestamp: int
    ) -> None:
        """Saves an image for debugging purposes with step number."""
        debug_dir = PDIService.DEBUG_DIR
        debug_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{step:02d}_{name}_{timestamp}.png"
        cv2.imwrite(str(debug_dir / filename), image)

    @staticmethod
    def process_frame_color_segmentation(
        frame: np.ndarray,
        roi: ROI,
        params: PDIColorSegmentationParameters,
        timestamp: int,
    ) -> list[tuple[int, int, int, int]]:
        """
        Performs color segmentation on a frame within the specified ROI.

        Args:
            frame (np.ndarray): Input frame to process
            roi (ROI): Region of interest to process
            params (PDIColorSegmentationParameters): Color segmentation parameters
            timestamp (int): Current video timestamp in milliseconds

        Returns:
            list[tuple[int, int, int, int]]: List of bounding boxes (x, y, w, h) for detected regions

        Examples:
            >>> import numpy as np
            >>> from app.models.geometry import ROI, Point, Size
            >>> from app.models.pdi import PDIColorSegmentationParameters, RGBColor
            >>> frame = np.zeros((200, 200, 3), dtype=np.uint8)
            >>> roi = ROI(position=Point(x=0, y=0), size=Size(width=200, height=200))
            >>> params = PDIColorSegmentationParameters(
            ...     lower_color=RGBColor(r=0, g=0, b=0),
            ...     upper_color=RGBColor(r=255, g=255, b=255),
            ...     min_area=100,
            ...     max_area=1000
            ... )
            >>> service = PDIService()
            >>> boxes = service.process_frame_color_segmentation(frame, roi, params, 1000)
            >>> isinstance(boxes, list)
            True
        """
        PDIService._save_debug_image(1, "original", frame, timestamp)

        roi_frame = frame[
            roi.position.y : roi.position.y + roi.size.height,
            roi.position.x : roi.position.x + roi.size.width,
        ]
        PDIService._save_debug_image(2, "roi", roi_frame, timestamp)

        processed_frame = cv2.GaussianBlur(roi_frame, (7, 7), 0)
        hsv_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2HSV)
        PDIService._save_debug_image(3, "hsv", hsv_frame, timestamp)

        mask = PDIService._create_color_mask(hsv_frame, params)
        PDIService._save_debug_image(4, "mask", mask, timestamp)

        mask = PDIService._apply_morphology(mask)
        PDIService._save_debug_image(5, "mask_morphology", mask, timestamp)

        masked_result = cv2.bitwise_and(roi_frame, roi_frame, mask=mask)
        PDIService._save_debug_image(6, "masked_result", masked_result, timestamp)

        return PDIService._find_bounding_boxes(
            roi_frame, mask, params.min_area, params.max_area, timestamp
        )

    @staticmethod
    def _create_color_mask(
        hsv_frame: np.ndarray, params: PDIColorSegmentationParameters
    ) -> np.ndarray:
        """Creates a binary mask for the specified color range."""
        if (
            params.lower_color.r > params.lower_color.g
            and params.lower_color.r > params.lower_color.b
        ):
            lower_mask = cv2.inRange(
                hsv_frame, np.array([0, 120, 70]), np.array([10, 255, 255])
            )
            upper_mask = cv2.inRange(
                hsv_frame, np.array([170, 120, 70]), np.array([180, 255, 255])
            )
            return cv2.bitwise_or(lower_mask, upper_mask)

        if (
            params.lower_color.g > params.lower_color.r
            and params.lower_color.g > params.lower_color.b
        ):
            return cv2.inRange(
                hsv_frame, np.array([35, 100, 100]), np.array([85, 255, 255])
            )

        if (
            params.lower_color.b > params.lower_color.r
            and params.lower_color.b > params.lower_color.g
        ):
            return cv2.inRange(
                hsv_frame, np.array([100, 100, 100]), np.array([140, 255, 255])
            )

        return cv2.inRange(
            hsv_frame, np.array([0, 100, 100]), np.array([180, 255, 255])
        )

    @staticmethod
    def _apply_morphology(mask: np.ndarray) -> np.ndarray:
        """Applies morphological operations to improve mask quality."""
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        return cv2.dilate(mask, kernel, iterations=2)

    @staticmethod
    def _find_bounding_boxes(
        original_frame: np.ndarray,
        mask: np.ndarray,
        min_area: int,
        max_area: int,
        timestamp: int,
    ) -> list[tuple[int, int, int, int]]:
        """Finds and filters contours to return valid bounding boxes."""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bounding_boxes = []
        debug_contours = original_frame.copy()
        debug_boxes = original_frame.copy()

        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                box = cv2.boundingRect(contour)
                bounding_boxes.append(box)

                cv2.drawContours(debug_contours, [contour], -1, (0, 255, 0), 2)
                cv2.rectangle(
                    debug_boxes,
                    (box[0], box[1]),
                    (box[0] + box[2], box[1] + box[3]),
                    (0, 255, 0),
                    2,
                )

        PDIService._save_debug_image(7, "contours", debug_contours, timestamp)
        PDIService._save_debug_image(8, "bounding_boxes", debug_boxes, timestamp)

        return bounding_boxes

    @staticmethod
    def process_frame_shape_detection(
        frame: np.ndarray,
        roi: ROI,
        params: PDIShapeDetectionParameters,
        timestamp: int,
    ) -> list[tuple[int, int, int, int]]:
        """
        Performs shape detection on a frame within the specified ROI.
        """
        roi_frame = frame[
            roi.position.y : roi.position.y + roi.size.height,
            roi.position.x : roi.position.x + roi.size.width,
        ]
        PDIService._save_debug_image(1, "1_roi", roi_frame, timestamp)

        gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        PDIService._save_debug_image(2, "2_gray", gray, timestamp)

        blurred = cv2.GaussianBlur(gray, (7, 7), 2)
        PDIService._save_debug_image(3, "3_blurred", blurred, timestamp)

        _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
        PDIService._save_debug_image(4, "4_binary", binary, timestamp)

        if params.shape == PDIShapeDetectionShape.CIRCLE:
            return PDIService._detect_circles(
                roi_frame, blurred, binary, params, timestamp
            )
        if params.shape == PDIShapeDetectionShape.TRIANGLE:
            return PDIService._detect_triangles(roi_frame, binary, params, timestamp)
        return PDIService._detect_rectangles(roi_frame, binary, params, timestamp)

    @staticmethod
    def _detect_circles(
        original_frame: np.ndarray,
        blurred: np.ndarray,
        binary: np.ndarray,
        params: PDIShapeDetectionParameters,
        timestamp: int,
    ) -> list[tuple[int, int, int, int]]:
        """Detects circles using HoughCircles and validates with contours."""
        result = ShapeDetectionResult(original_frame)
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        PDIService._save_contours_debug(binary, contours, 5, timestamp)

        circles = PDIService._find_circles(blurred, params)
        if circles is None:
            return []

        PDIService._process_detected_circles(
            circles[0],
            contours,
            binary.shape,
            params,
            result,
        )

        PDIService._save_debug_image(
            6, "6_final_detection", result.debug_frame, timestamp
        )
        return result.bounding_boxes

    @staticmethod
    def _process_detected_circles(
        circles: np.ndarray,
        contours: List[np.ndarray],
        shape: Tuple[int, int],
        params: PDIShapeDetectionParameters,
        result: ShapeDetectionResult,
    ) -> None:
        """Processes and validates detected circles."""
        circles = np.uint16(np.around(circles))
        for circle_arr in circles:
            x, y, r = circle_arr
            area = np.pi * r * r
            circle = Circle(x=x, y=y, r=r, area=area)

            if not PDIService._validate_circle(circle, contours, shape, params):
                continue

            PDIService._add_circle_to_result(circle, result)

    @staticmethod
    def _validate_circle(
        circle: Circle,
        contours: List[np.ndarray],
        shape: Tuple[int, int],
        params: PDIShapeDetectionParameters,
    ) -> bool:
        """Validates a detected circle."""
        circle_mask = np.zeros(shape, dtype=np.uint8)
        cv2.circle(circle_mask, (circle.x, circle.y), circle.r, 255, -1)

        for contour in contours:
            contour_mask = np.zeros(shape, dtype=np.uint8)
            cv2.drawContours(contour_mask, [contour], -1, 255, -1)

            overlap = cv2.bitwise_and(circle_mask, contour_mask)
            overlap_area = cv2.countNonZero(overlap)

            if (
                overlap_area > 0.7 * circle.area
                and params.min_area <= circle.area <= params.max_area
            ):
                return True
        return False

    @staticmethod
    def _add_circle_to_result(
        circle: Circle,
        result: ShapeDetectionResult,
    ) -> None:
        """Adds a validated circle to the result."""
        cv2.circle(result.debug_frame, (circle.x, circle.y), circle.r, (0, 255, 0), 2)

        box_x = int(circle.x - circle.r)
        box_y = int(circle.y - circle.r)
        box_size = int(2 * circle.r)
        result.bounding_boxes.append((box_x, box_y, box_size, box_size))

        cv2.rectangle(
            result.debug_frame,
            (box_x, box_y),
            (box_x + box_size, box_y + box_size),
            (255, 0, 0),
            2,
        )
        cv2.putText(
            result.debug_frame,
            f"area: {int(circle.area)}",
            (box_x, box_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
        )

    @staticmethod
    def _detect_triangles(
        original_frame: np.ndarray,
        binary: np.ndarray,
        params: PDIShapeDetectionParameters,
        timestamp: int,
    ) -> list[tuple[int, int, int, int]]:
        """Detects triangles using contour analysis."""
        result = ShapeDetectionResult(original_frame)

        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        PDIService._save_contours_debug(binary, contours, 5, timestamp)

        for contour in contours:
            area = cv2.contourArea(contour)
            if params.min_area <= area <= params.max_area:
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)

                if len(approx) == 3:
                    PDIService._add_triangle_to_result(contour, approx, result)

        PDIService._save_debug_image(
            6, "6_final_detection", result.debug_frame, timestamp
        )
        return result.bounding_boxes

    @staticmethod
    def _add_triangle_to_result(
        contour: np.ndarray,
        approx: np.ndarray,
        result: ShapeDetectionResult,
    ) -> None:
        """Adds a validated triangle to the result."""
        cv2.drawContours(result.debug_frame, [approx], -1, (0, 255, 0), 2)

        x, y, w, h = cv2.boundingRect(contour)
        result.bounding_boxes.append((x, y, w, h))

        cv2.rectangle(
            result.debug_frame,
            (x, y),
            (x + w, y + h),
            (255, 0, 0),
            2,
        )

        area = cv2.contourArea(contour)
        cv2.putText(
            result.debug_frame,
            f"area: {int(area)}",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
        )

    @staticmethod
    def _detect_rectangles(
        original_frame: np.ndarray,
        binary: np.ndarray,
        params: PDIShapeDetectionParameters,
        timestamp: int,
    ) -> list[tuple[int, int, int, int]]:
        """Detects rectangles using contour analysis and aspect ratios."""
        debug_frame = original_frame.copy()
        contours_frame = original_frame.copy()
        bounding_boxes = []

        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        cv2.drawContours(contours_frame, contours, -1, (0, 255, 0), 2)
        PDIService._save_debug_image(4, "all_contours", contours_frame, timestamp)

        for contour in contours:
            PDIService._process_rectangle_contour(
                contour,
                params,
                debug_frame,
                bounding_boxes,
            )

        PDIService._save_debug_image(5, "rectangles_detected", debug_frame, timestamp)
        return bounding_boxes

    @staticmethod
    def _process_rectangle_contour(
        contour: np.ndarray,
        params: PDIShapeDetectionParameters,
        debug_frame: np.ndarray,
        bounding_boxes: List[Tuple[int, int, int, int]],
    ) -> None:
        """Processes a single contour to detect rectangles."""
        area = cv2.contourArea(contour)
        if params.min_area <= area <= params.max_area:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)

            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                if h > 0:
                    aspect_ratio = w / h
                    min_ratio, max_ratio = PDIService._get_aspect_ratio_limits(params)

                    if min_ratio <= aspect_ratio <= max_ratio:
                        bounding_boxes.append((x, y, w, h))

                        cv2.drawContours(debug_frame, [approx], -1, (0, 255, 0), 2)
                        cv2.rectangle(
                            debug_frame, (x, y), (x + w, y + h), (255, 0, 0), 2
                        )
                        cv2.putText(
                            debug_frame,
                            f"ratio: {aspect_ratio:.2f}",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            1,
                        )

    @staticmethod
    def _save_contours_debug(
        binary: np.ndarray,
        contours: List[np.ndarray],
        step: int,
        timestamp: int,
    ) -> None:
        """Saves a debug image with contours."""
        binary_contours = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(binary_contours, contours, -1, (0, 255, 0), 2)
        PDIService._save_debug_image(
            step, f"{step}_binary_contours", binary_contours, timestamp
        )

    @staticmethod
    def _find_circles(
        blurred: np.ndarray, params: PDIShapeDetectionParameters
    ) -> np.ndarray:
        """Finds circles using HoughCircles."""
        return cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=int(np.sqrt(params.min_area / np.pi)),
            maxRadius=int(np.sqrt(params.max_area / np.pi)),
        )

    @staticmethod
    def _get_aspect_ratio_limits(
        params: PDIShapeDetectionParameters,
    ) -> Tuple[float, float]:
        """Returns aspect ratio limits based on rectangle type."""
        if params.rectangle_type == RectangleType.CUSTOM and params.custom_ratio:
            return params.custom_ratio.min_ratio, params.custom_ratio.max_ratio

        limits = {
            RectangleType.ANY: (0.2, 5.0),
            RectangleType.SQUARE: (0.8, 1.2),
            RectangleType.HORIZONTAL: (1.5, 5.0),
            RectangleType.VERTICAL: (0.2, 0.67),
        }
        return limits[params.rectangle_type]
