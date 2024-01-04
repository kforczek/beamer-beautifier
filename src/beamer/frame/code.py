import src.beamer.tokens as tokens


class FrameCode:
    """A representation of LaTeX code of a single frame, divided into sections."""
    def __init__(self, header="", base_code="", global_color_defs="", bg_img_def=""):
        """
        :param header: Header of the document which originally contained the frame - code containing package includes,
        command definitions and all things that go before "\begin{document}" statement.
        :param base_code: Code that goes between \begin{frame} and \end{frame}.
        :param global_color_defs: Global definitions of the color palette (they will be placed right after the header).
        :param bg_img_def: A definition of the frame-local background image (will be inserted before the
        frame definition).
        """
        self.header = header
        self.base_code = base_code
        self.global_color_defs = global_color_defs
        self.bg_img_def = bg_img_def

    def as_str(self) -> str:
        """
        :return: A full, compilable document, containing only this one frame.
        """
        code = self.header + "\n"

        if self.global_color_defs:
            code += self.global_color_defs + "\n"

        code += tokens.DOC_BEGIN + "\n"

        if self.bg_img_def:
            code += "{\n"
            code += self.bg_img_def + "\n"

        code += self.base_code + "\n"

        if self.bg_img_def:
            code += "}\n"

        code += tokens.DOC_END + "\n"

        return code
