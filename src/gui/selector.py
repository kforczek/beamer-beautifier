from PyQt5.QtWidgets import QFileDialog
from pathlib import Path


def get_user_document_path() -> str:
    dialog_name = "Select a presentation to open"
    file_filter = "Beamer documents (*.tex);; All files (*.*)"
    start_folder = str(Path.home())

    filename = QFileDialog.getOpenFileName(None, dialog_name, start_folder, file_filter)
    return filename
