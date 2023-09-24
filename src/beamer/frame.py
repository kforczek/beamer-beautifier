class FrameBeginError(Exception):
    pass


class FrameEndError(Exception):
    pass


class Frame:
    """Single Beamer frame"""

    _FRAME_BEGIN = "\\begin{frame}"
    _FRAME_END = "\\end{frame}"

    def __init__(self, code: str):
        if not code.startswith(self._FRAME_BEGIN):
            raise FrameBeginError(f"Frame code should begin with \"{self._FRAME_BEGIN}\"")

        if not code.endswith(self._FRAME_END):
            raise FrameEndError(f"Frame code should end with \"{self._FRAME_END}\"")

        self._code = code

    def compile(self, include_code="") -> str:
        """
        Compiles this frame as a standalone temporary document.
        :param include_code: optional LaTeX code snippet containing package includes
        :return: path to the compiled PDF file
        """

    def code(self) -> str:
        """
        :return: LaTeX code of the frame.
        """
        return self._code
