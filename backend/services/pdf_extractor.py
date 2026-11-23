import io

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extrai texto legível de um arquivo PDF binário usando PyMuPDF (fitz) ou fallback pypdf."""
    # 1. Tenta usar PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        full_text = []
        for index, page in enumerate(doc):
            text = page.get_text()
            if text:
                full_text.append(f"--- Página {index + 1} ---\n{text.strip()}")
        extracted = "\n\n".join(full_text)
        if extracted.strip():
            return extracted.strip()
    except ImportError:
        pass

    # 2. Tenta usar pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        full_text = []
        for index, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text.append(f"--- Página {index + 1} ---\n{text.strip()}")
        extracted = "\n\n".join(full_text)
        if extracted.strip():
            return extracted.strip()
    except ImportError:
        pass

    # Se nenhum leitor estiver instalado
    raise ValueError("Nenhum leitor de PDF (PyMuPDF ou pypdf) está instalado no ambiente.")
