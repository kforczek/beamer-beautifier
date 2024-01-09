from typing import Optional
from .scanner import TokenScanner
from ..beamer import tokens
from ..beamer.frame.code import FrameCode


class FrameImprovement:
    def check_preconditions(self, frame_code: FrameCode) -> bool:
        """Checks preconditions (if any) and returns True if an improvement can be made."""
        raise NotImplementedError("Overridden in subclasses")

    def improve(self, frame_code: FrameCode) -> Optional[FrameCode]:
        """
        Suggests an improvement of the frame if preconditions are met (or if there are no preconditions).
        :return: Improved code of the frame or None if the preconditions exist and are not met.
        """
        if not self.check_preconditions(frame_code):
            return None

        return self._improve(frame_code)

    def _improve(self, frame_code: FrameCode) -> FrameCode:
        raise NotImplementedError("Overridden in subclasses")


def get_local_generators() -> set[FrameImprovement]:
    return {
        ItemizeIndentIncrease(),
        EnumerateToTable(),
        ItemizeToTable()
    }


###############################################################################


class ItemizeIndentIncrease(FrameImprovement):
    def check_preconditions(self, frame_code: FrameCode) -> bool:
        return tokens.ITEMIZE_BEGIN in frame_code.base_code

    def _improve(self, frame_code: FrameCode) -> FrameCode:
        code = frame_code.base_code
        items_begin = code.find(tokens.ITEMIZE_BEGIN) + len(tokens.ITEMIZE_BEGIN)
        items_to_center = code[: items_begin] + tokens.items_indent(2) + code[items_begin:]
        return FrameCode(frame_code.header, items_to_center, frame_code.global_color_defs, frame_code.bg_img_path)


class ListToTable(FrameImprovement):
    class SplitCode:
        def __init__(self, pre_list_code: str, post_list_code: str, items: list[str]):
            self.pre_list_code = pre_list_code
            self.post_list_code = post_list_code
            self.items = items

    def __init__(self, list_begin_tkn: str, list_end_tkn: str):
        self._list_begin_tkn = list_begin_tkn
        self._list_end_tkn = list_end_tkn
        self._scanner = TokenScanner(tokens.ITEMIZE_BEGIN, tokens.ITEMIZE_END,
                                     tokens.ENUMERATE_BEGIN, tokens.ENUMERATE_END, tokens.ITEM)
        self._cache: dict[str, ListToTable.SplitCode] = dict()

    def check_preconditions(self, frame_code: FrameCode) -> bool:
        count = len(self._split_top_list_items(frame_code.base_code).items)
        return 1 < count <= 4

    def _improve(self, frame_code: FrameCode) -> FrameCode:
        split_code = self._split_top_list_items(frame_code.base_code)
        changed_snippet = r"\begin{tabular}{" + 'c'*len(split_code.items) + "}\n"
        for item in split_code.items[:-1]:
            changed_snippet += item + " & "
        changed_snippet += split_code.items[-1]
        changed_snippet += "\n\\end{tabular}"

        rstripped = split_code.pre_list_code.rstrip()
        if rstripped.endswith("\\\\") or rstripped.endswith("\n\n"):
            pre_code = split_code.pre_list_code
        else:
            pre_code = f"{split_code.pre_list_code} \\\\"

        return FrameCode(frame_code.header, f"{pre_code}{changed_snippet}{split_code.post_list_code}",
                         frame_code.global_color_defs, frame_code.bg_img_path)

    def _split_top_list_items(self, frame_code: str) -> SplitCode:
        if frame_code in self._cache:
            return self._cache[frame_code]

        depth = 0
        items = []
        buf = ""
        pre_code = ""
        post_code = ""
        list_done = False
        first_item = True
        for token in self._scanner.tokenize(frame_code):
            if not list_done:
                if token == self._list_begin_tkn or depth > 0 and token in (tokens.ITEMIZE_BEGIN, tokens.ENUMERATE_BEGIN):
                    depth += 1
                    if depth == 1:
                        continue
                elif token == self._list_end_tkn or depth > 1 and token in (tokens.ENUMERATE_END, tokens.ITEMIZE_END):
                    depth -= 1
                    if depth == 0:
                        if buf:
                            items.append(buf)
                            buf = ""
                        list_done = True
                        continue

            if depth >= 1:
                if depth == 1 and token == tokens.ITEM and not first_item:
                    # Flush the buffer
                    items.append(buf)
                    buf = ""
                else:
                    # Append to the buffer
                    if token != tokens.ITEM or depth > 1:
                        buf += token
                    elif first_item and depth == 1:
                        buf = ""
                        first_item = False
            elif not list_done:
                # Save everything to pre-code
                pre_code += token
            else:
                # Save everything to post-code
                post_code += token

        if depth != 0:
            raise ValueError("Unclosed list detected")

        split_code = self.SplitCode(pre_code, post_code, items)
        self._cache[frame_code] = split_code
        return split_code


class EnumerateToTable(ListToTable):
    def __init__(self):
        super().__init__(tokens.ENUMERATE_BEGIN, tokens.ENUMERATE_END)


class ItemizeToTable(ListToTable):
    def __init__(self):
        super().__init__(tokens.ITEMIZE_BEGIN, tokens.ITEMIZE_END)
