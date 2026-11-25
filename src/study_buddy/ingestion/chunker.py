# chunker.py - Cuts a document into chunks.
# Code: English

"""
The chunker: a Document from a loader becomes a list of Chunks.

Who calls it: ingest_file()-function in ingestion/pipeline.py (ticket #34),
right after the loader (ticket 24) and before save_document (ticket #26).

Each Section is cut on its own, this way no Chunk can span over two Sections
and every Chunk keeps its Section's source_location.

chunk_index counts from 0 across the whole document.
"""

from study_buddy.embedding.constants import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    MIN_SECTION_CHARS,
)
from study_buddy.models import Chunk, Document


# function to split up text
def split_text(text: str, size: int, overlap: int) -> list[str]:
    """
    Splits text into pieces of at most 'size' characters. Each piece
    overlaps characters before the previous one has ended.
    """
    # A guard: The window must ALWAYS move forward with at least +1 character PER step.
    if size <= 0:
        raise ValueError(f"Size MUST be above 0, I got {size}..")
    if not 0 <= overlap < size:
        raise ValueError(
            f"Overlap MUST be AT LEAST 0 and below size ({size}), I got {overlap}.."
        )

    step = size - overlap

    stop = max(len(text) - overlap, 1)

    return [text[start : start + size] for start in range(0, stop, step)]


# Function for the chunking logic
def chunk_document(document: Document) -> list[Chunk]:
    """
    Cut every Section of the document into Chunks using CHUNK_SIZE,
    CHUNK_OVERLAP and MIN_SECTION_CHARS from embedding/constants.py script.
    """
    chunks = []

    for section in document.sections:
        # A page with only IMAGES or a page number -> nothing to find
        if len(section.text.strip()) < MIN_SECTION_CHARS:
            continue

        for piece in split_text(section.text, CHUNK_SIZE, CHUNK_OVERLAP):
            # If there is only spaces and new lines == Nothing to find == no Chunk
            if not piece.strip():
                continue

            chunks.append(
                Chunk(
                    # The nr of chunks so far; 0, 1, 2, 3, 4, ... 69 over all sections
                    chunk_index=len(chunks),
                    content=piece,
                    source_location=section.source_location,
                )
            )

    return chunks
