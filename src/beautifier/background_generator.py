import os.path
from typing import Tuple
import random
from PIL import Image, ImageDraw

from .color_generator import RGBRandomizer, RandomColor


# TODO refactor to not do this in the constructor

class CustomBackground:
    """Represents a custom presentation background that can be applied to the frame by using
        a generated image file."""

    def __init__(self, file_path: str, resolution: Tuple[int, int], frame_idx: int, frame_cnt: int, include_progress_bar=False):
        """
        :param resolution: width and height of the presentation (in pixels).
        :param frame_idx: index of the frame which will use this background (starting at 1).
        :param frame_cnt: number of all frame in a presentation.
        :param include_progress_bar: if True, then a presentation progress bar will be included in the generated image.
        """
        pass

    def image_path(self) -> str:
        """
        :return: Path to the generated image.
        """
        raise NotImplementedError("Override in subclasses")


class RandomCirclesBackground(CustomBackground):
    """A background consisting of randomly placed circles of varying size, colored with one randomly selected color."""
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

    def __init__(self, file_path: str, resolution: Tuple[int, int], frame_idx: int, frame_cnt: int, include_progress_bar=False):
        super().__init__(file_path, resolution, frame_idx, frame_cnt, include_progress_bar)

        self._file_path = file_path
        self._circle_defs = set()
        self._resolution = 1920, round(1920 * min(resolution) / max(resolution))
        self._place_random_circles()
        self._randomize_color()

        img = Image.new(mode="RGB", size=self._resolution)
        self._draw_circles(img)

        img.save(file_path)

    def image_path(self) -> str:
        """
        :return: Absolute path to the image file.
        """
        return self._file_path

    def _place_random_circles(self):
        margin = self.__Circle.BOUNDING_BOX_SIZE
        failed_placements = 0
        while failed_placements < 5:
            radius = random.randint(self.CIRCLE_RADIUS_MIN, self.CIRCLE_RADIUS_MAX)
            xloc = random.randint(margin+radius, self._resolution[0]-radius-margin)
            yloc = random.randint(margin+radius, self._resolution[1]-radius-margin)

            circle = self.__Circle(xloc, yloc, radius)
            if not self._is_circle_valid(circle):
                failed_placements += 1
                continue

            self._circle_defs.add(circle)

    def _is_circle_valid(self, circle: __Circle) -> bool:
        """
        :return: True if the circle can be added, False if it collides with existing artifacts.
        """
        return not any([circle.collides(existing_circle) for existing_circle in self._circle_defs])

    def _randomize_color(self):
        randomizer = RGBRandomizer(128, 255, 128, 255, 128, 255)
        self._color = RandomColor(randomizer)

    def _draw_circles(self, img: Image):
        draw = ImageDraw.Draw(img)
        for circle in self._circle_defs:
            col = self._color.as_tuple()
            draw.ellipse((circle.top_left, circle.bottom_right), fill=(col[0], col[1], col[2], self.CIRCLES_OPACITY))


def get_backgrounds(dir_path: str,
                    resolution: Tuple[int, int],
                    frame_idx: int, frame_cnt: int,
                    include_progress_bar=False) -> set[CustomBackground]:
    backgrounds = set()

    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    for idx in range(4):
        backgrounds.add(
            RandomCirclesBackground(
                os.path.join(dir_path, f"background{idx}.png"), resolution, frame_idx, frame_cnt, include_progress_bar
            ))

    return backgrounds


def is_farther(pt1, pt2, margin):
    """
    :return: True if pt1.x > pt2.x and pt1.y > pt2.y (considering margin)
    """
    return pt1[0] + margin > pt2[0] and pt1[1] + margin > pt2[1]
