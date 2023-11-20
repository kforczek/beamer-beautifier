from PyQt5 import QtWidgets, QtCore
from typing import Callable


class MainSplitter(QtWidgets.QSplitter):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(QtCore.Qt.Orientation.Horizontal, parent)

        left_pane = MainSplitterLeftPane(self)
        right_pane = MainSplitterRightPane(self)

        self.addWidget(left_pane)
        self.addWidget(right_pane)
        self.setSizes([970, 430])

        self.image_display = left_pane.image_display
        self.thumbnails_view = right_pane.thumbnails_view
        self.prev_button = left_pane.navigation_buttons.prev_button
        self.next_button = left_pane.navigation_buttons.next_button
        self.improve_button = left_pane.improve_button


class MainSplitterLeftPane(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.image_display = ImageDisplay(self)
        self.improve_button = QtWidgets.QPushButton("Select this version")
        self.improve_button.setEnabled(False)
        self.navigation_buttons = NavigationButtonsLayout(self)

        layout.addWidget(self.image_display)
        layout.addWidget(self.improve_button)
        layout.setAlignment(self.improve_button, QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addLayout(self.navigation_buttons)


class MainSplitterRightPane(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.thumbnails_view = ThumbnailsListView(self)
        layout.addWidget(self.thumbnails_view)


class NavigationButtonsLayout(QtWidgets.QHBoxLayout):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__()

        self.prev_button = NavigationButton(parent, "←")
        self.next_button = NavigationButton(parent, "→")

        self.addWidget(self.prev_button)
        self.addSpacing(20)
        self.addWidget(self.next_button)


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

        self.setViewMode(QtWidgets.QListWidget.IconMode)
        self.setIconSize(QtCore.QSize(460, 300))
        self.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.setMovement(QtWidgets.QListWidget.Static)


class NavigationButton(QtWidgets.QPushButton):
    def __init__(self, parent: QtWidgets.QWidget, text: str):
        super().__init__(text, parent)

        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(50, 50)