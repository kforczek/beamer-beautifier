
import os
import src.beamer.tokens as tokens
from src.beamer.frame import Frame


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

        self._current_frame = -1

    def next_page(self):
        """
        :return: next page from the document as list of PixMaps (first one is the original), or None if there is no next page.
        """
        if self._current_frame >= len(self._frames):
            return None

        if self._current_frame < 0:
            self._current_frame = 0

        page_from_frame = self._frames[self._current_frame].next_page()
        if page_from_frame:
            return page_from_frame

        # No next page in current frame, go to the next one
        self._current_frame += 1
        return self.next_page()

    def prev_page(self):
        """
        :return: previous page from the document as list of PixMaps (first one is the original), or None if there is no previous page.
        """
        if self._current_frame < 0:
            return None

        if self._current_frame >= len(self._frames):
            self._current_frame = len(self._frames) - 1

        page_from_frame = self._frames[self._current_frame].prev_page()
        if page_from_frame:
            return page_from_frame

        # No previous page in current frame, go to the previous one
        self._current_frame -= 1
        return self.prev_page()

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

            frame_code = f"{tokens.FRAME_BEGIN}{frame_code}\n{tokens.FRAME_END}"
            frame_filename = f"{doc_name}_frame{idx:0{idx_len}}"

            frame = Frame(frame_filename, os.path.dirname(self._path), frame_code, header)
            self._frames.append(frame)
