import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from src.gui.widgets import MainSplitter
from src.beamer.document import BeamerDocument


class EmptyDocumentError(ValueError):
    pass


class MainWindow(QtWidgets.QFrame):
    def __init__(self, document: BeamerDocument, doc_folder_path: str, parent=None):
        super().__init__(parent)

        self._init_ui()
        self._init_document_logic(document)
        self._doc_folder_path = doc_folder_path

    def _init_ui(self):
        self.setGeometry(100, 100, 1480, 870)
        self.setWindowTitle('Beamer Beautifier')

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        splitter = MainSplitter(self)
        layout.addWidget(splitter)

        self._image_display = splitter.left_pane.image_display
        self._improve_button = splitter.left_pane.function_buttons.improve_button
        self._save_button = splitter.left_pane.function_buttons.save_button
        self._thumbnails_view = splitter.right_pane.top_thumbs_view

        splitter.left_pane.navigation_buttons.prev_button.clicked.connect(self._prev_page)
        splitter.left_pane.navigation_buttons.next_button.clicked.connect(self._next_page)
        self._improve_button.clicked.connect(self._select_improvement)
        self._thumbnails_view.itemSelectionChanged.connect(self._thumbnail_selection_changed)
        self._save_button.clicked.connect(self._save_changes)

    def _init_document_logic(self, document: BeamerDocument):
        self._document = document
        page = self._document.next_page()
        if not page:
            raise EmptyDocumentError("The document doesn't contain any pages, got nothing to display")

        self._highlighted_opt = None
        self._changes_count = 0
        self._thumbs = []
        self._load_page(page)

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

        self._load_page(page)

    def _next_page(self):
        page = self._document.next_page()
        if not page:
            return

        self._load_page(page)

    def _load_page(self, page_pixmaps):
        self._current_page = [to_qt_pixmap(page_opt) for page_opt in page_pixmaps]
        self._selected_opt = self._document.current_frame_alternative()
        self._display_page()
        self._load_thumbnails()

    def _display_page(self):
        option = self._highlighted_opt if self._highlighted_opt is not None else self._selected_opt
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

        if self._highlighted_opt in (None, self._selected_opt):
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

        self._selected_opt = self._highlighted_opt
        self._document.select_alternative(self._selected_opt)
        self._update_save_button_state(self._selected_opt)
        self._handle_thumb_highlight()

    def _save_changes(self):
        path = QtWidgets.QFileDialog.getSaveFileName(self, caption='Save modified presentation', directory=self._doc_folder_path)[0]
        if not path:
            return
        self._document.save(path)

    def _update_save_button_state(self, new_selected_opt: int):
        self._changes_count += 1 if new_selected_opt > 0 else -1
        self._save_button.setEnabled(self._changes_count > 0)

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


def run_app(document: BeamerDocument, doc_folder: str):
    app = QtWidgets.QApplication(sys.argv)
    viewer = MainWindow(document, doc_folder)
    viewer.show()
    sys.exit(app.exec_())
