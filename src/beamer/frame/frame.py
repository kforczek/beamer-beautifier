import os
from typing import List, Optional

import fitz
from src.beamer import tokens
from src.beamer.compilation import compile_tex, create_temp_dir, CompilationError
from src.beamer.page_info import PageInfo
from .code import FrameCode
from .compiler import FrameCompiler
from .improvements import (ImprovementsManager, LocalImprovementsManager,
                           BackgroundImprovementsManager, ColorSetsImprovementsManager)

from src.beautifier.background_generator import get_backgrounds


class FrameBeginError(Exception):
    pass


class FrameEndError(Exception):
    pass


class FrameNameError(Exception):
    pass


class BaseFrameCompilationError(RuntimeError):
    pass


class Frame:
    """Single Beamer frame"""

    def __init__(self, name: str, src_dir_path: str, code: str, include_code: str):
        """
        :param name: identifier that will be used to identify temporary TeX and PDF files resulting from this frame
        :param src_dir_path: path to the directory where the document containing the frame is located
        :param code: source code of the frame itself, encapsuled by \begin{frame} and \end{frame} commands
        :param include_code: optional LaTeX code snippet containing package includes
        """

        self._check_init_conditions(code, name)

        self._name = name
        self._src_dir = src_dir_path
        self._tmp_dir_path = create_temp_dir(self._src_dir)
        self._current_page = -1
        self._are_improvements_generated = False

        original_code = FrameCode(include_code, code)
        self._init_improvements(original_code)

    def _check_init_conditions(self, frame_code: str, frame_name: str):
        if not frame_code.lstrip().startswith(tokens.FRAME_BEGIN):
            raise FrameBeginError(f"Frame code should begin with \"{tokens.FRAME_BEGIN}\"")

        if not frame_code.rstrip().endswith(tokens.FRAME_END):
            raise FrameEndError(f"Frame code should end with \"{tokens.FRAME_END}\"")

        if not frame_name.isidentifier():
            raise FrameNameError("Frame name cannot contain non-alphanumerical characters except underscores")

    def _init_improvements(self, original_code: FrameCode):
        org_filepath = os.path.join(self._tmp_dir_path, f"{self._name}_org.tex")
        self._original_version = FrameCompiler(original_code, org_filepath)

        self._local_versions = LocalImprovementsManager(original_code, self._name, self._tmp_dir_path)
        self._background_versions = BackgroundImprovementsManager(self._original_version, self._name, self._tmp_dir_path)
        self._global_versions = ColorSetsImprovementsManager(original_code, self._name, self._tmp_dir_path)

    def code(self) -> str:
        """
        :return: LaTeX code of the frame (in currently selected version).
        """
        # TODO invent combining versions in different categories
        return self._original_code

    def next_page(self) -> Optional[PageInfo]:
        """
        :return: next page from the PDF file as lists of PixMaps (first one is the original),
            or None if there is no next page.
        """
        if not self._are_improvements_generated:
            self._generate_improvements()

        self._current_page += 1
        if self._current_page >= self._original_version.page_count():
            return None

        return self._curr_page()

    def prev_page(self) -> Optional[PageInfo]:
        """
        :return: previous page from the PDF file as lists of PixMaps (first one is the original),
            or None if there is no previous page.
        """
        if not self._are_improvements_generated:
            self._generate_improvements()

        self._current_page -= 1
        if self._current_page < 0:
            return None

        return self._curr_page()

    def local_improvements(self) -> LocalImprovementsManager:
        """
        :return: local improvements manager for this frame.
        """
        return self._local_versions

    def background_improvements(self) -> BackgroundImprovementsManager:
        """
        :return: background improvements manager for this frame.
        """
        return self._background_versions

    def global_improvements(self) -> ColorSetsImprovementsManager:
        """
        :return: global improvements manager for this frame.
        """
        return self._global_versions

    # def select_local_alternative(self, idx: int):
    #     """
    #     Handles selection of the local frame alternative, identified by its index.
    #     :param idx: index of the alternative frame to be selected
    #     """
    #     self._local_versions.select_alternative(idx)

    def _generate_improvements(self):
        for improvements in (self._local_versions, self._background_versions, self._global_versions):
            improvements.generate_improvements()
        self._are_improvements_generated = True

    def _curr_page(self) -> PageInfo:
        original_doc = self._original_version.doc()
        if not original_doc:
            raise BaseFrameCompilationError("Cannot continue when the original frame failed to compile")
        original_page = self._pixmap_from_document(original_doc)
        frame_improvements = self._improvements_as_pixmaps(self._local_versions)
        bg_improvements = self._improvements_as_pixmaps(self._background_versions)
        global_improvements = self._improvements_as_pixmaps(self._global_versions)
        return PageInfo(original_page, frame_improvements, bg_improvements, global_improvements)

    def _improvements_as_pixmaps(self, improvements: ImprovementsManager):
        pixmaps = []
        for version in improvements:
            doc = version.doc()
            if doc:
                pixmaps.append(self._pixmap_from_document(doc))
        return pixmaps

    def _pixmap_from_document(self, document):
        zoom_factor = 4.0
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        return document.load_page(self._current_page).get_pixmap(matrix=mat, alpha=True)
