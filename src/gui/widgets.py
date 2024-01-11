from typing import Optional

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QListWidgetItem

from src.beamer.document import BeamerDocument


class MainSplitter(QtWidgets.QSplitter):
    def __init__(self, parent: QtWidgets.QWidget, document: BeamerDocument):
        super().__init__(QtCore.Qt.Orientation.Horizontal, parent)

        self._is_any_change = False

        self.left_pane = MainSplitterLeftPane(self, document)
        self.right_pane = MainSplitterRightPane(self, document)

        self.addWidget(self.left_pane)
        self.addWidget(self.right_pane)
        self.setSizes([970, 430])

    def any_change_done(self):
        return self._is_any_change

    def notify_change_done(self):
        """Receives the information about any improvement being selected."""
        self._is_any_change = True
        self.left_pane.save_info_layout.save_button.setEnabled(True)

    def notify_saved(self):
        self._is_any_change = False
        self.left_pane.save_info_layout.save_button.setEnabled(False)


class MainSplitterLeftPane(QtWidgets.QWidget):
    def __init__(self, parent: MainSplitter, document: BeamerDocument):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.image_display = ImageDisplay(self)
        self.save_info_layout = SaveAndInfoLayout(document)
        self.navigation_buttons = NavigationButtonsLayout()

        layout.addWidget(self.image_display)
        layout.addLayout(self.save_info_layout)
        layout.addLayout(self.navigation_buttons)


class MainSplitterRightPane(QtWidgets.QTabWidget):
    def __init__(self, parent: MainSplitter, document: BeamerDocument):
        super().__init__(parent)

        self.frame_tab = ImprovementsTab(self, parent, document.current_local_improvements)
        self.background_tab = ImprovementsTab(self, parent, document.current_background_improvements, True)
        self.global_tab = ImprovementsTab(self, parent, document.current_global_improvements)

        self.addTab(self.frame_tab, "Content alignment")
        self.addTab(self.background_tab, "Background")
        self.addTab(self.global_tab, "Colors (global)")


class NavigationButtonsLayout(QtWidgets.QHBoxLayout):
    def __init__(self):
        super().__init__()

        self.prev_button = NavigationButton("←")
        self.next_button = NavigationButton("→")

        self.addWidget(self.prev_button)
        self.addSpacing(20)
        self.addWidget(self.next_button)


class SaveAndInfoLayout(QtWidgets.QHBoxLayout):
    def __init__(self, document: BeamerDocument):
        super().__init__()

        self.save_button = QtWidgets.QPushButton("Save changes")
        self.save_button.setEnabled(False)
        self.info_layout = InfoLayout(document)

        self.addWidget(self.save_button)
        self.addLayout(self.info_layout)

        self.setAlignment(self.save_button, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setAlignment(self.info_layout, QtCore.Qt.AlignmentFlag.AlignRight)


class InfoLayout(QtWidgets.QVBoxLayout):
    def __init__(self, document: BeamerDocument):
        super().__init__()

        self.page_progress_label = QtWidgets.QLabel("")
        self.frame_progress_label = QtWidgets.QLabel("")
        self.goto_button = QtWidgets.QPushButton("Go to...")

        self.addWidget(self.page_progress_label)
        self.addWidget(self.frame_progress_label)
        self.addWidget(self.goto_button)

        self._document = document
        self._page_idx = 0
        self._frame_count = document.frame_count()
        self._page_count = document.page_count()

    def next_page(self):
        """Increases the displayed page counter. Updates the frame counter, if necessary."""
        self._page_idx += 1
        self.page_progress_label.setText(f"Page: {self._page_idx} of {self._page_count}")
        self._update_frame_counter()

    def prev_page(self):
        """Decreases the displayed page counter. Updates the frame counter, if necessary."""
        self._page_idx -= 1
        self.page_progress_label.setText(f"Page: {self._page_idx} of {self._page_count}")
        self._update_frame_counter()

    def update(self):
        """Auto-updates counters basing on document information."""
        self._page_idx = self._document.current_page_idx() + 1
        self.page_progress_label.setText(f"Page: {self._page_idx} of {self._page_count}")
        self._update_frame_counter()

    def _update_frame_counter(self):
        frame_number = self._document.current_frame_idx() + 1
        self.frame_progress_label.setText(f"Frame: {frame_number} of {self._frame_count}")


class ImprovementsTab(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget, main_splitter: MainSplitter,
                 improvements_getter, regenerate_button=False):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)
        self._improvements_getter = improvements_getter
        self._main_splitter = main_splitter

        self.thumbs_view = ThumbnailsListView(self)
        self.function_buttons = FunctionButtonsLayout(regenerate_button)

        self.function_buttons.choose_button.clicked.connect(self._choose_button_click)

        layout.addWidget(self.thumbs_view)
        layout.addLayout(self.function_buttons)

    def _choose_button_click(self):
        selected_idx = self.thumbs_view.selectedIndex()
        improvements_mgr = self._improvements_getter()
        if improvements_mgr.selected_index() != selected_idx:
            self._main_splitter.notify_change_done()
        improvements_mgr.select_alternative(selected_idx)


