from PyQt5 import QtWidgets, QtCore


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
        self.function_buttons = GlobalButtonsLayout()
        self.navigation_buttons = NavigationButtonsLayout()

        layout.addWidget(self.image_display)
        layout.addLayout(self.function_buttons)
        layout.addLayout(self.navigation_buttons)


class MainSplitterRightPane(QtWidgets.QTabWidget):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self.frame_tab = ImprovementsTab(self)
        self.background_tab = ImprovementsTab(self)
        self.global_tab = ImprovementsTab(self)

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
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.thumbs_view = ThumbnailsListView(self)
        self.function_buttons = FunctionButtonsLayout()

        layout.addWidget(self.thumbs_view)
        layout.addLayout(self.function_buttons)


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
