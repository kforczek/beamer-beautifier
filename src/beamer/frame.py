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
        self._codes = [code]
        self._include_code = include_code
        self._src_dir = src_dir_path

        self._documents = []
        self._current_page = -1
        self._current_opt = 0  # original appearance
        self._suggest_changes()

    def compile(self):
        """
        Compiles this frame as a standalone temporary document.
        """
        self._documents.clear()
        tmp_dir_path = create_temp_dir(self._src_dir)
        for opt_idx, code in enumerate(self._codes):
            tmp_file_path = os.path.join(tmp_dir_path, f"{self._name}_opt{opt_idx}.tex")
            with open(tmp_file_path, "w") as tmp_file:
                if self._include_code:
                    tmp_file.write(self._include_code)
                    tmp_file.write("\n")
                tmp_file.write(tokens.DOC_BEGIN)
                tmp_file.write(code)
                tmp_file.write(tokens.DOC_END)

            pdf_path = compile_tex(tmp_file_path)
            self._documents.append(fitz.open(pdf_path))

    def code(self) -> str:
        """
        :return: LaTeX code of the frame (in currently selected version).
        """
        return self._codes[self._current_opt]

    def next_page(self):
        """
        :return: next page from the PDF file as list of PixMaps (first one is the original),
            or None if there is no next page.
        """
        if not self._documents:
            self.compile()
        if self._current_page < self._documents[self._current_opt].page_count - 1:
            self._current_page += 1
            return self._curr_page_as_pixmaps()
        return None

    def prev_page(self):
        """
        :return: previous page from the PDF file as list of PixMaps (first one is the original),
            or None if there is no previous page.
        """
        if not self._documents:
            self.compile()
        if self._current_page > 0:
            self._current_page -= 1
            return self._curr_page_as_pixmaps()
        return None

    def _curr_page_as_pixmaps(self):
        pixmaps = []
        for doc in self._documents:
            zoom_factor = 4.0
            mat = fitz.Matrix(zoom_factor, zoom_factor)
            pixmaps.append(doc.load_page(self._current_page).get_pixmap(matrix=mat, alpha=True))
        return pixmaps

    def _suggest_changes(self):
        base_code = self._codes[0]
        if tokens.ITEMIZE_BEGIN in base_code:
            items_begin = base_code.find(tokens.ITEMIZE_BEGIN) + len(tokens.ITEMIZE_BEGIN)

            items_to_center = base_code[: items_begin] + tokens.items_indent(2) + base_code[items_begin :]
            self._codes.append(items_to_center)
