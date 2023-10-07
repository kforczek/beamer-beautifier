import subprocess
import os
# from .frame import Frame


class InvalidPathError(AttributeError):
    pass


class CompilationError(OSError):
    def __init__(self, *args):
        super().__init__(*args)
        print()



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
        try:
            subprocess.check_call(
                ['xelatex', f'-output-directory={self._temp_dir}', '-interaction=nonstopmode', self._path],
                cwd=os.path.dirname(self._path)
            )
        except subprocess.CalledProcessError:
            raise CompilationError(f"Failed to compile the LaTeX document: compilation process"
                                   f" ended with an error (see logs for more info).") from None

        file_path = self._get_dest_temp_path()
        if not os.path.exists(file_path):
            raise CompilationError("Failed to compile the LaTeX document: output PDF file not created for unknown reason")

        return file_path

    # def compile_slide(self, frame: Frame) -> str:
    #     # Compiles one specific slide (identified by an index starting at 1)
    #     # and returns a path to the temporary PDF file.
    #     # TODO
    #     pass

    def _check_path(self) -> None:
        if not os.path.exists(self._path) or not os.path.isfile(self._path):
            raise InvalidPathError(f"Provided Beamer presentation path is invalid: {self._path}")

    def _create_temp_dir(self) -> None:
        if not os.path.exists(self._temp_dir):
            os.mkdir(self._temp_dir)

    def _get_dest_temp_path(self) -> str:
        return os.path.join(self._temp_dir, os.path.basename(self._path).split('.')[0] + ".pdf")
