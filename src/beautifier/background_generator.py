import os.path
from copy import copy
from typing import Tuple, Optional
import random
from PIL import Image, ImageDraw

from .color_generator import RGBRandomizer, RGBRandomizers, RandomColor


class FrameProgressInfo:
    """Contains information about the frame in the context of an entire presentation"""
    def __init__(self, frame_idx: int, frame_cnt: int):
        """
        :param frame_idx: index of the frame which will use this background (starting at 1).
        :param frame_cnt: number of all frame in a presentation.
        """
        self.frame_idx = frame_idx
        self.frame_cnt = frame_cnt


class BackgroundGenerator:
    """Represents a custom presentation background that can be applied to the frame by using
        a generated image file."""
    def generate_background(self, file_path: str, resolution: Tuple[int, int],
                            progress_info: Optional[FrameProgressInfo]):
        """
        :param file_path: path of the destination file.
        :param resolution: width and height of the presentation (in pixels).
        :param progress_info: optional information about the frame position in the original document.
        """
        raise NotImplementedError("Override in subclasses")


class RandomCirclesBackground(BackgroundGenerator):
    """Generator for backgrounds consisting of randomly placed circles of varying size,
        colored with one randomly selected color."""
    CIRCLE_RADIUS_MIN = 30
    CIRCLE_RADIUS_MAX = 60
    CIRCLES_OPACITY = 128
    MAX_FAILED_PLACEMENTS = 5

    SMALL_COLUMN_HEIGHT_MIN = 20
    SMALL_COLUMN_HEIGHT_MAX = 40
    LARGE_COLUMN_HEIGHT_MIN = 80
    LARGE_COLUMN_HEIGHT_MAX = 120
    COLUMNS_WIDTH = 5
    COLUMNS_COUNT = 100
    MEDIUM_COLUMNS_COUNT = 16
    LARGE_COLUMNS_COUNT = 15
    column_heights = []  # heights of the progress bar columns (if included)

    class __Circle:
        BOUNDING_BOX_SIZE = 30

        def __init__(self, xloc: int, yloc: int, radius: int):
            self.top_left = (xloc-radius, yloc-radius)
            self.bottom_right = (xloc+radius, yloc+radius)

        def collides(self, other):
            return is_farther(self.bottom_right, other.top_left, self.BOUNDING_BOX_SIZE) and is_farther(other.bottom_right, self.top_left, self.BOUNDING_BOX_SIZE) \
                or is_farther(other.bottom_right, self.top_left, self.BOUNDING_BOX_SIZE) and is_farther(self.bottom_right, other.top_left, self.BOUNDING_BOX_SIZE)

    def __init__(self, color_randomizer: RGBRandomizer):
        self._randomizer = color_randomizer

    def generate_background(self, file_path: str, resolution: Tuple[int, int],
                            progress_info: Optional[FrameProgressInfo]):

        resolution = 1920, round(1920 * min(resolution) / max(resolution))
        circle_defs = self._place_random_circles(resolution)

        img = Image.new(mode="RGB", size=resolution, color="white")
        self._draw_circles(img, circle_defs)

        if progress_info:
            column_defs = self._generate_progress_columns(progress_info)
            self._draw_progress_columns(img, resolution, column_defs)

        img.save(file_path)

    def _place_random_circles(self, resolution):
        circle_defs = set()
        margin = self.__Circle.BOUNDING_BOX_SIZE
        failed_placements = 0
        while failed_placements < self.MAX_FAILED_PLACEMENTS:
            radius = random.randint(self.CIRCLE_RADIUS_MIN, self.CIRCLE_RADIUS_MAX)
            xloc = random.randint(margin+radius, resolution[0]-radius-margin)
            yloc = random.randint(margin+radius, resolution[1]-radius-margin)

            circle = self.__Circle(xloc, yloc, radius)
            if not self._is_circle_valid(circle, circle_defs):
                failed_placements += 1
                continue
            else:
                failed_placements = 0

            circle_defs.add(circle)
        return circle_defs

    def _is_circle_valid(self, circle: __Circle, circle_defs) -> bool:
        """
        :return: True if the circle can be added, False if it collides with existing artifacts.
        """
        return not any([circle.collides(existing_circle) for existing_circle in circle_defs])

    def _draw_circles(self, img: Image, circle_defs):
        draw = ImageDraw.Draw(img)
        for circle in circle_defs:
            col = RandomColor(self._randomizer).as_tuple()
            draw.ellipse((circle.top_left, circle.bottom_right), fill=(col[0], col[1], col[2], self.CIRCLES_OPACITY))

    def _draw_progress_columns(self, img: Image, img_resolution, column_defs):
        x_start = round(img_resolution[0] * 0.1)
        x_end = round(img_resolution[0] * 0.9)
        x_step = (x_end - x_start) // self.COLUMNS_COUNT
        y_bottom = round(img_resolution[1] * 0.95)
        draw = ImageDraw.Draw(img)

        x = x_start
        for column_height in column_defs:
            c0 = (x, y_bottom - column_height)
            c1 = (x + self.COLUMNS_WIDTH, y_bottom)
            draw.rectangle((c0, c1), fill="black")

            x += x_step

    def _generate_progress_columns(self, progress_info: FrameProgressInfo) -> list[int]:
        if not self.column_heights:
            self._prepare_progress_columns()

        local_heights = copy(self.column_heights)
        progress_mid_point = round(progress_info.frame_idx * self.COLUMNS_COUNT / (progress_info.frame_cnt - 1))

        # Large columns
        left = progress_mid_point - self.LARGE_COLUMNS_COUNT // 2
        right = progress_mid_point + self.LARGE_COLUMNS_COUNT // 2
        self._randomize_selected_columns(local_heights, left, right, self.LARGE_COLUMN_HEIGHT_MIN, self.LARGE_COLUMN_HEIGHT_MAX)

        # Medium columns - to the left of the mid-point
        right = progress_mid_point - self.LARGE_COLUMNS_COUNT // 2
        left = right - self.MEDIUM_COLUMNS_COUNT // 2
        self._randomize_medium_columns(local_heights, left, right)

        # Medium columns - to the right of the mid-point
        left = progress_mid_point + self.LARGE_COLUMNS_COUNT // 2
        right = left + self.MEDIUM_COLUMNS_COUNT // 2
        self._randomize_medium_columns(local_heights, right, left)  # reversed range - the columns should be getting bigger from right to left

        return local_heights

    def _randomize_selected_columns(self, heights_list, left_idx, right_idx, min_val, max_val):
        left_idx = max(0, min(self.COLUMNS_COUNT, left_idx))
        right_idx = max(0, min(self.COLUMNS_COUNT, right_idx))

        if right_idx - left_idx <= 0:
            return

        for idx in range(left_idx, right_idx):
            heights_list[idx] = random.randint(min_val, max_val)

    def _randomize_medium_columns(self, heights_list, left_idx, right_idx):
        left_idx = max(0, min(self.COLUMNS_COUNT, left_idx))
        right_idx = max(0, min(self.COLUMNS_COUNT, right_idx))
        if left_idx == right_idx:
            return

        if left_idx < right_idx:
            step = 1
        else:
            left_idx = max(0, left_idx-1)
            right_idx = max(0, right_idx-1)
            step = -1

        curr_height_min = self.SMALL_COLUMN_HEIGHT_MAX
        curr_height_max = (self.SMALL_COLUMN_HEIGHT_MAX + self.LARGE_COLUMN_HEIGHT_MIN) // 2

        total_min = curr_height_max
        total_max = (self.LARGE_COLUMN_HEIGHT_MIN + self.LARGE_COLUMN_HEIGHT_MAX) // 2

        for idx in range(left_idx, right_idx, step):
            heights_list[idx] = random.randint(curr_height_min,  curr_height_max)

            curr_height_min = min(curr_height_min + 5, total_min)
            curr_height_max = min(curr_height_max + 3, total_max)

    @classmethod
    def _prepare_progress_columns(cls):
        for _ in range(cls.COLUMNS_COUNT):
            col_height = random.randint(cls.SMALL_COLUMN_HEIGHT_MIN, cls.SMALL_COLUMN_HEIGHT_MAX)
            cls.column_heights.append(col_height)


def get_backgrounds() -> list[BackgroundGenerator]:
    return [
        RandomCirclesBackground(RGBRandomizers.PINK_SHADES),
        RandomCirclesBackground(RGBRandomizers.GREEN_SHADES),
        RandomCirclesBackground(RGBRandomizers.PURPLE_SHADES),
    ]


def is_farther(pt1, pt2, margin):
    """
    :return: True if pt1.x > pt2.x and pt1.y > pt2.y (considering margin)
    """
    return pt1[0] + margin > pt2[0] and pt1[1] + margin > pt2[1]
