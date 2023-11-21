from gui.app import run_app
from beamer.document import BeamerDocument
from examples.selector import select_example


def run_example() -> None:
    doc_path = select_example()
    document = BeamerDocument(doc_path)
    run_app(document)


if __name__ == '__main__':
    run_example()
