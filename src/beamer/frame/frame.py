import os
import shutil
from typing import Optional, Any
from copy import copy

from src.beamer import tokens
from src.beamer.compilation.compilation import create_temp_dir
from src.beamer.compilation.loading_handler_iface import IPageLoadingHandler, PriorityLoadTask, \
    BackgroundRegenerationTask

from src.beamer.page_getter import PageGetter
from src.beamer.graphics import pixmap_from_document
from .code import FrameCode
from .compiler import FrameCompiler
from .improvements import (LocalImprovementsManager,
                           BackgroundImprovementsManager, ColorSetsImprovementsManager)
from ...beautifier.background_generator import FrameProgressInfo


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

    def __init__(self, name: str, src_dir_path: str, code: str,
                 include_code: str, loading_handler: IPageLoadingHandler, progress_info: FrameProgressInfo):
        """
        :param name: identifier that will be used to identify temporary TeX and PDF files resulting from this frame
        :param src_dir_path: path to the directory where the document containing the frame is located
        :param code: source code of the frame itself, encapsuled by \begin{frame} and \end{frame} commands
        :param include_code: optional LaTeX code snippet containing package includes
        :param loading_handler: handler for multithreading compilation and page loading
        :param progress_info: information about the frame location in the source document
        """

        _check_init_conditions(code, name)

        self._name = name
        self._src_dir = src_dir_path
        self._loading_handler = loading_handler
        self._idx = progress_info.frame_idx

        self._tmp_dir_path = create_temp_dir(self._src_dir)
        self._current_page = -1

        original_code = FrameCode(include_code, code)
        self._init_improvements(original_code, progress_info)

        is_first = progress_info.frame_idx == 0
        is_last = progress_info.frame_idx == progress_info.frame_cnt - 1
        self._min_page_val = 0 if is_first else -1
        self._max_page_val = self._original_version.page_count() - 1 if is_last else self._original_version.page_count()

    def improved_code(self) -> FrameCode:
        """
        :return: LaTeX code of the frame (in currently selected version).
        """
        code = copy(self._original_version.code())
        self._ensure_improvements_generated()
        for improvement in (self._local_versions, self._background_versions, self._global_versions):
            improvement.decorate(code)

        return code

    def original_code(self) -> FrameCode:
        """
        :return: original (input) LaTeX code of the frame.
        """
        return self._original_version.code()

    def next_page(self, page_getter: Optional[PageGetter]) -> Optional[Any]:
        """
        Immediately returns the pixmap of the original next page and - if page_getter has been provided - notifies
        the compiling thread to prioritize loading corresponding improvements.
        :return: next page from the original PDF file, or None if there is no next page.
        """
        if self._current_page >= self._original_version.page_count() - 1:
            self._current_page = self._max_page_val
            return None

        self._current_page += 1
        return self._load_current_page(page_getter)

    def prev_page(self, page_getter: Optional[PageGetter]) -> Optional[Any]:
        """
        Immediately returns the pixmap of the original previous page and - if page_getter has been provided - notifies
        the compiling thread to prioritize loading corresponding improvements.
        :return: previous page from the original PDF file, or None if there is no previous page.
        """
        if self._current_page <= 0:
            self._current_page = self._min_page_val
            return None

        self._current_page -= 1
        return self._load_current_page(page_getter)

    def page_count(self):
        """
        :return: count of all pages in the frame.
        """
        return self._original_version.page_count()

    def regenerate_background_improvements(self, page_getter: PageGetter) -> None:
        """
        Notifies the compiling thread to prioritize regenerating background improvements for the current page.
        """
        task = BackgroundRegenerationTask(self._idx, self._current_page, page_getter)
        self._loading_handler.set_priority_task(task)

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

    def save_resources(self, dest_folder: str):
        """
        Saves any resources (generated background images) that this frame instance might be using. The resources are
        copied to the destination folder. The folder is created if it didn't exist before.
        """
        background_code = self._background_versions.current_version().code()
        if not background_code.bg_img_path:
            return

        src_filepath = os.path.join(self._tmp_dir_path, background_code.bg_img_path)
        full_dest_dir = os.path.join(dest_folder, os.path.dirname(background_code.bg_img_path))

        if not os.path.exists(full_dest_dir):
            os.mkdir(full_dest_dir)

        shutil.copy2(src_filepath, full_dest_dir)

    def _init_improvements(self, original_code: FrameCode, progress_info: FrameProgressInfo):
        org_filepath = os.path.join(self._tmp_dir_path, f"{self._name}_org.tex")
        self._original_version = FrameCompiler(original_code, org_filepath)
        if not self._original_version.doc():
            raise BaseFrameCompilationError("Compilation failed for an original frame - this is a critical error")

        self._local_versions = LocalImprovementsManager(original_code, self._name, self._tmp_dir_path)
        self._background_versions = BackgroundImprovementsManager(
            self._original_version, self._name, self._tmp_dir_path, progress_info)
        self._global_versions = ColorSetsImprovementsManager(original_code, self._name, self._tmp_dir_path)

    def _load_current_page(self, page_getter: Optional[PageGetter]):
        if page_getter:
            task = PriorityLoadTask(self._idx, self._current_page, page_getter)
            self._loading_handler.set_priority_task(task)
        return pixmap_from_document(self._original_version.doc(), self._current_page)

    def _ensure_improvements_generated(self):
        for improvements in (self._local_versions, self._background_versions, self._global_versions):
            if not improvements.all_improvements():
                improvements.generate_improvements()


def _check_init_conditions(frame_code: str, frame_name: str):
    if not frame_code.lstrip().startswith(tokens.FRAME_BEGIN):
        raise FrameBeginError(f"Frame code should begin with \"{tokens.FRAME_BEGIN}\"")

    if not frame_code.rstrip().endswith(tokens.FRAME_END):
        raise FrameEndError(f"Frame code should end with \"{tokens.FRAME_END}\"")

    if not frame_name.isidentifier():
        raise FrameNameError("Frame name cannot contain non-alphanumerical characters except underscores")
