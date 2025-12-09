# backend/utils.py
import json
from typing import Optional
import fitz  # pymupdf
from bs4 import BeautifulSoup


def extract_text_from_upload(
    filename: str,
    content_type: Optional[str],
    data: bytes,
) -> str:
    """
    Return plain text from various file types.
    """
    ext = filename.lower().split(".")[-1]
    content_type = (content_type or "").lower()

    if ext in ["md", "txt"]:
        return data.decode("utf-8", errors="ignore")

    if ext == "json":
        obj = json.loads(data.decode("utf-8", errors="ignore"))
        # pretty-print JSON to text
        return json.dumps(obj, indent=2)

    if ext in ["html", "htm"] or "html" in content_type:
        soup = BeautifulSoup(data, "html.parser")
        # keep visible text only
        return soup.get_text(separator="\n")

    if ext == "pdf" or "pdf" in content_type:
        text_parts = []
        with fitz.open(stream=data, filetype="pdf") as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)

    # fallback
    return data.decode("utf-8", errors="ignore")
