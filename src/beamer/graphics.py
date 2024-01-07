from fitz import fitz


def pixmap_from_document(document, page_idx: int):
    zoom_factor = 4.0
    mat = fitz.Matrix(zoom_factor, zoom_factor)
    return document.load_page(page_idx).get_pixmap(matrix=mat, alpha=True)
