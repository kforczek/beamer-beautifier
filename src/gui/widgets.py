from typing import Optional

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QListWidgetItem

from src.beamer.document.document import BeamerDocument


class MainSplitter(QtWidgets.QSplitter):
    def __init__(self, parent: QtWidgets.QWidget, document: BeamerDocument):
        super().__init__(QtCore.Qt.Orientation.Horizontal, parent)

        self._is_any_change = False

        self.left_pane = MainSplitterLeftPane(self)
        self.right_pane = MainSplitterRightPane(self, document)

        self.addWidget(self.left_pane)
        self.addWidget(self.right_pane)
        self.setSizes([970, 430])

    def notify_change_done(self):
        """Receives the information about any improvement being selected."""
        self._is_any_change = True
        self.left_pane.function_buttons.save_button.setEnabled(True)

    def is_any_change_done(self):
        return self._is_any_change


class MainSplitterLeftPane(QtWidgets.QWidget):
    def __init__(self, parent: MainSplitter):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.image_display = ImageDisplay(self)
        self.function_buttons = GlobalButtonsLayout()
        self.navigation_buttons = NavigationButtonsLayout()

        layout.addWidget(self.image_display)
        layout.addLayout(self.function_buttons)
        layout.addLayout(self.navigation_buttons)


class MainSplitterRightPane(QtWidgets.QTabWidget):
    def __init__(self, parent: MainSplitter, document: BeamerDocument):
        super().__init__(parent)

        self.frame_tab = ImprovementsTab(self, parent, document.current_local_improvements)
        self.background_tab = ImprovementsTab(self, parent, document.current_background_improvements)
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


class GlobalButtonsLayout(QtWidgets.QHBoxLayout):
    def __init__(self):
        super().__init__()

        self.save_button = QtWidgets.QPushButton("Save changes")
        self.save_button.setEnabled(False)

        self.addWidget(self.save_button)
        self.setAlignment(self.save_button, QtCore.Qt.AlignmentFlag.AlignLeft)


class ImprovementsTab(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget, main_splitter: MainSplitter, improvements_getter):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)
        self._improvements_getter = improvements_getter
        self._main_splitter = main_splitter

        self.thumbs_view = ThumbnailsListView(self)
        self.function_buttons = FunctionButtonsLayout()

        self.function_buttons.choose_button.clicked.connect(self._choose_button_click)
        self.function_buttons.regenerate_button.clicked.connect(self._regenerate_button_click)

        layout.addWidget(self.thumbs_view)
        layout.addLayout(self.function_buttons)

    def _choose_button_click(self):
        selected_idx = self.thumbs_view.selectedIndex()
        improvements_mgr = self._improvements_getter()
        if improvements_mgr.selected_index() != selected_idx:
            self._main_splitter.notify_change_done()
        improvements_mgr.select_alternative(selected_idx)

    def _regenerate_button_click(self):
        self._improvements_getter().generate_improvements()
        # TODO invalidate currently displayed thumbnails


class FunctionButtonsLayout(QtWidgets.QHBoxLayout):
    def __init__(self):
        super().__init__()

        self.choose_button = QtWidgets.QPushButton("Choose this version")
        self.regenerate_button = QtWidgets.QPushButton("Regenerate")

        self.addWidget(self.choose_button)
        self.addWidget(self.regenerate_button)
        self.setAlignment(self.choose_button, QtCore.Qt.AlignmentFlag.AlignLeft)
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

    def addItem(self, aitem: QListWidgetItem) -> None:
        super().addItem(aitem)
        self._items.append(aitem)

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
