import sys
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication

from .widgets import MainSplitter, ThumbnailsListView
from src.beamer.document.document import BeamerDocument
from src.beamer.page_info import PageInfo


class EmptyDocumentError(ValueError):
    pass


class MainWindow(QtWidgets.QFrame):
    def __init__(self, document: BeamerDocument, doc_folder_path: str, parent=None):
        super().__init__(parent)

        self._init_ui(document)
        self._init_document_logic(document)
        self._doc_folder_path = doc_folder_path

    def _init_ui(self, document: BeamerDocument):
        self.resize(1500, 870)
        self.setWindowTitle('Beamer Beautifier')

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self._splitter = MainSplitter(self, document)
        layout.addWidget(self._splitter)

        self._image_display = self._splitter.left_pane.image_display
        self._save_button = self._splitter.left_pane.function_buttons.save_button
        self._frame_thumbs_view = self._splitter.right_pane.frame_tab.thumbs_view
        self._background_thumbs_view = self._splitter.right_pane.background_tab.thumbs_view
        self._global_thumbs_view = self._splitter.right_pane.global_tab.thumbs_view

        self._splitter.left_pane.navigation_buttons.prev_button.clicked.connect(self._prev_page)
        self._splitter.left_pane.navigation_buttons.next_button.clicked.connect(self._next_page)
        self._frame_thumbs_view.itemClicked.connect(lambda _: self._local_thumbnail_selection_changed())
        self._background_thumbs_view.itemClicked.connect(lambda _: self._background_thumbnail_selection_changed())
        self._global_thumbs_view.itemClicked.connect(lambda _: self._global_thumbnail_selection_changed())
        self._save_button.clicked.connect(self._save_changes)

    def _init_document_logic(self, document: BeamerDocument):
        self._document = document
        page = self._document.next_page()
        if not page:
            raise EmptyDocumentError("The document doesn't contain any pages, got nothing to display")

        self._selected_local_opt = 0
        self._selected_background_opt = 0
        self._selected_global_opt = 0
        self._local_highlighted_opt = None
        self._background_highlighted_opt = None
        self._global_highlighted_opt = None
        self._local_thumb_items = []
        self._background_thumb_items = []
        self._global_thumb_items = []
        self._load_page(page)

    def _load_thumbnails(self):
        self._load_specific_thumbnails(self._frame_thumbs_view, self._local_thumb_items)
        self._load_specific_thumbnails(self._background_thumbs_view, self._background_thumb_items)
        self._load_specific_thumbnails(self._global_thumbs_view, self._global_thumb_items)

        self._highlight_local_thumbnail()
        self._highlight_background_thumbnail()
        self._highlight_global_thumbnail()

    def _load_specific_thumbnails(self, dest_listview, thumbnail_items):
        dest_listview.clear()

        for idx, item in enumerate(thumbnail_items):
            dest_listview.addItem(item)

    def _highlight_local_thumbnail(self):
        item_to_highlight = self._local_thumb_items[self._selected_local_opt]
        self._frame_thumbs_view.setCurrentItem(item_to_highlight)
        self._local_highlighted_opt = self._selected_local_opt

    def _highlight_background_thumbnail(self):
        item_to_highlight = self._background_thumb_items[self._selected_background_opt]
        self._background_thumbs_view.setCurrentItem(item_to_highlight)
        self._background_highlighted_opt = self._selected_background_opt

    def _highlight_global_thumbnail(self):
        item_to_highlight = self._global_thumb_items[self._selected_global_opt]
        self._global_thumbs_view.setCurrentItem(item_to_highlight)
        self._global_highlighted_opt = self._selected_global_opt

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
        self._local_thumb_items.clear()
        self._background_thumb_items.clear()
        self._global_thumb_items.clear()

        self._original_page = to_qt_pixmap(page_info.original_page)
        self._curr_local_improvements = [self._original_page]
        self._curr_background_improvements = [self._original_page]
        self._curr_global_improvements = [self._original_page]

        self._curr_local_improvements.extend([to_qt_pixmap(page_opt) for page_opt in page_info.frame_improvements])
        self._local_thumb_items = [to_thumbnail_item(improvement) for improvement in self._curr_local_improvements]

        self._curr_background_improvements.extend([to_qt_pixmap(page_opt) for page_opt in page_info.background_improvements])
        self._background_thumb_items = [to_thumbnail_item(improvement) for improvement in self._curr_background_improvements]

        self._curr_global_improvements.extend([to_qt_pixmap(page_opt) for page_opt in page_info.global_improvements])
        self._global_thumb_items = [to_thumbnail_item(improvement) for improvement in self._curr_global_improvements]

        self._selected_local_opt = self._document.current_local_improvements().selected_index()
        self._selected_background_opt = self._document.current_background_improvements().selected_index()
        self._selected_global_opt = self._document.current_global_improvements().selected_index()

        self._display_page()
        self._load_thumbnails()

    def _display_page(self, image_to_display=None):
        if image_to_display is None:
            image_to_display = self._original_page
        #option = self._local_highlighted_opt if self._local_highlighted_opt is not None else self._selected_opt
        current_width = self._image_display.width()
        current_height = self._image_display.height()
        #pixmap = self._curr_local_improvements[option].scaled(
        pixmap = image_to_display.scaled(
            current_width, current_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self._image_display.setPixmap(pixmap)

    def _local_thumbnail_selection_changed(self):
        self._local_highlighted_opt = self._thumbnail_selection_changed(
            self._curr_local_improvements,
            self._frame_thumbs_view,
            self._local_thumb_items,
            self._selected_local_opt)

    def _background_thumbnail_selection_changed(self):
        self._background_highlighted_opt = self._thumbnail_selection_changed(
            self._curr_background_improvements,
            self._background_thumbs_view,
            self._background_thumb_items,
            self._selected_background_opt)

    def _global_thumbnail_selection_changed(self):
        self._global_highlighted_opt = self._thumbnail_selection_changed(
            self._curr_global_improvements,
            self._global_thumbs_view,
            self._global_thumb_items,
            self._selected_global_opt)

    def _thumbnail_selection_changed(self, improvements_list, thumbs_view: ThumbnailsListView, thumb_items, curr_selected_opt: int) -> int:
        """
        Handles changes in highlighting of the thumbnails.
        :return: Index of the highlighted thumbnail.
        """
        highlighted_idx = thumbs_view.selectedIndex()

        if highlighted_idx in (None, curr_selected_opt) and len(thumb_items) > curr_selected_opt:
            thumbs_view.setCurrentItem(thumb_items[curr_selected_opt])
            highlighted_idx = curr_selected_opt

        self._handle_thumb_highlight(improvements_list, highlighted_idx)
        return highlighted_idx

    def _handle_thumb_highlight(self, improvements_list, highlighted_idx):
        self._display_page(improvements_list[highlighted_idx])

    def _save_changes(self):
        path = QtWidgets.QFileDialog.getSaveFileName(self, caption='Save modified presentation',
                                                     directory=self._doc_folder_path)[0]
        if not path:
            return
        self._document.save(path)
        self._splitter.notify_saved()

    def _update_save_button_state(self, new_selected_opt: int):
        changes_count = self._selected_local_opt + self._selected_background_opt + self._selected_global_opt
        self._save_button.setEnabled(changes_count > 0)

    def resizeEvent(self, event):
        self._display_page()
        super(MainWindow, self).resizeEvent(event)

    def showEvent(self, event):
        self._display_page()
        super(MainWindow, self).showEvent(event)

    def closeEvent(self, a0: QtGui.QCloseEvent):
        if not self._splitter.any_change_done():
            a0.accept()
            return

        message_title = "Discard changes?"
        message_content = "You have made changes to the loaded presentation. " \
                          "Are you sure you want to exit without saving the results?"
        selection = QtWidgets.QMessageBox.question(self, message_title, message_content,
                                                   QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                                                   QtWidgets.QMessageBox.Cancel)
        if selection == QtWidgets.QMessageBox.Ok:
            a0.accept()
        else:
            a0.ignore()


def to_qt_pixmap(fitz_pixmap):
    img = QtGui.QImage(fitz_pixmap.samples, fitz_pixmap.width, fitz_pixmap.height,
                       fitz_pixmap.width * fitz_pixmap.n, QtGui.QImage.Format_RGBA8888)
    return QtGui.QPixmap.fromImage(img)


def to_thumbnail_item(qt_pixmap):
    pixmap = qt_pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    item = QtWidgets.QListWidgetItem()
    item.setIcon(QtGui.QIcon(pixmap))
    return item


def run_app(app: QApplication, document: BeamerDocument, doc_folder: str):
    viewer = MainWindow(document, doc_folder)
    viewer.show()
    sys.exit(app.exec_())
