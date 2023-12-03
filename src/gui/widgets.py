from PyQt5 import QtWidgets, QtCore
from typing import Callable


class MainSplitter(QtWidgets.QSplitter):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(QtCore.Qt.Orientation.Horizontal, parent)

        self.left_pane = MainSplitterLeftPane(self)
        self.right_pane = MainSplitterRightPane(self)

        self.addWidget(self.left_pane)
        self.addWidget(self.right_pane)
        self.setSizes([970, 430])


class MainSplitterLeftPane(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.image_display = ImageDisplay(self)
        self.function_buttons = FunctionButtonsLayout()
        self.navigation_buttons = NavigationButtonsLayout()

        layout.addWidget(self.image_display)
        layout.addLayout(self.function_buttons)
        layout.addLayout(self.navigation_buttons)


class MainSplitterRightPane(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.top_thumbs_view = ThumbnailsListView(self)
        self.bottom_thumbs_view = ThumbnailsListView(self)

        first_label = QtWidgets.QLabel(self)
        first_label.setText("Frame changes:")
        second_label = QtWidgets.QLabel(self)
        second_label.setText("Presentation (global) changes:")

        layout.addWidget(first_label)
        layout.addWidget(self.top_thumbs_view)
        layout.addSpacing(10)
        layout.addWidget(second_label)
        layout.addWidget(self.bottom_thumbs_view)


class NavigationButtonsLayout(QtWidgets.QHBoxLayout):
    def __init__(self):
        super().__init__()

        self.prev_button = NavigationButton("←")
        self.next_button = NavigationButton("→")

        self.addWidget(self.prev_button)
        self.addSpacing(20)
        self.addWidget(self.next_button)


class FunctionButtonsLayout(QtWidgets.QHBoxLayout):
    def __init__(self):
        super().__init__()

        self.save_button = QtWidgets.QPushButton("Save changes")
        self.save_button.setEnabled(False)

        self.improve_button = QtWidgets.QPushButton("Select this version")
        self.improve_button.setEnabled(False)

        self.addWidget(self.save_button)
        self.addWidget(self.improve_button)
        self.setAlignment(self.save_button, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setAlignment(self.improve_button, QtCore.Qt.AlignmentFlag.AlignRight)


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
    def __init__(self, text: str):
        super().__init__(text)

        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(50, 50)
