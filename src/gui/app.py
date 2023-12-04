import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from src.gui.widgets import MainSplitter
from src.beamer.document import BeamerDocument
from src.beamer.page_info import PageInfo


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
        self._local_thumbnails_view = splitter.right_pane.top_thumbs_view
        self._global_thumbnails_view = splitter.right_pane.bottom_thumbs_view

        splitter.left_pane.navigation_buttons.prev_button.clicked.connect(self._prev_page)
        splitter.left_pane.navigation_buttons.next_button.clicked.connect(self._next_page)
        self._improve_button.clicked.connect(self._select_improvement)
        self._local_thumbnails_view.itemSelectionChanged.connect(self._local_thumbnail_selection_changed)
        # TODO connect thumbs bottom
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
        self._load_specific_thumbnails(self._local_thumbnails_view, self._curr_local_improvements)
        self._load_specific_thumbnails(self._global_thumbnails_view, self._curr_global_improvements)

    def _load_specific_thumbnails(self, dest_listview, thumbnails_list):
        self._thumbs.clear()
        while dest_listview.count() > 0:
            dest_listview.takeItem(0)

        for idx, opt in enumerate(thumbnails_list):
            pixmap = opt.scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            item = QtWidgets.QListWidgetItem()
            item.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(QtGui.QImage(pixmap.toImage()))))

            dest_listview.addItem(item)
            self._thumbs.append(item)

            if idx == self._selected_opt:
                dest_listview.setCurrentItem(item)
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

    def _load_page(self, page_info: PageInfo):
        self._curr_local_improvements = [to_qt_pixmap(page_opt) for page_opt in page_info.local_improvements]
        self._curr_global_improvements = [to_qt_pixmap(page_opt) for page_opt in page_info.global_improvements]
        self._selected_opt = self._document.current_frame_alternative()
        self._display_page()
        self._load_thumbnails()

    def _display_page(self):
        option = self._highlighted_opt if self._highlighted_opt is not None else self._selected_opt
        current_width = self._image_display.width()
        current_height = self._image_display.height()
        pixmap = self._curr_local_improvements[option].scaled(
            current_width, current_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self._image_display.setPixmap(pixmap)

    def _local_thumbnail_selection_changed(self):
        curr_item = self._local_thumbnails_view.currentItem()

        try:
            self._highlighted_opt = self._thumbs.index(curr_item) if curr_item else None
        except ValueError:
            self._highlighted_opt = None

        if self._highlighted_opt in (None, self._selected_opt):
            if len(self._thumbs) > self._selected_opt:
                self._local_thumbnails_view.setCurrentItem(self._thumbs[self._selected_opt])
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
