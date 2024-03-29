import os
from typing import List

from .code import FrameCode
from .compiler import FrameCompiler
from src.beautifier.frame_generator import get_local_generators
from src.beautifier.background_generator import get_backgrounds, FrameProgressInfo


class InvalidAlternativeIndex(ValueError):
    pass


#############  INTERFACES  #############

class ImprovementsManager:
    """Handles improvements generation and selection"""

    def __init__(self):
        self._current_opt = None
        self._versions = []

    def __getitem__(self, item):
        return self._versions[item]

    def current_version(self) -> FrameCompiler:
        """
        :return: A FrameCompiler that corresponds to current selection.
        """
        return self._versions[self._current_opt]

    def selected_index(self) -> int:
        """
        :return: Index of the currently selected improvement.
        """
        return self._current_opt+1 if self._current_opt is not None else 0

    def select_alternative(self, idx: int):
        """
        :param idx: index of the alternative version to be selected
        """
        if idx > len(self._versions) or idx < 0:
            raise InvalidAlternativeIndex(f"Invalid index of the frame alternative: {idx} "
                                          f"(correct index range: 0-{len(self._versions) - 1})")
        self._current_opt = idx-1 if idx > 0 else None

    def all_improvements(self) -> List[FrameCompiler]:
        """
        :return: All generated improvements, returned as document compilers.
        """
        return self._versions

    def generate_improvements(self):
        """Generates new set of improvements for the input (original) frame."""
        for _ in self.improvements_generator():
            pass

    def remove_improvement(self, improvement: FrameCompiler):
        """Removes a generated improvement from the list. Useful if the FrameCompiler failed
        to compile the improved document, which makes it essentially useless."""
        self._versions.remove(improvement)

    def improvements_generator(self):
        """Returns a generator that internally adds the improvements while yielding them to the caller."""
        raise NotImplementedError("Override in subclasses")

    def decorate(self, destination_code: FrameCode):
        """Applies changes to the destination code version according to currently selected improvement (if any)."""
        raise NotImplementedError("Override in subclasses")


class GlobalImprovementsManager(ImprovementsManager):
    """A category for which all instances of the improvements manager share the selected version.
        Note that due to how static variables work in Python, any subclass must manually define
        a static _GLOBAL_OPT field."""

    def current_version(self) -> FrameCompiler:
        self._current_opt = type(self)._GLOBAL_OPT
        return super().current_version()

    def selected_index(self) -> int:
        self._current_opt = type(self)._GLOBAL_OPT
        return super().selected_index()

    def select_alternative(self, idx: int):
        super().select_alternative(idx)
        type(self)._GLOBAL_OPT = self._current_opt


#############  FINAL IMPROVEMENT MANAGERS  #############

class LocalImprovementsManager(ImprovementsManager):
    _PREFIX = "l"
    _GENERATORS = get_local_generators()

    def __init__(self, original_code: FrameCode, base_name: str, tmp_dir_path: str):
        super().__init__()
        self._original_code = original_code
        self._base_name = base_name
        self._tmp_dir_path = tmp_dir_path

    def improvements_generator(self):
        self._versions.clear()
        index_gen = 0
        for improvement in self._GENERATORS:
            improved_code = improvement.improve(self._original_code)
            if not improved_code:
                continue

            filename = f"{self._base_name}_{self._PREFIX}{index_gen}.tex"
            filepath = os.path.join(self._tmp_dir_path, filename)
            self._versions.append(FrameCompiler(improved_code, filepath))
            yield self._versions[-1]
            index_gen += 1

    def decorate(self, destination_code: FrameCode):
        if self._current_opt is None:
            return
        improved_code = self.current_version().code()
        destination_code.header = improved_code.header
        destination_code.base_code = improved_code.base_code


class BackgroundImprovementsManager(GlobalImprovementsManager):
    _PREFIX = "b"
    _GENERATORS = get_backgrounds()
    _GLOBAL_OPT = None

    def __init__(self, original_frame_version: FrameCompiler, base_name: str, tmp_dir_path: str,
                 progress_info: FrameProgressInfo):
        super().__init__()
        self._original_version = original_frame_version
        self._base_name = base_name
        self._tmp_dir_path = tmp_dir_path
        self._progress_info = progress_info

    def improvements_generator(self):
        RES_FOLDER_NAME = "res"

        self._versions.clear()
        rect = self._original_version.doc().load_page(0).bound()
        original_code = self._original_version.code()
        dir_path = os.path.join(self._tmp_dir_path, RES_FOLDER_NAME)

        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        bg_idx = 0
        for background in self._GENERATORS:
            img_filename = f"{self._base_name}_bg{bg_idx}.png"
            img_full_filepath = os.path.join(dir_path, img_filename)
            img_relative_filepath = os.path.join(RES_FOLDER_NAME, img_filename)

            background.generate_background(img_full_filepath, (rect.width, rect.height), self._progress_info)

            full_code = FrameCode(original_code.header, original_code.base_code,
                                  original_code.global_color_defs, img_relative_filepath)

            tex_filename = f"{self._base_name}_{self._PREFIX}{bg_idx}.tex"
            tex_filepath = os.path.join(self._tmp_dir_path, tex_filename)
            self._versions.append(FrameCompiler(full_code, tex_filepath))
            yield self._versions[-1]
            bg_idx += 1

    def decorate(self, destination_code: FrameCode):
        if self.selected_index() == 0:
            return

        if not self._versions:
            self.generate_improvements()

        destination_code.bg_img_path = self.current_version().code().bg_img_path


class ColorSetsImprovementsManager(GlobalImprovementsManager):
    _PREFIX = "g"
    _COLOR_SETS = None
    _GLOBAL_OPT = None

    @classmethod
    def define_color_sets(cls, color_sets: List[str]):
        cls._COLOR_SETS = color_sets

    def __init__(self, original_code: FrameCode, base_name: str, tmp_dir_path: str):
        super().__init__()
        self._original_code = original_code
        self._base_name = base_name
        self._tmp_dir_path = tmp_dir_path

    def improvements_generator(self):
        self._versions.clear()
        index_gen = 0
        for colors in self._COLOR_SETS:
            code_with_colors = FrameCode(self._original_code.header, self._original_code.base_code,
                                         colors, self._original_code.bg_img_path)
            filename = f"{self._base_name}_{self._PREFIX}{index_gen}.tex"
            filepath = os.path.join(self._tmp_dir_path, filename)
            self._versions.append(FrameCompiler(code_with_colors, filepath))
            yield self._versions[-1]
            index_gen += 1

    def decorate(self, destination_code: FrameCode):
        if self.selected_index() == 0:
            return

        if not self._versions:
            self.generate_improvements()

        destination_code.global_color_defs = self.current_version().code().global_color_defs
