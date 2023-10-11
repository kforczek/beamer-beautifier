import os
import shutil


def select_example() -> str:
    example_docs = [
        ("Simple (single page)", "simple-single"),
        ("Simple (multiple pages)", "simple-multiple"),
        ("Freiburg University 1", "freiburg-demo-1"),
        ("Freiburg University 2", "freiburg-demo-2"),
        ("Overleaf (Universitat Siegen)", "overleaf-siegen")
    ]

    print("Select an example to continue with:")

    idx_dict = {str(idx+1): pair for idx, pair in enumerate(example_docs)}
    for idx, pair in idx_dict.items():
        disp_name = pair[0]
        print(f'{idx}: "{disp_name}"')

    selection = ""
    while selection not in idx_dict:
        selection = input("Please type a number: ")

    _, src_folder = idx_dict[selection]
    return copy_example_to_temp_folder(src_folder)


def copy_example_to_temp_folder(src_folder: str) -> str:
    TEMP_FOLDER_NAME = "temp"

    base_path = os.path.join(os.path.dirname(os.getcwd()), "examples")
    src_path = os.path.join(base_path, src_folder)
    dest_path = os.path.join(base_path, TEMP_FOLDER_NAME)
    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)

    shutil.copytree(src_path, dest_path)
    return os.path.join(dest_path, "main.tex")
