
import os
# from .frame import Frame
from .compilation import compile_tex


class BeamerDocument:
    """Handles operations on Beamer code."""

    def __init__(self, doc_path: str):
        self._path = doc_path
        self._check_path()

    def compile(self) -> str:
        """Compiles the document and returns a path to the temporary PDF file."""
        return compile_tex(self._path)

    def _check_path(self) -> None:
        if not os.path.exists(self._path) or not os.path.isfile(self._path):
            raise InvalidPathError(f"Provided Beamer presentation path is invalid: {self._path}")
