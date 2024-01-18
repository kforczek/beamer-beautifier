import os
from typing import Optional, Any

from src.beamer import tokens
from src.beamer.compilation.loading_handler import PageLoadingHandler
from src.beamer.frame.frame import Frame
from src.beamer.frame.improvements import LocalImprovementsManager, BackgroundImprovementsManager, \
    ColorSetsImprovementsManager
from src.beamer.page_getter import PageGetter
from src.beautifier.background_generator import FrameProgressInfo
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
        self._page_count = sum([frame.page_count() for frame in self._frames])
        self._current_frame = -1
        self._current_page = -1

        color_versions = [get_random_color_set() for _ in range(4)]
        ColorSetsImprovementsManager.define_color_sets(color_versions)

    def next_page(self, page_getter: Optional[PageGetter]) -> Optional[Any]:
        """
        Notifies the compiling thread to prioritize loading next page and load it version-by-version
        into the provided page_getter.
        :return: original version of the page, or None if there is no next page.
        """
        if self._current_frame >= len(self._frames):
            return None

        if self._current_frame < 0:
            self._current_frame = 0

        page_from_frame = self._frames[self._current_frame].next_page(page_getter)
        if page_from_frame:
            self._current_page += 1
            return page_from_frame

        # No next page in current frame, go to the next one
        self._current_frame += 1
        return self.next_page(page_getter)

    def prev_page(self, page_getter: Optional[PageGetter]) -> Optional[Any]:
        """
        Notifies the compiling thread to prioritize loading previous page and load it version-by-version
        into the provided page_getter.
        :return: original version of the page, or None if there is no previous page.
        """
        if self._current_frame < 0:
            return None

        if self._current_frame >= len(self._frames):
            self._current_frame = len(self._frames) - 1

        page_from_frame = self._frames[self._current_frame].prev_page(page_getter)
        if page_from_frame:
            self._current_page -= 1
            return page_from_frame

        # No previous page in current frame, go to the previous one
        self._current_frame -= 1
        return self.prev_page(page_getter)

    def goto_page(self, page_idx: int, page_getter: PageGetter):
        if page_idx >= self._page_count:
            raise RuntimeError("Invalid page index")

        if page_idx == self._current_page:
            return

        if page_idx < self._current_page:
            fun_to_call = self.prev_page
            stop_cond_modifier = -1
        else:
            fun_to_call = self.next_page
            stop_cond_modifier = 1

        while self._current_page + stop_cond_modifier != page_idx:
            fun_to_call(None)

        page = fun_to_call(page_getter)

        assert page
        return page

    def goto_frame(self, frame_idx: int, page_getter: PageGetter):
        if frame_idx >= len(self._frames):
            raise RuntimeError("Invalid frame index")

        if frame_idx == self._current_frame:
            return

        if frame_idx < self._current_frame:
            fun_to_call = self.prev_page
            stop_cond_modifier = -1
        else:
            fun_to_call = self.next_page
            stop_cond_modifier = 1

        while self._current_frame + stop_cond_modifier != frame_idx:
            fun_to_call(None)

        page = fun_to_call(page_getter)

        assert page
        return page

    def regenerate_background_improvements(self, page_getter: PageGetter) -> None:
        """
        Notifies the compiling thread to prioritize regenerating background improvements for the current page
        and load them version-by-version into the provided page_getter.
        """
        self._frames[self._current_frame].regenerate_background_improvements(page_getter)

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

    def current_global_improvements(self) -> ColorSetsImprovementsManager:
        """
        :return: global improvements manager for the current frame.
        """
        return self._frames[self._current_frame].global_improvements()

    def current_frame_idx(self) -> int:
        """
        :return: index of the currently opened frame (starting at 0).
        """
        return self._current_frame

    def current_page_idx(self) -> int:
        """
        :return: index of the currently opened page (starting at 0).
        """
        return self._current_page

    def frame_count(self) -> int:
        """
        :return: count of all frames in the document.
        """
        return len(self._frames)

    def page_count(self) -> int:
        """
        :return: count of all pages in the document.
        """
        return self._page_count

    def save(self, output_path: str):
        """
        Saves the modified document in the output path, overwriting the file if it already exists.
        """
        if not output_path.endswith('.tex'):
            output_path = output_path + ".tex"

        if os.path.exists(output_path):
            os.remove(output_path)

        improved_code = self._org_raw_code
        global_colors_definitions = self._frames[0].improved_code().global_color_defs
        if global_colors_definitions:
            improved_code = improved_code.replace(self._header.rstrip(),
                                                  self._header.rstrip() + "\n" + global_colors_definitions)

        output_dir = os.path.dirname(output_path)
        for frame in self._frames:
            improved_code = improved_code.replace(frame.original_code().frame_str().strip(),
                                                  frame.improved_code().frame_str().strip())
            frame.save_resources(output_dir)

        with open(output_path, 'w') as fh:
            fh.write(improved_code)

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
            self._org_raw_code = doc.read()

            if not tokens.BEAMER_DECL in self._org_raw_code:
                raise NotBeamerPresentation("Provided document is not a Beamer presentation.")

            if self._org_raw_code.count(tokens.FRAME_BEGIN) != self._org_raw_code.count(tokens.FRAME_END):
                raise FrameCountError("Detected different numbers of frame begins and ends, this won't compile")

            self._header = self._org_raw_code[: self._org_raw_code.find(tokens.DOC_BEGIN)]
            self._post_frames_code = self._org_raw_code[self._org_raw_code.rfind(tokens.FRAME_END) + len(
                tokens.FRAME_END): self._org_raw_code.rfind(tokens.DOC_END)]
            raw_frames = self._org_raw_code.split(tokens.FRAME_BEGIN)[1:]

        doc_name = os.path.basename(self._path).rsplit('.', 1)[0].replace(' ', '_')
        idx_len = len(str(len(raw_frames)))

        loading_handler = PageLoadingHandler()
        self._frames = []
        for idx, frame_code in enumerate(raw_frames):
            frame_code = frame_code[: frame_code.rfind(tokens.FRAME_END)]
            if tokens.FRAME_END in frame_code:
                raise FrameCountError("Detected multiple consecutive frame ends, this won't compile")

            if not frame_code.endswith("\n"):
                frame_code += "\n"
            frame_code = f"{tokens.FRAME_BEGIN}{frame_code}{tokens.FRAME_END}\n"
            frame_filename = f"{doc_name}_frame{idx + 1:0{idx_len}}"
            progress_info = FrameProgressInfo(idx, len(raw_frames))

            frame = Frame(frame_filename, os.path.dirname(self._path),
                          frame_code, self._header, loading_handler, progress_info)
            self._frames.append(frame)
        loading_handler.init_frames(self._frames)
        loading_handler.start()
