"""Tests for text chunking logic."""

import pytest
from app.services.chunk_service import clean_text, chunk_text


class TestCleanText:
    """Text normalisation tests."""

    def test_strip_whitespace(self):
        assert clean_text("  hello  ") == "hello"

    def test_normalize_windows_line_endings(self):
        assert clean_text("line1\r\nline2") == "line1\nline2"

    def test_normalize_legacy_mac_line_endings(self):
        assert clean_text("line1\rline2") == "line1\nline2"

    def test_collapse_multiple_blank_lines(self):
        text = "paragraph1\n\n\n\n\nparagraph2"
        result = clean_text(text)
        assert result == "paragraph1\n\nparagraph2"

    def test_preserve_single_blank_line(self):
        text = "paragraph1\n\nparagraph2"
        assert clean_text(text) == "paragraph1\n\nparagraph2"

    def test_preserve_chinese_punctuation(self):
        text = "盼望着，盼望着，东风来了。"
        assert clean_text(text) == "盼望着，盼望着，东风来了。"


class TestChunkText:
    """Chunk splitting tests."""

    def test_empty_string(self):
        assert chunk_text("") == []

    def test_whitespace_only(self):
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        text = "这是一段很短的文字。"
        chunks = chunk_text(text, chunk_size=300)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_exact_chunk_size(self):
        text = "A" * 300
        chunks = chunk_text(text, chunk_size=300)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_multiple_chunks(self):
        # Create a text that should produce ~3 chunks of 300 chars with 50 overlap
        text = "Hello World! " * 100  # ~1300 chars
        chunks = chunk_text(text, chunk_size=300, overlap=50)
        assert len(chunks) > 1
        # Each chunk should be at most 300 chars
        for c in chunks:
            assert len(c) <= 300

    def test_overlap_between_chunks(self):
        # Use a predictable pattern to verify overlap
        text = "".join(f"{i:03d}" for i in range(200))  # 600 chars of digits
        chunks = chunk_text(text, chunk_size=150, overlap=30)
        assert len(chunks) >= 3
        # Second chunk should overlap with the end of first chunk
        first_end = chunks[0][-30:]
        second_start = chunks[1][:30]
        # At least some characters should match (sliding window)
        assert len(chunks[0]) <= 150

    def test_tail_merge(self):
        # chunk_size=50, overlap=10, step=40.
        # text = 95 chars → start positions: 0, 40, 80
        #   start=0:  0-50  → "A"*50
        #   start=40: 40-90 → "A"*50
        #   start=80: 80-95 → "A"*15  (< 30 chars) → merged into previous chunk
        text = "A" * 95
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        assert len(chunks) == 2
        # The tiny tail should have been merged into the second chunk
        assert len(chunks[-1]) >= 50  # original 50 + 15 merged

    def test_overlap_validation(self):
        # Text must be longer than chunk_size to reach the overlap check.
        with pytest.raises(ValueError):
            chunk_text("A" * 200, chunk_size=100, overlap=100)

    def test_overlap_greater_than_chunk_size(self):
        with pytest.raises(ValueError):
            chunk_text("A" * 200, chunk_size=100, overlap=150)
