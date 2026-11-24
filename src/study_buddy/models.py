# models.py - Script för samlade pydantic models
# Kod: Engelska

"""
Our models and the shape that every track hands to the next.

Field names match our sql/schema.sql This way the same word means the same thing,
from the loader to Postgres and out to the sources dropdown menu in streamlit.

Only what Phase 1 needs right now:
file_hash, status, error_message and char_count are not included.

TODO: Update fields for when we need fields mentioned above.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict


# Class for the SECTIONS of our files
class Section(BaseModel):
    """
    One page, one section of a video or the whole .txt file
    """

    text: str
    # {"second": 125} for a video, {"page": 69} for a PDF or None for .txt and .md
    source_location: dict | None = None


# Class for DOCUMENTS (txt, pdf, md, youtube.. ...)
class Document(BaseModel):
    """
    What every loader hands to our chunker.
    """

    filename: str
    # Exact match so the loader lowercases our file suffixes(.pdf, .MD, .Txt etc)
    source_type: Literal["txt", "md", "pdf", "youtube"]
    sections: list[Section]


# Class for CHUNKS
class Chunk(BaseModel):
    """
    One piece of text after chunking BEFORE it is saved.

    chunk_index is the position in its document and starts at 0 in
    EVERY document. This is NOT the id in Postgres that the chunk gets when saved.
    """

    model_config = ConfigDict(extra="forbid")

    chunk_index: int
    content: str
    source_location: dict | None = None


# Class for our SOURCE
class Source(BaseModel):
    """
    Only ONE row in the sources dropdown.

    chunk_id is chunks.id in Postgres. The SAME id the vector has in LanceDB.
    """

    chunk_id: int
    filename: str
    source_location: dict | None = None
    content: str


# Class for our ANSWERS
class Answer(BaseModel):
    """
    What our POST /ask-endpoint returns.
    sources CAN be an empty list.
    """

    answer: str
    sources: list[Source]
