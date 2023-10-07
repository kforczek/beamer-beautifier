from .compilation import compile_tex, create_temp_dir
import os


class FrameBeginError(Exception):
    pass


class FrameEndError(Exception):
    pass


class FrameNameError(Exception):
    pass


class Frame:
    """Single Beamer frame"""

    _FRAME_BEGIN = "\\begin{frame}"
    _FRAME_END = "\\end{frame}"

    def __init__(self, name: str, src_dir_path: str, code: str, include_code: str):
        """
        :param name: identifier that will be used to identify temporary TeX and PDF files resulting from this frame
        :param src_dir_path: path to the directory where the document containing the frame is located
        :param code: source code of the frame itself, encapsuled by \begin{frame} and \end{frame} commands
        :param include_code: optional LaTeX code snippet containing package includes
        """
        if not code.startswith(self._FRAME_BEGIN):
            raise FrameBeginError(f"Frame code should begin with \"{self._FRAME_BEGIN}\"")

        if not code.endswith(self._FRAME_END):
            raise FrameEndError(f"Frame code should end with \"{self._FRAME_END}\"")

        if not name.isidentifier():
            raise FrameNameError("Frame name cannot contain non-alphanumerical characters except underscores")

        self._name = name
        self._code = code
        self._include_code = include_code
        self._src_dir = src_dir_path

    def compile(self) -> str:
        """
        Compiles this frame as a standalone temporary document.
        :return: path to the compiled PDF file
        """
        tmp_dir_path = create_temp_dir(self._src_dir)
        tmp_file_path = os.path.join(tmp_dir_path, f"{self._name}.tex")
        with open(tmp_file_path, "w") as tmp_file:
            if self._include_code:
                tmp_file.write(self._include_code)
                tmp_file.write("\n")
            tmp_file.write(self._code)

        return compile_tex(tmp_file_path)

    def code(self) -> str:
        """
        :return: LaTeX code of the frame.
        """
        return self._code
