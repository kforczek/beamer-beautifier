FRAME_BEGIN = "\\begin{frame}"
FRAME_END = "\\end{frame}"
FRAME_ALT_DECL = "\\frame"  #TODO accept these
DOC_BEGIN = "\\begin{document}"
DOC_END = "\\end{document}"

ITEMIZE_BEGIN = "\\begin{itemize}"
ITEMIZE_END = "\\end{itemize}"
ENUMERATE_BEGIN = "\\begin{enumerate}"
ENUMERATE_END = "\\end{enumerate}"


def hspace(size_cm: int) -> str:
    return f"\\hspace{{{size_cm}cm}}"

def items_indent(size_cm: int) ->str:
    return f"\\addtolength{{\\itemindent}}{{{size_cm}cm}}"
