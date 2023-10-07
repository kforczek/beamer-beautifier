import sys
import fitz
from PyQt5 import QtCore, QtGui, QtWidgets
from src.beamer.document import BeamerDocument


class PDFViewer(QtWidgets.QWidget):
    def __init__(self, pdf_path: str, parent=None):
        super(PDFViewer, self).__init__(parent)

        self.current_page = 0
        self.pdf_path = pdf_path
        self.document = fitz.open(self.pdf_path)

        self.init_ui()

    def init_ui(self):
        self.setGeometry(100, 100, 1160, 700)
        self.setWindowTitle('Beamer Beautifier')

        self.pdf_widget = QtWidgets.QLabel(self)
        self.pdf_widget.setAlignment(QtCore.Qt.AlignCenter)

        self.pdf_list = QtWidgets.QListWidget(self)
        self.pdf_list.setViewMode(QtWidgets.QListWidget.IconMode)
        self.pdf_list.setIconSize(QtCore.QSize(460, 300))
        self.pdf_list.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.pdf_list.setMovement(QtWidgets.QListWidget.Static)

        pdf_label_container = QtWidgets.QWidget()
        pdf_label_layout = QtWidgets.QVBoxLayout()

        # Navigation buttons
        self.previous_button = QtWidgets.QPushButton("←")
        self.previous_button.clicked.connect(self.previous_page)
        self.previous_button.setFixedSize(50, 50)
        self.next_button = QtWidgets.QPushButton("→")
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setFixedSize(50, 50)

        # Button layout with spacers
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.previous_button)
        button_layout.addSpacing(20)  # Spacing between buttons
        button_layout.addWidget(self.next_button)
        button_layout.addStretch(1)

        pdf_label_layout.addWidget(self.pdf_widget)
        pdf_label_layout.addLayout(button_layout)
        pdf_label_container.setLayout(pdf_label_layout)

        # Set minimum width to avoid the widget disappearing
        pdf_label_container.setMinimumWidth(200)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(pdf_label_container)
        self.splitter.addWidget(self.pdf_list)

        self.splitter.setSizes([700, 460])

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        self.display_page()
        self.load_thumbnails()

    def load_thumbnails(self):
        while self.pdf_list.count() > 0:
            self.pdf_list.takeItem(0)

        for _ in range(10):
            pixmap = self.load_pixmap(self.current_page).scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            item = QtWidgets.QListWidgetItem()
            item.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(QtGui.QImage(pixmap.toImage()))))
            self.pdf_list.addItem(item)

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()
            self.load_thumbnails()

    def next_page(self):
        if self.current_page < self.document.page_count - 1:
            self.current_page += 1
            self.display_page()
            self.load_thumbnails()

    def display_page(self):
        current_width = self.pdf_widget.width()
        current_height = self.pdf_widget.height()
        pixmap = self.load_pixmap(self.current_page).scaled(
            current_width, current_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self.pdf_widget.setPixmap(pixmap)

    def load_pixmap(self, page):
        zoom_factor = 4.0

        mat = fitz.Matrix(zoom_factor, zoom_factor)

        pix = self.document.load_page(page).get_pixmap(matrix=mat, alpha=True)

        img = QtGui.QImage(pix.samples, pix.width, pix.height, pix.width * pix.n, QtGui.QImage.Format_RGBA8888)
        return QtGui.QPixmap.fromImage(img)

    def resizeEvent(self, event):
        self.display_page()
        super(PDFViewer, self).resizeEvent(event)

    def showEvent(self, event):
        self.display_page()
        super(PDFViewer, self).showEvent(event)


def run_viewer(document: BeamerDocument):
    doc_path = document.compile()
    app = QtWidgets.QApplication(sys.argv)
    viewer = PDFViewer(doc_path)
    viewer.show()
    sys.exit(app.exec_())
