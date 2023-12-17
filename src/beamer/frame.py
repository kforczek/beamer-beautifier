import os
from typing import List, Optional

import fitz
from . import tokens
from .compilation import compile_tex, create_temp_dir, CompilationError
from .page_info import PageInfo
from src.beautifier.frame_generator import get_improvements
from src.beautifier.background_generator import get_backgrounds


class FrameBeginError(Exception):
    pass


class FrameEndError(Exception):
    pass


class FrameNameError(Exception):
    pass


class InvalidAlternativeIndex(ValueError):
    pass


class FrameVersion:
    """A single option of how the frame can look."""
    def __init__(self, code: str, tmp_doc_path: str):
        self._code = code
        self._tmp_doc_path = tmp_doc_path
        self._compiled_doc = None

    def doc(self):
        if not self._compiled_doc:
            self._compile()

        return self._compiled_doc

    def _compile(self):
        try:
            with open(self._tmp_doc_path, "w") as tmp_file:
                tmp_file.write(self._code)
            pdf_path = compile_tex(self._tmp_doc_path)
            self._compiled_doc = fitz.open(pdf_path)
        except CompilationError:
            print(f'Failed to compile improvement proposal: "{self._tmp_doc_path}"; will be ignored.')


class VersionsContainer:
    def __init__(self, base_name: str, tmp_dir_path: str, tmp_doc_prefix: str):
        self._base_name = base_name
        self._tmp_dir_path = tmp_dir_path
        self._prefix = tmp_doc_prefix
        self._versions = []
        self._current_opt = 0
        self._index_gen = 1

    def __getitem__(self, item):
        return self._versions[item]

    def add(self, improved_code: str):
        filename = f"{self._base_name}_{self._prefix}{self._index_gen}.tex"
        filepath = os.path.join(self._tmp_dir_path, filename)
        self._versions.append(FrameVersion(improved_code, filepath))
        self._index_gen += 1

    def current_version(self):
        """
        :return: A FrameVersion that corresponds to current selection.
        """
        return self._versions[self._current_opt]

    def select_alternative(self, idx: int):
        """
        :param idx: index of the alternative version to be selected
        """
        if idx >= len(self._versions) or idx < 0:
            raise InvalidAlternativeIndex(f"Invalid index of the frame alternative: {idx} "
                                          f"(correct index range: 0-{len(self._versions) - 1})")
        self._current_opt = idx


class PageManager:
    """Isolated paging abstraction for all code versions (original and with various improvements)."""
    def __init__(self, original_version: FrameVersion, frame_name: str, tmp_dir_path: str):
        self.local_versions = VersionsContainer(frame_name, tmp_dir_path, "l")
        self.background_versions = VersionsContainer(frame_name, tmp_dir_path, "b")
        self.global_versions = VersionsContainer(frame_name, tmp_dir_path, "g")
        self.original_version = original_version

        self._current_page = -1

    def next_page(self) -> Optional[PageInfo]:
        self._current_page += 1
        if self._current_page >= self.background_versions.current_version().doc().page_count:
            return None

        return self._curr_page()

    def prev_page(self) -> Optional[PageInfo]:
        self._current_page -= 1
        if self._current_page < 0:
            return None

        return self._curr_page()

    def _curr_page(self) -> PageInfo:
        original_page = self._pixmap_from_document(self.original_version.doc())
        frame_improvements = [self._pixmap_from_document(version.doc()) for version in self.local_versions]
        bg_improvements = [self._pixmap_from_document(version.doc()) for version in self.background_versions]
        global_improvements = [self._pixmap_from_document(version.doc()) for version in self.global_versions]
        return PageInfo(original_page, frame_improvements, bg_improvements, global_improvements)

    def _pixmap_from_document(self, document):
        zoom_factor = 4.0
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        return document.load_page(self._current_page).get_pixmap(matrix=mat, alpha=True)


class Frame:
    """Single Beamer frame"""

    _IMPROVEMENTS = get_improvements()

    def __init__(self, name: str, src_dir_path: str, code: str, include_code: str, color_sets: List[str]):
        """
        :param name: identifier that will be used to identify temporary TeX and PDF files resulting from this frame
        :param src_dir_path: path to the directory where the document containing the frame is located
        :param code: source code of the frame itself, encapsuled by \begin{frame} and \end{frame} commands
        :param include_code: optional LaTeX code snippet containing package includes
        :param color_sets: codes that change the color scheme
        """
        if not code.lstrip().startswith(tokens.FRAME_BEGIN):
            raise FrameBeginError(f"Frame code should begin with \"{tokens.FRAME_BEGIN}\"")

        if not code.rstrip().endswith(tokens.FRAME_END):
            raise FrameEndError(f"Frame code should end with \"{tokens.FRAME_END}\"")

        if not name.isidentifier():
            raise FrameNameError("Frame name cannot contain non-alphanumerical characters except underscores")

        self._name = name

        self._original_code = code
        self._include_code = include_code

        self._src_dir = src_dir_path
        self._tmp_dir_path = create_temp_dir(self._src_dir)

        org_filepath = os.path.join(self._tmp_dir_path, f"{self._name}_org.tex")
        original_version = FrameVersion(full_code(include_code, code), org_filepath)
        self._page_mgr = PageManager(original_version, self._name, self._tmp_dir_path)

        self._generate_local_improvements()
        self._generate_background_improvements()
        self._generate_global_improvements(color_sets)

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
        return self._page_mgr.next_page()

    def prev_page(self) -> Optional[PageInfo]:
        """
        :return: previous page from the PDF file as lists of PixMaps (first one is the original),
            or None if there is no previous page.
        """
        return self._page_mgr.prev_page()

    def current_alternative(self) -> int:
        """
        :return: index of the currently selected frame alternative.
        """
        # TODO struct of three alternatives?
        return 0

    def select_alternative(self, idx: int):
        """
        Handles selection of the frame alternative, identified by its index (following the order of PixMaps returned
        by prev_page() and next_page() methods).
        :param idx: index of the alternative frame to be selected
        """
        # TODO refactor to three functions for alternatives in categories
        self._page_mgr.local_versions.select_alternative(idx)

    def _generate_local_improvements(self):
        src_code = self._original_code
        for improvement in self._IMPROVEMENTS:
            improved_code = improvement.improve(src_code)
            if improved_code:
                self._page_mgr.local_versions.add(full_code(self._include_code, improved_code))

    def _generate_background_improvements(self):
        rect = self._page_mgr.original_version.doc().load_page(0).bound()
        dir_path = os.path.join(self._tmp_dir_path, "res")

        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        bg_idx = 0
        for background in get_backgrounds():
            file_path = os.path.join(dir_path, f"{self._name}_bg{bg_idx}.png")
            background.generate_background(file_path, (rect.width, rect.height), None)  # TODO frame idx etc
            bg_idx += 1

            bg_include_stmt = r"""\setbeamertemplate{background} 
{
    \includegraphics[width=\paperwidth,height=\paperheight]{""" + file_path + "}\n}"

            improved_code = f"{{\n{bg_include_stmt}\n{self._original_code}\n}}"
            self._page_mgr.background_versions.add(full_code(self._include_code, improved_code))

    def _generate_global_improvements(self, color_sets):
        for colors in color_sets:
            self._page_mgr.global_versions.add(full_code(self._include_code, self._original_code, colors))


def full_code(header: str, base_code: str, color_defs=None):
    code = header + "\n"

    if color_defs:
        code += color_defs + "\n"

    code += tokens.DOC_BEGIN + "\n"
    code += base_code + "\n"
    code += tokens.DOC_END + "\n"

    return code
