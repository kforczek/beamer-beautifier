
import os
from . import tokens
from .frame import Frame
from .compilation import compile_tex


class InvalidPathError(AttributeError):
    pass


class FrameCountError(RuntimeError):
    pass


class BeamerDocument:
    """Handles operations on Beamer code."""
    def __init__(self, doc_path: str):
        self._path = doc_path
        self._check_path()
        self._split_frames()

    def compile(self) -> str:
        """Compiles the document and returns a path to the temporary PDF file."""
        for f in self._frames:
            f.compile()
        return compile_tex(self._path)

    def _check_path(self) -> None:
        if not os.path.exists(self._path) or not os.path.isfile(self._path):
            raise InvalidPathError(f"Provided Beamer presentation path is invalid: {self._path}")

    def _split_frames(self) -> None:
        """
        Splits the document and saves separate frame objects.
        """
        header = ""
        raw_frames = []
        with open(self._path, "r") as doc:
            content = doc.read()
            if content.count(tokens.FRAME_BEGIN) != content.count(tokens.FRAME_END):
                raise FrameCountError("Detected different numbers of frame begins and ends, this won't compile")

            header = content[: content.find(tokens.DOC_BEGIN)]
            raw_frames = content.split(tokens.FRAME_BEGIN)[1:]

        doc_name = os.path.basename(self._path).rsplit('.', 1)[0].replace(' ', '_')
        idx_len = len(str(len(raw_frames)))
        self._frames = []
        for idx, frame_code in enumerate(raw_frames, start=1):
            frame_code = frame_code[: frame_code.rfind(tokens.FRAME_END)]
            if tokens.FRAME_END in frame_code:
                raise FrameCountError("Detected multiple consecutive frame ends, this won't compile")

            frame_code = f"{tokens.FRAME_BEGIN} {frame_code} {tokens.FRAME_END}"
            frame_filename = f"{doc_name}_frame{idx:{idx_len}}"

            frame = Frame(frame_filename, os.path.dirname(self._path), frame_code, header)
            self._frames.append(frame)
