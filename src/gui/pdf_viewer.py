import sys

import fitz
from PyQt5 import QtCore, QtGui, QtWidgets
from src.beamer.document import BeamerDocument


class PDFViewer(QtWidgets.QWidget):
    def __init__(self, document: BeamerDocument):
        super(PDFViewer, self).__init__(None)

        self.current_page = 0
        self._document = document

        path = self._document.compile()
        self._pdf_file = fitz.open(path)

        self.init_ui()

    def init_ui(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('PDF Viewer')

        self.pdf_label = QtWidgets.QLabel(self)
        self.pdf_label.setGeometry(0, 0, 400, 600)
        self.pdf_label.setAlignment(QtCore.Qt.AlignCenter)

        self.pdf_list = QtWidgets.QListWidget(self)
        self.pdf_list.setGeometry(400, 0, 400, 600)
        self.pdf_list.setViewMode(QtWidgets.QListWidget.IconMode)
        self.pdf_list.setIconSize(QtCore.QSize(200, 200))
        self.pdf_list.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.pdf_list.setMovement(QtWidgets.QListWidget.Static)

        self.load_page()

    def load_page(self):
        self.pdf_label.setPixmap(self.load_pixmap(self.current_page).scaled(400, 600, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

        for page in range(self._pdf_file.page_count):
            pixmap = self.load_pixmap(page).scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            item = QtWidgets.QListWidgetItem()
            item.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(QtGui.QImage(pixmap.toImage()))))
            self.pdf_list.addItem(item)

    def load_pixmap(self, page):
        pix = self._pdf_file.load_page(page).get_pixmap(alpha=True)
        img = QtGui.QImage(pix.samples, pix.width, pix.height, pix.width * pix.n, QtGui.QImage.Format_RGBA8888)
        return QtGui.QPixmap.fromImage(img)


def run_viewer(document: BeamerDocument) -> None:
    app = QtWidgets.QApplication(sys.argv)
    viewer = PDFViewer(document)
    viewer.show()
    sys.exit(app.exec_())
