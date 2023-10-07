
import os
# from .frame import Frame
from .compilation import compile_tex


class BeamerDocument:
    """Handles operations on Beamer code."""

    _TEMP_DIR_NAME = ".bb-temp"

    def __init__(self, doc_path: str):
        self._path = doc_path
        self._temp_dir = os.path.join(os.path.dirname(doc_path), self._TEMP_DIR_NAME)
        self._check_path()
        self._create_temp_dir()

    def compile(self) -> str:
        """Compiles the document and returns a path to the temporary PDF file."""
        return compile_tex(self._path, self._temp_dir)

    def _check_path(self) -> None:
        if not os.path.exists(self._path) or not os.path.isfile(self._path):
            raise InvalidPathError(f"Provided Beamer presentation path is invalid: {self._path}")

    def _create_temp_dir(self) -> None:
        if not os.path.exists(self._temp_dir):
            os.mkdir(self._temp_dir)