class FunctionButtonsLayout(QtWidgets.QHBoxLayout):
    def __init__(self, regenerate_button=False):
        super().__init__()

        self.choose_button = QtWidgets.QPushButton("Choose this version")
        self.addWidget(self.choose_button)
        self.setAlignment(self.choose_button, QtCore.Qt.AlignmentFlag.AlignLeft)

        if regenerate_button:
            self.regenerate_button = QtWidgets.QPushButton("Regenerate")
            self.addWidget(self.regenerate_button)
            self.setAlignment(self.regenerate_button, QtCore.Qt.AlignmentFlag.AlignRight)


class ImageDisplay(QtWidgets.QLabel):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setAlignment(QtCore.Qt.AlignCenter)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(950, 500)


class ThumbnailsListView(QtWidgets.QListWidget):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self._items = []

        self.setViewMode(QtWidgets.QListWidget.IconMode)
        self.setIconSize(QtCore.QSize(460, 300))
        self.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.setMovement(QtWidgets.QListWidget.Static)

    def items(self):
        return self._items

    def addItem(self, aitem: QListWidgetItem) -> None:
        super().addItem(aitem)
        self._items.append(aitem)

    def replaceItem(self, idx: int, new_item: QListWidgetItem):
        if idx < 0:
            idx += len(self._items)
        self._items = [item.clone() for item in self._items]
        self._items[idx] = new_item

        super().clear()
        for item in self._items:
            super().addItem(item)

    def clear(self) -> None:
        super().clear()
        self._items.clear()

    def selectedIndex(self) -> Optional[int]:
        curr_item = self.currentItem()
        try:
            return self._items.index(curr_item) if curr_item else None
        except ValueError:
            return None


class NavigationButton(QtWidgets.QPushButton):
    def __init__(self, text: str):
        super().__init__(text)

        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(50, 50)


class GoToDialog(QtWidgets.QDialog):
    def __init__(self, parent, document: BeamerDocument):
        super().__init__(parent)

        self._document = document

        self.page_option = QtWidgets.QRadioButton("Page")
        self.frame_option = QtWidgets.QRadioButton("Frame")
        self.number = QtWidgets.QSpinBox()
        self.ok_button = QtWidgets.QPushButton("OK")

        radiobuttons = QtWidgets.QHBoxLayout()
        radiobuttons.addWidget(self.page_option)
        radiobuttons.addWidget(self.frame_option)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(radiobuttons)
        layout.addWidget(self.number)
        layout.addWidget(self.ok_button)

        self.setWindowTitle("Go to...")
        self.setLayout(layout)

        self.page_option.setChecked(True)
        self.number.setMinimum(1)
        self.number.setMaximum(self._document.page_count())

        self.page_option.toggled.connect(self._page_option_toggled)
        self.frame_option.toggled.connect(self._frame_option_toggled)

    def _page_option_toggled(self, is_checked: bool):
        if not is_checked:
            return

        self.number.setMaximum(self._document.page_count())

    def _frame_option_toggled(self, is_checked: bool):
        if not is_checked:
            return

        self.number.setMaximum(self._document.frame_count())


# class WaitingDialogRunner(QtWidgets.QProgressDialog):
#     class __OperationRunner(QtCore.QObject):
#         def __init__(self, _operation: Callable):
#             super().__init__()
#             self.result = None
#             self._operation = _operation
#
#         def run(self):
#             self.result = self._operation()
#
#     def __init__(self, parent: QtWidgets.QWidget, operation: Callable, dialog_title="", dialog_text=""):
#         super().__init__(parent)
#
#         self.setWindowTitle(dialog_title)
#         self.setLabelText(dialog_text)
#         self.setMinimum(0)
#         self.setMaximum(0)
#         self.setValue(0)
#         self._runner = self.__OperationRunner(operation)
#
#     def run(self) -> Any:
#         thread = QtCore.QThread()
#         self._runner.moveToThread(thread)
#         thread.started.connect(self._runner.run)
#
#         self.setVisible(True)
#         thread.start()
#         if not thread.wait():
#             raise RuntimeError("Operation failed, what to do now?")
#         self.setVisible(False)
#         return self._runner.result
