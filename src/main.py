import os
from gui.pdf_viewer import run_viewer
from beamer.document import BeamerDocument


def run_example() -> None:
    base_path = os.path.dirname(os.getcwd())
    ex_file = os.path.join(base_path, "examples/simple/main.tex")
    document = BeamerDocument(ex_file)
    run_viewer(document)


if __name__ == '__main__':
    run_example()
