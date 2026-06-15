"""
Text cleaning and chunk splitting.

The module normalises raw text and splits it into overlapping chunks suitable
for embedding generation.
"""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """
    Normalise *text* for downstream processing.

    Steps (order matters):

    1. Strip leading / trailing whitespace.
    2. Normalise Windows (``\\r\\n``) and legacy Mac (``\\r``) line endings to
       Unix (``\\n``).
    3. Collapse sequences of **three or more** blank lines into a single blank
       line (two consecutive ``\\n`` characters).
    4. Preserve Chinese punctuation and meaningful internal line breaks.
    """
    text = text.strip()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ consecutive newlines → exactly 2 (one blank line)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def chunk_text(
    text: str,
    chunk_size: int = 300,
    overlap: int = 50,
) -> list[str]:
    """
    Split *text* into overlapping chunks of up to *chunk_size* characters.

    Parameters
    ----------
    text:
        Cleaned text to split.
    chunk_size:
        Maximum characters per chunk (default 300).
    overlap:
        Number of characters shared between consecutive chunks (default 50).
        Must be strictly less than *chunk_size*.

    Returns
    -------
    list[str]
        One or more chunks.  An empty input produces an empty list.
        A text shorter than *chunk_size* is returned as a single chunk.
        Tail chunks shorter than 30 characters are merged into the previous
        chunk to avoid tiny orphan fragments.
    """
    text = text.strip()

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    step = chunk_size - overlap

    for start in range(0, len(text), step):
        chunk = text[start : start + chunk_size].strip()
        if not chunk:
            continue

        # Merge tiny trailing fragments into the previous chunk.
        if len(chunk) < 30 and chunks:
            chunks[-1] += chunk
        else:
            chunks.append(chunk)

    return chunks
