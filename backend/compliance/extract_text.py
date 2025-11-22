import fitz  # PyMuPDF

def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF document."""
    try:
        text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text("text")
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"PDF text extraction failed: {e}")
