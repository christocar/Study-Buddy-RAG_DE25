# test_pydantic_models.py - Test for our BaseModels and their shape.
# Code: English
# Comments: English

import pytest
from pydantic import ValidationError

from study_buddy.models import Answer, Chunk, Document, Section, Source


# The four filetypes the project plans to use must all get through
@pytest.mark.parametrize("source_type", ["txt", "md", "pdf", "youtube"])
def test_document_accepts_the_source_types(source_type):
    doc = Document(
        filename="world-domination-notes", source_type=source_type, sections=[]
    )
    assert doc.source_type == source_type


# Literal is an exact match - NOTES.TXT must be lowercased by the loader first
@pytest.mark.parametrize("source_type", ["docx", "pDF", "TXT", "Md"])
def test_document_rejects_unknown_and_uppercase_source_types(source_type):
    with pytest.raises(ValidationError):
        Document(filename="notes", source_type=source_type, sections=[])


# a .txt file has no page or second, so the loader can leave the place out
def test_source_location_is_none_when_left_out():
    assert Section(text="A whole .txt file").source_location is None


# "I dont know" is a valid answer, and it has no sources
def test_answer_without_sources_is_valid():
    answer = Answer(answer="The material does not cover that.", sources=[])
    assert answer.sources == []


# The trip FastAPI and Streamlit make: model -> JSON -> model, nothing lost
def test_answer_survives_the_trip_through_json():
    source = Source(
        chunk_id=42,
        filename="lecture.pdf",
        source_location={"page": 3},
        content="RAG retrieves before it generates.",
    )
    answer = Answer(answer="It retrieves first.", sources=[source])

    assert Answer.model_validate_json(answer.model_dump_json()) == answer


# A chunk is not saved yet so it has a place but no ID
def test_chunk_has_no_id_before_it_is_saved():
    with pytest.raises(ValidationError):
        Chunk(chunk_id=69, chunk_index=0, content="Text before it is saved.")
