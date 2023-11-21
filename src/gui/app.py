import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from src.gui.widgets import MainSplitter
from src.beamer.document import BeamerDocument


class EmptyDocumentError(ValueError):
    pass


class MainWindow(QtWidgets.QFrame):
    def __init__(self, document: BeamerDocument, parent=None):
        super().__init__(parent)

        self._init_ui()
        self._init_document_logic(document)

        self._display_page()
        self._load_thumbnails()

    def _init_ui(self):
        self.setGeometry(100, 100, 1480, 870)
        self.setWindowTitle('Beamer Beautifier')

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        splitter = MainSplitter(self)
        layout.addWidget(splitter)

        self._image_display = splitter.image_display
        self._thumbnails_view = splitter.thumbnails_view
        self._improve_button = splitter.improve_button

        splitter.prev_button.clicked.connect(self._prev_page)
        splitter.next_button.clicked.connect(self._next_page)
        splitter.improve_button.clicked.connect(self._select_improvement)
        self._thumbnails_view.itemSelectionChanged.connect(self._thumbnail_selection_changed)

    def _init_document_logic(self, document: BeamerDocument):
        self._document = document
        page = self._document.next_page()
        if not page:
            raise EmptyDocumentError("The document doesn't contain any pages, got nothing to display")

        self._current_page = [to_qt_pixmap(page_opt) for page_opt in page]
        self._selected_opt = 0
        self._highlighted_opt = None
        self._thumbs = []

    def _load_thumbnails(self):
        self._thumbs.clear()
        while self._thumbnails_view.count() > 0:
            self._thumbnails_view.takeItem(0)

        for idx, opt in enumerate(self._current_page):
            pixmap = opt.scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            item = QtWidgets.QListWidgetItem()
            item.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(QtGui.QImage(pixmap.toImage()))))

            self._thumbnails_view.addItem(item)
            self._thumbs.append(item)

            if idx == self._selected_opt:
                self._thumbnails_view.setCurrentItem(item)
                self._highlighted_opt = self._selected_opt

    def _prev_page(self):
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
        option = self._highlighted_opt if self._highlighted_opt else self._selected_opt
        current_width = self._image_display.width()
        current_height = self._image_display.height()
        pixmap = self._current_page[option].scaled(
            current_width, current_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self._image_display.setPixmap(pixmap)

    def _thumbnail_selection_changed(self):
        curr_item = self._thumbnails_view.currentItem()

        try:
            self._highlighted_opt = self._thumbs.index(curr_item) if curr_item else None
        except ValueError:
            self._highlighted_opt = None

        if not self._highlighted_opt or self._highlighted_opt == self._selected_opt:
            if len(self._thumbs) > self._selected_opt:
                self._thumbnails_view.setCurrentItem(self._thumbs[self._selected_opt])
                self._highlighted_opt = self._selected_opt
                self._handle_thumb_highlight()
            return

        # Another option has been highlighted
        self._handle_thumb_highlight()

    def _handle_thumb_highlight(self):
        self._improve_button.setEnabled(self._highlighted_opt != self._selected_opt)
        self._display_page()

    def _select_improvement(self):
        if self._highlighted_opt == self._selected_opt:
            return

        self._document.select_alternative(self._selected_opt)
        self._selected_opt = self._highlighted_opt
        self._handle_thumb_highlight()

    def resizeEvent(self, event):
        self._display_page()
        super(MainWindow, self).resizeEvent(event)

    def showEvent(self, event):
        self._display_page()
        super(MainWindow, self).showEvent(event)


def to_qt_pixmap(fitz_pixmap):
    img = QtGui.QImage(fitz_pixmap.samples, fitz_pixmap.width, fitz_pixmap.height,
                       fitz_pixmap.width * fitz_pixmap.n, QtGui.QImage.Format_RGBA8888)
    return QtGui.QPixmap.fromImage(img)


def run_app(document: BeamerDocument):
    app = QtWidgets.QApplication(sys.argv)
    viewer = MainWindow(document)
    viewer.show()
    sys.exit(app.exec_())
