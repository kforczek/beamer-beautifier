import os.path
import sys

from PyQt5 import QtWidgets

from gui.app import run_app
from gui.selector import get_user_document_path
from beamer.document.document import BeamerDocument
from examples.selector import select_example


def main():
    example_switches = ('-e', '--example')
    app = QtWidgets.QApplication(sys.argv)

    if len(sys.argv) > 0 and any([switch in sys.argv for switch in example_switches]):
        doc_path = select_example()

    else:
        doc_path = get_user_document_path()[0]

    if not doc_path:
        return

    document = BeamerDocument(doc_path)
    run_app(app, document, os.path.dirname(doc_path))


if __name__ == '__main__':
    main()
