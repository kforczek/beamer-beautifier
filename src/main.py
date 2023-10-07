import os
from gui.pdf_viewer import run_viewer
from beamer.document import BeamerDocument
from examples.selector import select_example

def run_example() -> None:
    doc_path = select_example()
    document = BeamerDocument(doc_path)
    run_viewer(document)


if __name__ == '__main__':
    run_example()
