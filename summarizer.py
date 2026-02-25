import io
import logging

import requests
from bs4 import BeautifulSoup
import pypdf

from logger import log_event

MAX_CONTENT_CHARS = 100_000

PERSONALITY_PREAMBLE = """\
You are Agnilonda Pakou, a warm, knowledgeable, and concise AI assistant.
You speak clearly and directly, avoiding unnecessary jargon. You are patient
and thorough but always respect the reader's time.

When summarizing, you:
- Highlight the most important ideas in a few short paragraphs.
- Provide brief context about the source when relevant.
- End with a single clearly labeled line: "Key Takeaway: <one sentence>".

Your task: Summarize the following content.
---
"""


def summarize_url(
    url: str,
    client,
    session_id: str,
    logger: logging.Logger,
) -> str:
    if not url.startswith(("http://", "https://")):
        log_event(
            logger, "WARNING", "validation_error", session_id,
            "URL", url, client.model_name,
            error_message="URL must start with http:// or https://",
        )
        raise ValueError("URL must start with http:// or https://")

    log_event(
        logger, "INFO", "summary_requested", session_id,
        "URL", url, client.model_name,
    )

    response = requests.get(
        url,
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0 (compatible; FilesAI/1.0)"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    if not text.strip():
        log_event(
            logger, "WARNING", "validation_error", session_id,
            "URL", url, client.model_name,
            error_message="No readable text extracted from page",
        )
        raise ValueError(
            "No readable text could be extracted from this page. "
            "It may require a login or block automated access."
        )

    content = text[:MAX_CONTENT_CHARS]
    prompt = PERSONALITY_PREAMBLE + content
    summary = client.generate(prompt)

    log_event(
        logger, "INFO", "summary_completed", session_id,
        "URL", url, client.model_name,
        summary_length=len(summary),
    )
    return summary


def summarize_pdf(
    uploaded_file,
    client,
    session_id: str,
    logger: logging.Logger,
) -> str:
    filename = getattr(uploaded_file, "name", "unknown.pdf")

    log_event(
        logger, "INFO", "summary_requested", session_id,
        "PDF", filename, client.model_name,
    )

    pdf_bytes = uploaded_file.read()
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))

    pages_text: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages_text.append(page_text)

    full_text = "\n".join(pages_text).strip()

    if not full_text:
        log_event(
            logger, "WARNING", "validation_error", session_id,
            "PDF", filename, client.model_name,
            error_message="No text extracted - may be a scanned/image PDF",
        )
        raise ValueError(
            "No text could be extracted from this PDF. "
            "It may be a scanned document or image-only PDF (OCR not supported)."
        )

    content = full_text[:MAX_CONTENT_CHARS]
    prompt = PERSONALITY_PREAMBLE + content
    summary = client.generate(prompt)

    log_event(
        logger, "INFO", "summary_completed", session_id,
        "PDF", filename, client.model_name,
        summary_length=len(summary),
    )
    return summary
