import os.path
from typing import Tuple, Optional
import random
from PIL import Image, ImageDraw

from .color_generator import RGBRandomizer, RandomColor


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
        :param progress_info: additional information about the frame that can affect the generated result.
        """
        raise NotImplementedError("Override in subclasses")


class RandomCirclesBackground(BackgroundGenerator):
    """Generator for backgrounds consisting of randomly placed circles of varying size,
        colored with one randomly selected color."""
    CIRCLE_RADIUS_MIN = 30
    CIRCLE_RADIUS_MAX = 60
    CIRCLES_OPACITY = 128

    class __Circle:
        BOUNDING_BOX_SIZE = 30

        def __init__(self, xloc: int, yloc: int, radius: int):
            self.top_left = (xloc-radius, yloc-radius)
            self.bottom_right = (xloc+radius, yloc+radius)

        def collides(self, other):
            return is_farther(self.bottom_right, other.top_left, self.BOUNDING_BOX_SIZE) \
                or is_farther(other.bottom_right, self.top_left, self.BOUNDING_BOX_SIZE)

    def generate_background(self, file_path: str, resolution: Tuple[int, int],
                            progress_info: Optional[FrameProgressInfo]):

        resolution = 1920, round(1920 * min(resolution) / max(resolution))
        circle_defs = self._place_random_circles(resolution)
        self._randomize_color()

        img = Image.new(mode="RGB", size=resolution)
        self._draw_circles(img, circle_defs)

        img.save(file_path)

    def _place_random_circles(self, resolution):
        circle_defs = set()
        margin = self.__Circle.BOUNDING_BOX_SIZE
        failed_placements = 0
        while failed_placements < 5:
            radius = random.randint(self.CIRCLE_RADIUS_MIN, self.CIRCLE_RADIUS_MAX)
            xloc = random.randint(margin+radius, resolution[0]-radius-margin)
            yloc = random.randint(margin+radius, resolution[1]-radius-margin)

            circle = self.__Circle(xloc, yloc, radius)
            if not self._is_circle_valid(circle, circle_defs):
                failed_placements += 1
                continue

            circle_defs.add(circle)
        return circle_defs

    def _is_circle_valid(self, circle: __Circle, circle_defs) -> bool:
        """
        :return: True if the circle can be added, False if it collides with existing artifacts.
        """
        return not any([circle.collides(existing_circle) for existing_circle in circle_defs])

    def _randomize_color(self):
        randomizer = RGBRandomizer(128, 255, 128, 255, 128, 255)
        self._color = RandomColor(randomizer)

    def _draw_circles(self, img: Image, circle_defs):
        draw = ImageDraw.Draw(img)
        for circle in circle_defs:
            col = self._color.as_tuple()
            draw.ellipse((circle.top_left, circle.bottom_right), fill=(col[0], col[1], col[2], self.CIRCLES_OPACITY))


def get_backgrounds() -> set[BackgroundGenerator]:
    backgrounds = set()

    for idx in range(4):
        backgrounds.add(RandomCirclesBackground())

    return backgrounds


def is_farther(pt1, pt2, margin):
    """
    :return: True if pt1.x > pt2.x and pt1.y > pt2.y (considering margin)
    """
    return pt1[0] + margin > pt2[0] and pt1[1] + margin > pt2[1]
