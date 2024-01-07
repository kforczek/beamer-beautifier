import shutil
import subprocess
import os
from datetime import datetime


TEMP_DIR_NAME = ".bb-temp"
LOGS_SUBDIR_NAME = "bb-logs"


class CompilationError(OSError):
    def __init__(self, *args):
        super().__init__(*args)
        print()


def compile_tex(src_doc_path: str) -> str:
    """
    Compiles TeX document.
    :param src_doc_path: path to the TeX document to be compiled
    :return: path to the compiled PDF file
    """
    src_folder = os.path.dirname(src_doc_path)
    output_dir_path = create_temp_dir(src_folder) if TEMP_DIR_NAME not in src_doc_path else src_folder

    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    filename = os.path.basename(src_doc_path).split('.')[0]
    with open(os.path.join(output_dir_path, LOGS_SUBDIR_NAME, f'{timestamp}-{filename}.txt'), 'w') as log_file:
        try:
            subprocess.check_call(
                ['xelatex', f'-output-directory={output_dir_path}', '-interaction=nonstopmode', src_doc_path],
                cwd=os.path.dirname(src_doc_path), stdout=log_file, stderr=log_file
            )
        except subprocess.CalledProcessError:
            raise CompilationError(f"Failed to compile the LaTeX document: compilation process"
                                   f" ended with an error (see logs for more info).") from None

        file_path = get_dest_pdf_path(src_doc_path, output_dir_path)
        if not os.path.exists(file_path):
            raise CompilationError("Failed to compile the LaTeX document:"
                                   " output PDF file not created for unknown reason")

    return file_path


def get_dest_pdf_path(src_doc_path: str, output_dir_path: str) -> str:
    """Returns a path where a compiled PDF document should be located."""
    return os.path.join(output_dir_path, os.path.basename(src_doc_path).split('.')[0] + ".pdf")


def create_temp_dir(working_dir_path: str) -> str:
    """
    Creates a temporary working directory if it doesn't exist.
    Internal structure is also created (logs folder inside the temp dir).
    :return: path to the temporary directory
    """
    temp_dir_path = os.path.join(working_dir_path, TEMP_DIR_NAME)
    if os.path.exists(temp_dir_path):
        return temp_dir_path

    os.mkdir(temp_dir_path)
    for file in os.listdir(working_dir_path):
        abs_src_path = os.path.join(working_dir_path, file)
        if os.path.isfile(abs_src_path) and "tex" not in file.split("."):
            shutil.copyfile(abs_src_path, os.path.join(temp_dir_path, file))
        elif os.path.isdir(abs_src_path) and TEMP_DIR_NAME not in abs_src_path:
            shutil.copytree(abs_src_path, os.path.join(temp_dir_path, file))

    logs_dir_path = os.path.join(temp_dir_path, LOGS_SUBDIR_NAME)
    if not os.path.exists(logs_dir_path):
        os.mkdir(logs_dir_path)

    return temp_dir_path
