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


class BaseFrameCompilationError(CompilationError):
    pass


class InvalidAlternativeIndex(ValueError):
    pass


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

        self._frame_codes = [code]
        self._background_codes = [code]

        self._include_code = include_code
        self._src_dir = src_dir_path
        self._color_sets = color_sets

        self._frame_docs = []
        self._background_docs = []
        self._global_docs = []

        self._current_page = -1
        self._current_opt = 0  # original appearance
        self._tmp_dir_path = create_temp_dir(self._src_dir)
        self._suggest_changes()

    def compile(self):
        """
        Compiles this frame as a standalone temporary document.
        """
        self._frame_docs.clear()
        for opt_idx, code in enumerate(self._frame_codes):
            tmp_file_name = f"{self._name}_l{opt_idx}.tex"
            tmp_file_path = os.path.join(self._tmp_dir_path, tmp_file_name)
            try:
                self._frame_docs.append(self._try_compile_code(code, tmp_file_path))
            except BaseFrameCompilationError:
                if opt_idx == 0:
                    raise
                print(f'Failed to compile improvement proposal: "{tmp_file_name}"; will be ignored.')

        self._global_docs.append(self._try_compile_code(self._frame_codes[0], os.path.join(self._tmp_dir_path, f"{self._name}_g0.tex")))
        # TODO make it faster: first document is the same in local & global vectors
        for opt_idx, color_defs in enumerate(self._color_sets, start=1):
            tmp_file_name = f"{self._name}_g{opt_idx}.tex"
            tmp_file_path = os.path.join(self._tmp_dir_path, tmp_file_name)
            try:
                self._global_docs.append(self._try_compile_code(self._frame_codes[0], tmp_file_path, color_defs))
            except BaseFrameCompilationError:
                print(f'Failed to compile improvement proposal: "{tmp_file_name}"; will be ignored.')

        self._generate_backgrounds()

        # TODO make it faster: first document is the same in local & global vectors
        for opt_idx, code in enumerate(self._background_codes):
            tmp_file_name = f"{self._name}_bg{opt_idx}.tex"
            tmp_file_path = os.path.join(self._tmp_dir_path, tmp_file_name)
            try:
                self._background_docs.append(self._try_compile_code(code, tmp_file_path))
            except BaseFrameCompilationError:
                if opt_idx == 0:
                    raise
                print(f'Failed to compile improvement proposal: "{tmp_file_name}"; will be ignored.')

    def code(self) -> str:
        """
        :return: LaTeX code of the frame (in currently selected version).
        """
        return self._frame_codes[self._current_opt]

    def original_code(self) -> str:
        """
        :return: LaTeX code of the original frame, regardless of current selection.
        """
        return self._frame_codes[0]

    def next_page(self):
        """
        :return: next page from the PDF file as lists of PixMaps (first one is the original),
            or None if there is no next page.
        """
        if not self._frame_docs:
            self.compile()

        self._current_page += 1
        if self._current_page >= self._frame_docs[self._current_opt].page_count:
            return None

        return self._curr_page()

    def prev_page(self) -> Optional[PageInfo]:
        """
        :return: previous page from the PDF file as lists of PixMaps (first one is the original),
            or None if there is no previous page.
        """
        if not self._frame_docs:
            self.compile()

        self._current_page -= 1
        if self._current_page < 0:
            return None

        return self._curr_page()

    def current_alternative(self) -> int:
        """
        :return: index of the currently selected frame alternative.
        """
        return self._current_opt

    def select_alternative(self, idx: int):
        """
        Handles selection of the frame alternative, identified by its index (following the order of PixMaps returned
        by prev_page() and next_page() methods).
        :param idx: index of the alternative frame to be selected
        """
        if idx >= len(self._frame_codes) or idx < 0:
            raise InvalidAlternativeIndex(f"Invalid index of the frame alternative: {idx} "
                                          f"(correct index range: 0-{len(self._frame_codes) - 1})")

        self._current_opt = idx

    def _try_compile_code(self, code: str, tmp_file_path: str, color_defs=None):
        with open(tmp_file_path, "w") as tmp_file:
            if self._include_code:
                tmp_file.write(self._include_code + "\n")

            if color_defs:
                tmp_file.write(color_defs + "\n")

            tmp_file.write(tokens.DOC_BEGIN + "\n")
            tmp_file.write(code)
            tmp_file.write("\n" + tokens.DOC_END)

        try:
            pdf_path = compile_tex(tmp_file_path)
            return fitz.open(pdf_path)

        except CompilationError:
            raise BaseFrameCompilationError(f'Compilation failed for frame "{os.path.basename(tmp_file_path)}"')

    def _curr_page(self) -> PageInfo:
        frame_improvements = [self._pixmap_from_document(doc) for doc in self._frame_docs]
        bg_improvements = [self._pixmap_from_document(doc) for doc in self._background_docs]
        global_improvements = [self._pixmap_from_document(doc) for doc in self._global_docs]
        return PageInfo(frame_improvements, bg_improvements, global_improvements)

    def _pixmap_from_document(self, document):
        zoom_factor = 4.0
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        return document.load_page(self._current_page).get_pixmap(matrix=mat, alpha=True)

    def _suggest_changes(self):
        src_code = self.original_code()
        for improvement in self._IMPROVEMENTS:
            improved_code = improvement.improve(src_code)
            if improved_code:
                self._frame_codes.append(improved_code)

    def _generate_backgrounds(self):
        rect = self._frame_docs[0].load_page(0).bound()
        dir_path = os.path.join(self._tmp_dir_path, "res")

        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        bg_idx = 0
        for background in get_backgrounds():
            file_path = os.path.join(dir_path, f"{self._name}_bg{bg_idx}.png")
            background.generate_background(file_path, (rect.width, rect.height), None) # TODO frame idx etc
            bg_idx += 1

            bg_include_stmt = r"""\setbeamertemplate{background} 
{
    \includegraphics[width=\paperwidth,height=\paperheight]{""" + file_path + "}\n}"

            self._background_codes.append(f"{{\n{bg_include_stmt}\n{self._background_codes[0]}\n}}")
