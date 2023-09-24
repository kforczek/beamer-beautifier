from gui.pdf_viewer import run_viewer
from beamer.document import BeamerDocument


def run_example() -> None:
    #document = BeamerDocument("/home/kuba/Documents/beamer-beautifier/examples/overleaf-template/main.tex") # TODO change
    document = BeamerDocument("/home/kuba/Documents/beamer-beautifier/examples/simple/main.tex") # TODO change
    run_viewer(document)


if __name__ == '__main__':
    run_example()