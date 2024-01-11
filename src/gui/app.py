import sys

from threading import Lock
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication

from .widgets import MainSplitter, ThumbnailsListView, GoToDialog
from src.beamer.document import BeamerDocument
from src.beamer.page_getter import PageGetter


class EmptyDocumentError(ValueError):
    pass


class MainWindow(QtWidgets.QFrame):
    def __init__(self, document: BeamerDocument, doc_folder_path: str, parent=None):
        super().__init__(parent)

        self._init_ui(document)
        self._init_document_logic(document)
        self._doc_folder_path = doc_folder_path

    def _init_ui(self, document: BeamerDocument):
        self.resize(1500, 920)
        self.setWindowTitle('Beamer Beautifier')

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self._splitter = MainSplitter(self, document)
        layout.addWidget(self._splitter)

        self._image_display = self._splitter.left_pane.image_display
        self._info_layout = self._splitter.left_pane.save_info_layout.info_layout
        self._save_button = self._splitter.left_pane.save_info_layout.save_button
        self._frame_thumbs_view = self._splitter.right_pane.frame_tab.thumbs_view
        self._background_thumbs_view = self._splitter.right_pane.background_tab.thumbs_view
        self._global_thumbs_view = self._splitter.right_pane.global_tab.thumbs_view
        self._goto_dialog = None

        self._splitter.right_pane.background_tab.function_buttons.regenerate_button.clicked.connect(self._regenerate_backgrounds_click)
        self._splitter.left_pane.navigation_buttons.prev_button.clicked.connect(self._prev_page)
        self._splitter.left_pane.navigation_buttons.next_button.clicked.connect(self._next_page)
        self._splitter.left_pane.save_info_layout.info_layout.goto_button.clicked.connect(self._goto_button_click)
        self._frame_thumbs_view.itemClicked.connect(lambda _: self._local_thumbnail_selection_changed())
        self._background_thumbs_view.itemClicked.connect(lambda _: self._background_thumbnail_selection_changed())
        self._global_thumbs_view.itemClicked.connect(lambda _: self._global_thumbnail_selection_changed())
        self._save_button.clicked.connect(self._save_changes)

    def _init_document_logic(self, document: BeamerDocument):
        self._document = document

        self._selected_local_opt = 0
        self._selected_background_opt = 0
        self._selected_global_opt = 0

        self._curr_local_improvements = []
        self._curr_background_improvements = []
        self._curr_global_improvements = []

        self._local_highlighted_opt = None
        self._background_highlighted_opt = None
        self._global_highlighted_opt = None

        self._page_getter_lock = Lock()
        self._current_page_getter = None
        self._original_page = None

        self._local_fillers_count = 0
        self._background_fillers_count = 0
        self._global_fillers_count = 0

        self._next_page()
        if not self._original_page:
            raise EmptyDocumentError("The document doesn't contain any pages, got nothing to display")

    def _check_caller(self, caller: PageGetter):
        """Checks whether the calling PageGetter is still allowed to send updates (if not, it means that the
        page has been changed and updates from any old PageGetters are irrelevant)."""
        with self._page_getter_lock:
            return caller is self._current_page_getter

    def _add_local_version(self, pixmap, caller: PageGetter):
        if not self._check_caller(caller):
            return

        self._local_fillers_count = self._add_version(
            pixmap, self._curr_local_improvements, self._frame_thumbs_view, self._local_fillers_count)
        self._highlight_local_thumbnail()

    def _add_background_version(self, pixmap, caller: PageGetter):
        if not self._check_caller(caller):
            return

        self._background_fillers_count = self._add_version(
            pixmap, self._curr_background_improvements, self._background_thumbs_view, self._background_fillers_count)
        self._highlight_background_thumbnail()

    def _add_global_version(self, pixmap, caller: PageGetter):
        if not self._check_caller(caller):
            return

        self._global_fillers_count = self._add_version(
            pixmap, self._curr_global_improvements, self._global_thumbs_view, self._global_fillers_count)
        self._highlight_global_thumbnail()

    def _add_version(self, pixmap, improvements_list, thumbs_view, fillers_counter) -> int:
        """Adds version and returns the updated fillers counter."""
        qt_pixmap = to_qt_pixmap(pixmap)
        item = to_thumbnail_item(qt_pixmap)
        if fillers_counter > 0:
            improvements_list[-fillers_counter] = qt_pixmap
            thumbs_view.replaceItem(-fillers_counter, item)
            fillers_counter -= 1
        else:
            improvements_list.append(qt_pixmap)
            thumbs_view.addItem(item)

        self._display_page()
        return fillers_counter

    def _highlight_local_thumbnail(self):
        item_to_highlight = self._frame_thumbs_view.items()[self._selected_local_opt]
        self._frame_thumbs_view.setCurrentItem(item_to_highlight)
        self._local_highlighted_opt = self._selected_local_opt

    def _highlight_background_thumbnail(self):
        item_to_highlight = self._background_thumbs_view.items()[self._selected_background_opt]
        self._background_thumbs_view.setCurrentItem(item_to_highlight)
        self._background_highlighted_opt = self._selected_background_opt

    def _highlight_global_thumbnail(self):
        item_to_highlight = self._global_thumbs_view.items()[self._selected_global_opt]
        self._global_thumbs_view.setCurrentItem(item_to_highlight)
        self._global_highlighted_opt = self._selected_global_opt

    def _prev_page(self):
        self._prepare_page_getter()
        original_page = self._document.prev_page(self._current_page_getter)
        if not original_page:
            return

        self._prepare_page_load()
        self._load_original_page(original_page)
        self._info_layout.prev_page()

    def _next_page(self):
        self._prepare_page_getter()
        original_page = self._document.next_page(self._current_page_getter)
        if not original_page:
            return

        self._prepare_page_load()
        self._load_original_page(original_page)
        self._info_layout.next_page()

    def _goto_page(self, page_idx):
        self._prepare_page_getter()
        original_page = self._document.goto_page(page_idx, self._current_page_getter)
        if not original_page:
            return

        self._prepare_page_load()
        self._load_original_page(original_page)
        self._info_layout.update()

    def _goto_frame(self, frame_idx):
        self._prepare_page_getter()
        original_page = self._document.goto_frame(frame_idx, self._current_page_getter)
        if not original_page:
            return

        self._prepare_page_load()
        self._load_original_page(original_page)
        self._info_layout.update()

    def _regenerate_backgrounds_click(self):
        if not self._current_page_getter:
            self._prepare_page_getter()

        self._curr_background_improvements = [self._original_page]
        self._background_thumbs_view.clear()
        self._background_thumbs_view.addItem(to_thumbnail_item(self._original_page))
        self._background_fillers_count = self._create_fillers(
            self._document.current_background_improvements().selected_index(),
            self._curr_background_improvements,
            self._background_thumbs_view)

        self._document.regenerate_background_improvements(self._current_page_getter)

    def _prepare_page_getter(self):
        with self._page_getter_lock:
            if self._current_page_getter:
                self._current_page_getter.cancel()

            self._current_page_getter = PageGetter(self._add_local_version, self._add_background_version,
                                                   self._add_global_version)

    def _prepare_page_load(self):
        self._curr_local_improvements.clear()
        self._curr_background_improvements.clear()
        self._curr_global_improvements.clear()

        self._frame_thumbs_view.clear()
        self._background_thumbs_view.clear()
        self._global_thumbs_view.clear()

        self._local_fillers_count = 0
        self._background_fillers_count = 0
        self._global_fillers_count = 0

    def _load_original_page(self, pixmap):
        self._original_page = to_qt_pixmap(pixmap)

        self._curr_local_improvements = [self._original_page]
        self._curr_background_improvements = [self._original_page]
        self._curr_global_improvements = [self._original_page]

        self._frame_thumbs_view.addItem(to_thumbnail_item(self._original_page))
        self._background_thumbs_view.addItem(to_thumbnail_item(self._original_page))
        self._global_thumbs_view.addItem(to_thumbnail_item(self._original_page))

        self._selected_local_opt = self._document.current_local_improvements().selected_index()
        self._selected_background_opt = self._document.current_background_improvements().selected_index()
        self._selected_global_opt = self._document.current_global_improvements().selected_index()

        self._local_fillers_count = self._create_fillers(
            self._selected_local_opt, self._curr_local_improvements, self._frame_thumbs_view)

        self._background_fillers_count = self._create_fillers(
            self._selected_background_opt, self._curr_background_improvements, self._background_thumbs_view)

        self._global_fillers_count = self._create_fillers(
            self._selected_global_opt, self._curr_global_improvements, self._global_thumbs_view)

        self._display_page()
        self._highlight_local_thumbnail()
        self._highlight_background_thumbnail()
        self._highlight_global_thumbnail()

    def _create_fillers(self, count: int, improvements_list, thumbs_view):
        """Creates filler improvements. Returns a number of how many were created."""
        for _ in range(count):
            filler_pixmap = self._original_page.copy()
            filler_pixmap.fill(QtGui.QColor(200, 200, 200))
            improvements_list.append(filler_pixmap)
            thumbs_view.addItem(to_thumbnail_item(filler_pixmap))
        return count

    def _display_page(self, image_to_display=None):
        if image_to_display is None:
            image_to_display = self._original_page
        current_width = self._image_display.width()
        current_height = self._image_display.height()
        pixmap = image_to_display.scaled(
            current_width, current_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self._image_display.setPixmap(pixmap)

    def _local_thumbnail_selection_changed(self):
        self._local_highlighted_opt = self._thumbnail_selection_changed(
            self._curr_local_improvements,
            self._frame_thumbs_view,
            self._selected_local_opt)

    def _background_thumbnail_selection_changed(self):
        self._background_highlighted_opt = self._thumbnail_selection_changed(
            self._curr_background_improvements,
            self._background_thumbs_view,
            self._selected_background_opt)

    def _global_thumbnail_selection_changed(self):
        self._global_highlighted_opt = self._thumbnail_selection_changed(
            self._curr_global_improvements,
            self._global_thumbs_view,
            self._selected_global_opt)

    def _thumbnail_selection_changed(self, improvements_list, thumbs_view: ThumbnailsListView, curr_selected_opt: int) -> int:
        """
        Handles changes in highlighting of the thumbnails.
        :return: Index of the highlighted thumbnail.
        """
        highlighted_idx = thumbs_view.selectedIndex()
        thumb_items = thumbs_view.items()

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

    def _goto_button_click(self):
        if self._goto_dialog:
            return

        self._goto_dialog = GoToDialog(self, self._document)
        self._goto_dialog.show()
        self._goto_dialog.ok_button.clicked.connect(self._goto_dialog_accepted)
        self._goto_dialog.canceled.connect(self._goto_dialog_canceled)

    def _goto_dialog_accepted(self):
        self._goto_dialog.canceled.disconnect()
        self._goto_dialog.close()

        selected_idx = self._goto_dialog.number.value() - 1
        if self._goto_dialog.page_option.isChecked():
            self._goto_page(selected_idx)
        else:
            self._goto_frame(selected_idx)

        self._goto_dialog.destroy()
        self._goto_dialog = None

    def _goto_dialog_canceled(self):
        self._goto_dialog.destroy()
        self._goto_dialog = None

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
