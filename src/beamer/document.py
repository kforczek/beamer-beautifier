import os
from typing import Optional

from . import tokens
from .frame.frame import Frame
from .frame.improvements import LocalImprovementsManager, BackgroundImprovementsManager, GlobalImprovementsManager
from .page_info import PageInfo
from src.beautifier.color_generator import get_random_color_set


class NotBeamerPresentation(ValueError):
    pass


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

        color_versions = [get_random_color_set() for _ in range(4)]
        GlobalImprovementsManager.define_color_sets(color_versions)

    def next_page(self) -> Optional[PageInfo]:
        """
        :return: next page from the document as lists of PixMaps (first one is the original), or None if there is no next page.
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

    def prev_page(self) -> Optional[PageInfo]:
        """
        :return: previous page from the document as lists of PixMaps (first one is the original), or None if there is no previous page.
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

    def current_frame_alternative(self) -> int:
        """
        :return: index of the currently selected alternative for current frame.
        """
        # TODO remove - ImprovementsManager will be used here
        return self._frames[self._current_frame].current_alternative()

    def current_local_improvements(self) -> LocalImprovementsManager:
        """
        :return: local improvements manager for the current frame.
        """
        return self._frames[self._current_frame].local_improvements()

    def current_background_improvements(self) -> BackgroundImprovementsManager:
        """
        :return: background improvements manager for the current frame.
        """
        return self._frames[self._current_frame].background_improvements()

    def current_global_improvements(self) -> GlobalImprovementsManager:
        """
        :return: global improvements manager for the current frame.
        """
        return self._frames[self._current_frame].global_improvements()

    # def select_local_alternative(self, idx: int):
    #     """
    #     Handles selection of the alternative proposed for a current frame. The alternative is identified by its index
    #     (following the order of PixMaps returned by prev_page() and next_page() methods).
    #     :param idx: index of the alternative frame to be selected
    #     """
    #     self._frames[self._current_frame].select_alternative(idx)

    def save(self, output_path: str):
        """
        Saves the modified document in the output path, overwriting the file if it already exists.
        """
        if not output_path.endswith('.tex'):
            output_path = output_path + ".tex"
        if os.path.exists(output_path):
            os.remove(output_path)

        with open(output_path, 'w') as fh:
            fh.write(self._header)
            fh.write(f"\n{tokens.DOC_BEGIN}\n")
            for frame in self._frames:
                fh.write("\n" + frame.code())
            fh.write(self._post_frames_code)
            fh.write(f"\n{tokens.DOC_END}\n")

    def _check_path(self) -> None:
        if not os.path.exists(self._path) or not os.path.isfile(self._path):
            raise InvalidPathError(f"Provided Beamer presentation path is invalid: {self._path}")

    def _split_frames(self) -> None:
        """
        Splits the document and saves separate frame objects.
        """
        self._header = ""
        raw_frames = []
        with open(self._path, "r") as doc:
            content = doc.read()

            if not tokens.BEAMER_DECL in content:
                raise NotBeamerPresentation("Provided document is not a Beamer presentation.")

            if content.count(tokens.FRAME_BEGIN) != content.count(tokens.FRAME_END):
                raise FrameCountError("Detected different numbers of frame begins and ends, this won't compile")

            self._header = content[: content.find(tokens.DOC_BEGIN)]
            self._post_frames_code = content[content.rfind(tokens.FRAME_END) + len(tokens.FRAME_END): content.rfind(tokens.DOC_END)]
            raw_frames = content.split(tokens.FRAME_BEGIN)[1:]

        doc_name = os.path.basename(self._path).rsplit('.', 1)[0].replace(' ', '_')
        idx_len = len(str(len(raw_frames)))
        self._frames = []
        for idx, frame_code in enumerate(raw_frames, start=1):
            frame_code = frame_code[: frame_code.rfind(tokens.FRAME_END)]
            if tokens.FRAME_END in frame_code:
                raise FrameCountError("Detected multiple consecutive frame ends, this won't compile")

            if not frame_code.endswith("\n"):
                frame_code += "\n"
            frame_code = f"{tokens.FRAME_BEGIN}{frame_code}{tokens.FRAME_END}\n"
            frame_filename = f"{doc_name}_frame{idx:0{idx_len}}"

            frame = Frame(frame_filename, os.path.dirname(self._path), frame_code, self._header)
            self._frames.append(frame)
