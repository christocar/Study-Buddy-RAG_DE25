# Test for chunking logic
# tests for split_text()-function + chunk_document()-function
# Kod: Engelska

"""
split_text function is tested with small numbers, size 10 and overlap 3,
this is on purpose to make a failing test more readable.

chunk_document is tested with lenhths build from CHUNK_SIZE, this way
the tests should still hold when/if the constants change.
"""

import string  # import used for ALPHABET constant

import pytest

from study_buddy.embedding.constants import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    MAX_INPUT_TOKENS,
    MIN_SECTION_CHARS,
)
from study_buddy.ingestion.chunker import chunk_document, split_text
from study_buddy.ingestion.loaders.text import load_text_file
from study_buddy.models import Document, Section

TEXT_22 = "0123456789abcdefghijkl"  # 22 characters in total
ALPHABET = string.ascii_letters + string.digits  # 62 different characters


# Function to create a document
def create_document(*sections: Section) -> Document:
    return Document(
        filename="world_domination_plans.pdf",
        source_type="pdf",
        sections=list(sections),
    )


# ================= split_text =================
#
#
# ==== SMALL WINDOW, SIZE + OVERLAP EXAMPLE ====
# Very small text to understand the size and overlap logic
# Making it very easy to read
SMALL_SAMPLE = "1234567890"


# Window moves 3 (4 MINUS 1)
def test_small_sample_window_moves_by_size_minus_overlap():
    pieces_small = split_text(SMALL_SAMPLE, size=4, overlap=1)

    assert pieces_small == ["1234", "4567", "7890"]


# The window moves 7 (10 - 3) and the last piece should reach the end
def test_window_moves_by_size_minus_overlap():
    pieces = split_text(TEXT_22, size=10, overlap=3)

    assert pieces == ["0123456789", "789abcdefg", "efghijkl"]


# A text that is exactly one window long gives exactly ONE piece, not a duplicate tail
def test_text_of_exactly_size_gives_one_piece():
    assert split_text("0123456789", size=10, overlap=3) == ["0123456789"]


# Nothing is lost, the pieces without their overlap still gives back the whole text
@pytest.mark.parametrize("length", [1, 9, 10, 11, 17, 18, 62])
def test_pieces_give_back_the_whole_text(length):
    text = ALPHABET[:length]

    pieces = split_text(text, size=10, overlap=3)

    assert pieces[0] + "".join(piece[3:] for piece in pieces[1:]) == text


# Guard: a step of 0 or less is refused,
# range() also raises ValueError on a step of 0,
# so a match proves that OUR guard raised it
@pytest.mark.parametrize(
    "size, overlap, message",
    [
        (10, 10, "below size"),
        (10, 11, "below size"),
        (10, -1, "below size"),
        (0, 0, "above 0"),
    ],
)
def test_bad_size_or_overlap_is_refused(size, overlap, message):
    with pytest.raises(ValueError, match=message):
        split_text(TEXT_22, size=size, overlap=overlap)


# Testing the constants: overlap below size, and a chunk under the models cap
def test_constants_are_safe():
    assert 0 <= CHUNK_OVERLAP < CHUNK_SIZE
    assert CHUNK_SIZE <= MAX_INPUT_TOKENS


# ================= chunk_document =================
#
#
# chunk_index counts 0, 1, 2... ... across ALL sections with no restart
def test_chunk_index_counts_from_zero_across_sections():
    doc = create_document(
        Section(text="a" * (CHUNK_SIZE * 2), source_location={"page": 1}),
        Section(text="b" * (CHUNK_SIZE * 2), source_location={"page": 2}),
    )

    chunks = chunk_document(doc)

    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


# No chunk spans across TWO sections(pages for a pdf) and every chunk,
# should keep its sections place.
def test_no_chunk_spans_over_two_sections():
    doc = create_document(
        Section(text="a" * (CHUNK_SIZE + 1), source_location={"page": 1}),
        Section(text="b" * (CHUNK_SIZE + 1), source_location={"page": 2}),
    )
    letter_on_page = {1: "a", 2: "b"}

    for chunk in chunk_document(doc):
        page = chunk.source_location["page"]
        assert set(chunk.content) == {letter_on_page[page]}


# A long .txt from issue #25: no chunk is longer than CHUNK_SIZE
def test_long_txt_never_gives_a_chunk_over_the_cap():
    data = ("A story about Bella the rabbit. " * 5000).encode(
        "utf-8"
    )  # 160k characters

    chunks = chunk_document(load_text_file("long.txt", data))

    assert len(chunks) > 1
    assert all(len(chunk.content) <= CHUNK_SIZE for chunk in chunks)


# A page number that gives no chunk, and exactly MIN_SECTION_CHARS is kept
def test_short_sections_are_skipped_without_a_gap():
    doc = create_document(
        Section(text="", source_location={"page": 1}),
        Section(text="12", source_location={"page": 2}),
        Section(text="x" * MIN_SECTION_CHARS, source_location={"page": 3}),
    )

    chunks = chunk_document(doc)

    assert [(c.chunk_index, c.source_location) for c in chunks] == [(0, {"page": 3})]


# A PDF with only images gives an an empty list so the pipeline can say so, NO OCR in project
def test_document_with_no_text_gives_no_chunks():
    doc = create_document(Section(text=""), Section(text="   \n  "))

    assert chunk_document(doc) == []
