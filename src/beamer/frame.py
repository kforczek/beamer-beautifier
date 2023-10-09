import os
import fitz
from . import tokens
from .compilation import compile_tex, create_temp_dir


class FrameBeginError(Exception):
    pass


class FrameEndError(Exception):
    pass


class FrameNameError(Exception):
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
        if not code.startswith(tokens.FRAME_BEGIN):
            raise FrameBeginError(f"Frame code should begin with \"{tokens.FRAME_BEGIN}\"")

        if not code.endswith(tokens.FRAME_END):
            raise FrameEndError(f"Frame code should end with \"{tokens.FRAME_END}\"")

        if not name.isidentifier():
            raise FrameNameError("Frame name cannot contain non-alphanumerical characters except underscores")

        self._name = name
        self._code = code
        self._include_code = include_code
        self._src_dir = src_dir_path

        self._document = None
        self._current_page = -1

    def compile(self):
        """
        Compiles this frame as a standalone temporary document.
        """
        tmp_dir_path = create_temp_dir(self._src_dir)
        tmp_file_path = os.path.join(tmp_dir_path, f"{self._name}.tex")
        with open(tmp_file_path, "w") as tmp_file:
            if self._include_code:
                tmp_file.write(self._include_code)
                tmp_file.write("\n")
            tmp_file.write(tokens.DOC_BEGIN)
            tmp_file.write(self._code)
            tmp_file.write(tokens.DOC_END)

        pdf_path = compile_tex(tmp_file_path)
        self._document = fitz.open(pdf_path)

    def code(self) -> str:
        """
        :return: LaTeX code of the frame.
        """
        return self._code

    def next_page(self):
        """
        :return: next page from the PDF file as PixMap, or None if there is no next page.
        """
        if not self._document:
            self.compile()
        if self._current_page < self._document.page_count - 1:
            self._current_page += 1
            return self._curr_page_as_pixmap()
        return None

    def prev_page(self):
        """
        :return: previous page from the PDF file as PixMap, or None if there is no previous page.
        """
        if not self._document:
            self.compile()
        if self._current_page > 0:
            self._current_page -= 1
            return self._curr_page_as_pixmap()
        return None

    def _curr_page_as_pixmap(self):
        zoom_factor = 4.0
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        pix = self._document.load_page(self._current_page).get_pixmap(matrix=mat, alpha=True)