import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from .widgets import MainSplitter, ThumbnailsListView
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
        self.setGeometry(100, 100, 1500, 870)
        self.setWindowTitle('Beamer Beautifier')

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        splitter = MainSplitter(self)
        layout.addWidget(splitter)

        self._image_display = splitter.left_pane.image_display
        # self._improve_button = splitter.left_pane.function_buttons.improve_button
        self._save_button = splitter.left_pane.function_buttons.save_button
        self._frame_thumbs_view = splitter.right_pane.frame_tab.thumbs_view
        self._background_thumbs_view = splitter.right_pane.background_tab.thumbs_view
        self._global_thumbs_view = splitter.right_pane.global_tab.thumbs_view

        splitter.left_pane.navigation_buttons.prev_button.clicked.connect(self._prev_page)
        splitter.left_pane.navigation_buttons.next_button.clicked.connect(self._next_page)
        # self._improve_button.clicked.connect(self._select_improvement)
        self._frame_thumbs_view.itemSelectionChanged.connect(self._local_thumbnail_selection_changed)
        self._background_thumbs_view.itemSelectionChanged.connect(self._background_thumbnail_selection_changed)
        self._global_thumbs_view.itemSelectionChanged.connect(self._global_thumbnail_selection_changed)
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
        self._global_highlighted_opt = None
        self._changes_count = 0
        self._local_thumb_items = []
        self._background_thumb_items = []
        self._global_thumb_items = []
        self._load_page(page)

    def _load_thumbnails(self):
        self._load_specific_thumbnails(self._frame_thumbs_view, self._local_thumb_items)
        self._load_specific_thumbnails(self._background_thumbs_view, self._background_thumb_items)
        self._load_specific_thumbnails(self._global_thumbs_view, self._global_thumb_items)

    def _load_specific_thumbnails(self, dest_listview, thumbnail_items):
        dest_listview.clear()

        for idx, item in enumerate(thumbnail_items):
            dest_listview.addItem(item)

            if idx == self._selected_local_opt:
                dest_listview.setCurrentItem(item)
                self._local_highlighted_opt = self._selected_local_opt

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

        self._selected_local_opt = self._document.current_frame_alternative()
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

        if highlighted_idx in (None, curr_selected_opt):
            if len(thumb_items) > curr_selected_opt:
                thumbs_view.setCurrentItem(thumb_items[curr_selected_opt])
                highlighted_opt = curr_selected_opt
                self._handle_thumb_highlight(improvements_list, highlighted_opt)
            return highlighted_idx

        # Another option has been highlighted
        self._handle_thumb_highlight(improvements_list, highlighted_idx)
        return highlighted_idx

    def _handle_thumb_highlight(self, improvements_list, highlighted_idx):
        # self._improve_button.setEnabled(self._local_highlighted_opt != self._selected_local_opt)  # TODO button fix (2 buttons?)
        self._display_page(improvements_list[highlighted_idx])

    def _select_improvement(self):
        if self._local_highlighted_opt == self._selected_local_opt:
            return

        self._selected_local_opt = self._local_highlighted_opt
        self._document.select_alternative(self._selected_local_opt)
        self._update_save_button_state(self._selected_local_opt)
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


def to_thumbnail_item(qt_pixmap):
    pixmap = qt_pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    item = QtWidgets.QListWidgetItem()
    item.setIcon(QtGui.QIcon(pixmap))
    return item


def run_app(document: BeamerDocument, doc_folder: str):
    app = QtWidgets.QApplication(sys.argv)
    viewer = MainWindow(document, doc_folder)
    viewer.show()
    sys.exit(app.exec_())
