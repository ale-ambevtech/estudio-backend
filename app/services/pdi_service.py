from pathlib import Path

import cv2
import numpy as np

from ..models.geometry import ROI
from ..models.pdi import PDIColorSegmentationParameters


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
