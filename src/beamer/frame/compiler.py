import fitz

from src.beamer.compilation import compile_tex, CompilationError
from .code import FrameCode


class FrameCompiler:
    """Utility class for lazy compiling frame code as a standalone Beamer presentation."""
    def __init__(self, code: FrameCode, tmp_doc_path: str):
        self._code = code
        self._tmp_doc_path = tmp_doc_path
        self._is_compiled = False
        self._compiled_doc = None
        self._page_count = None

    def doc(self):
        """
        :return: Compiled PDF document resulting from the frame code.
        """
        if not self._is_compiled:
            self._compile()

        return self._compiled_doc

    def page_count(self):
        if self._page_count is None:
            self._page_count = self.doc().page_count if self.doc() else 0

        return self._page_count

    def code(self):
        return self._code

    def _compile(self):
        try:
            with open(self._tmp_doc_path, "w") as tmp_file:
                tmp_file.write(self._code.as_string())
            pdf_path = compile_tex(self._tmp_doc_path)
            self._compiled_doc = fitz.open(pdf_path)
        except CompilationError:
            print(f'Failed to compile improvement proposal: "{self._tmp_doc_path}"; will be ignored.')

        self._is_compiled = True
