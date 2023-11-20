import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from src.beamer.document import BeamerDocument


class EmptyDocumentError(ValueError):
    pass


class PDFViewer(QtWidgets.QWidget):
    def __init__(self, document: BeamerDocument, parent=None):
        super(PDFViewer, self).__init__(parent)

        self._document = document

        page = self._document.next_page()
        if not page:
            raise EmptyDocumentError("The document doesn't contain any page, got nothing to display")

        self._current_page = [to_qt_pixmap(page_opt) for page_opt in page]
        self._selected_opt = 0
        self._init_ui()

    def _init_ui(self):
        self.setGeometry(100, 100, 1160, 700)
        self.setWindowTitle('Beamer Beautifier')

        self._pdf_label = QtWidgets.QLabel(self)
        self._pdf_label.setAlignment(QtCore.Qt.AlignCenter)

        self._thumbs_list = QtWidgets.QListWidget(self)
        self._thumbs_list.setViewMode(QtWidgets.QListWidget.IconMode)
        self._thumbs_list.setIconSize(QtCore.QSize(460, 300))
        self._thumbs_list.setResizeMode(QtWidgets.QListWidget.Adjust)
        self._thumbs_list.setMovement(QtWidgets.QListWidget.Static)

        pdf_label_container = QtWidgets.QWidget()
        pdf_label_layout = QtWidgets.QVBoxLayout()

        # Navigation buttons
        self._prev_button = QtWidgets.QPushButton("←")
        self._prev_button.clicked.connect(self._previous_page)
        self._prev_button.setFixedSize(50, 50)
        self._next_button = QtWidgets.QPushButton("→")
        self._next_button.clicked.connect(self._next_page)
        self._next_button.setFixedSize(50, 50)

        self._improve_button = QtWidgets.QPushButton("Select this version")
        self._improve_button.setEnabled(False)

        # Button layout with spacers
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self._prev_button)
        button_layout.addSpacing(20)  # Spacing between buttons
        button_layout.addWidget(self._next_button)
        button_layout.addStretch(1)

        pdf_display_layout = QtWidgets.QVBoxLayout()
        pdf_display_layout.addWidget(self._pdf_label)
        pdf_display_layout.addWidget(self._improve_button)
        pdf_display_layout.setAlignment(self._improve_button, QtCore.Qt.AlignRight)
        self._pdf_label.setMinimumWidth(250)

        pdf_label_layout.addLayout(pdf_display_layout)
        pdf_label_layout.addLayout(button_layout)
        pdf_label_container.setLayout(pdf_label_layout)

        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self._splitter.addWidget(pdf_label_container)
        self._splitter.addWidget(self._thumbs_list)
        self._splitter.setSizes([1040, 460])

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self._splitter)
        self.setLayout(layout)

        self._display_page()
        self._load_thumbnails()

    def _load_thumbnails(self):
        # TODO will be changed in future
        while self._thumbs_list.count() > 0:
            self._thumbs_list.takeItem(0)

        for idx, opt in enumerate(self._current_page):
            pixmap = opt.scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            item = QtWidgets.QListWidgetItem()
            item.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(QtGui.QImage(pixmap.toImage()))))
            if idx == self._selected_opt:
                item.setSelected(True)
            self._thumbs_list.addItem(item)

    def _previous_page(self):
        page = self._document.prev_page()
        if not page:
            return

        self._current_page = [to_qt_pixmap(page_opt) for page_opt in page]
        self._display_page()
        self._load_thumbnails()

    def _next_page(self):
        page = self._document.next_page()
        if not page:
            return

        self._current_page = [to_qt_pixmap(page_opt) for page_opt in page]
        self._display_page()
        self._load_thumbnails()

    def _display_page(self):
        current_width = self._pdf_label.width()
        current_height = self._pdf_label.height()
        pixmap = self._current_page[self._selected_opt].scaled(
            current_width, current_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self._pdf_label.setPixmap(pixmap)

    def resizeEvent(self, event):
        self._display_page()
        super(PDFViewer, self).resizeEvent(event)

    def showEvent(self, event):
        self._display_page()
        super(PDFViewer, self).showEvent(event)


def to_qt_pixmap(fitz_pixmap):
    img = QtGui.QImage(fitz_pixmap.samples, fitz_pixmap.width, fitz_pixmap.height,
                       fitz_pixmap.width * fitz_pixmap.n, QtGui.QImage.Format_RGBA8888)
    return QtGui.QPixmap.fromImage(img)


def run_viewer(document: BeamerDocument):
    app = QtWidgets.QApplication(sys.argv)
    viewer = PDFViewer(document)
    viewer.show()
    sys.exit(app.exec_())
