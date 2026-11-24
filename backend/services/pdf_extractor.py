import io


def _format_pages(pages_text) -> str:
    full_text = [
        f"--- Página {index + 1} ---\n{text.strip()}"
        for index, text in enumerate(pages_text)
        if text and text.strip()
    ]
    return "\n\n".join(full_text).strip()


def _extract_with_pymupdf(file_bytes: bytes) -> str:
    import fitz
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        return _format_pages(page.get_text() for page in doc)


def _extract_with_pypdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    return _format_pages(page.extract_text() for page in reader.pages)


def _extract_with_pypdfium2(file_bytes: bytes) -> str:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(file_bytes)
    try:
        pages_text = []
        for page in pdf:
            textpage = page.get_textpage()
            pages_text.append(textpage.get_text_range())
            textpage.close()
            page.close()
        return _format_pages(pages_text)
    finally:
        pdf.close()


_EXTRACTORS = (
    ("PyMuPDF", _extract_with_pymupdf),
    ("pypdf", _extract_with_pypdf),
    ("pypdfium2", _extract_with_pypdfium2),
)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extrai texto legível de um PDF, tentando PyMuPDF, pypdf e pypdfium2 em sequência."""
    available = []
    errors = []

    for name, extractor in _EXTRACTORS:
        try:
            text = extractor(file_bytes)
        except ImportError:
            continue
        except Exception as exc:  # PDF corrompido, criptografado etc.
            available.append(name)
            errors.append(f"{name}: {exc}")
            continue

        available.append(name)
        if text:
            return text

    if not available:
        raise ValueError(
            "Nenhum leitor de PDF (PyMuPDF, pypdf ou pypdfium2) está instalado no ambiente. "
            "Execute: pip install -r backend/requirements.txt"
        )

    if errors and len(errors) == len(available):
        raise ValueError(
            "Não foi possível abrir o PDF (arquivo corrompido ou protegido por senha). "
            f"Detalhes: {'; '.join(errors)}"
        )

    raise ValueError(
        "O PDF não contém texto extraível. Provavelmente é um documento escaneado (imagem). "
        "Envie um PDF com texto selecionável ou cole o conteúdo como texto."
    )
