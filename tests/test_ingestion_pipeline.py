# test_ingestion_pipeline.py
# Tests for ingest_file() with fakes, no Postgres, no API is needed.
# Code: English
# Comments: English

"""
ingest_file() glues four pieces together.
These tests check the glue, not the pieces: each piece already has its own tests.

Postgres, the embedding API and LanceDB are swapped for fakes with monkeypatch,
this way the tests can run in CI. The loader and the chunker are the real ones.

The fake Postgres hands out ids from 100 and not from 0. If the pipeline mixed up
chunk_index and the chunk id, the vectors would end up under the wrong ids and
the first test would fail.
"""

from contextlib import nullcontext

import pytest

from study_buddy.embedding.constants import CHUNK_SIZE, MIN_SECTION_CHARS
from study_buddy.ingestion import pipeline

# Built from the constants, like the chunker tests, so they hold if they change
LONG_TEXT = ("word " * CHUNK_SIZE).encode("utf-8")  # several chunks
SHORT_TEXT = ("x" * (MIN_SECTION_CHARS - 1)).encode("utf-8")  # no chunk at all


@pytest.fixture
def fakes(monkeypatch):
    # Each fake writes down what it got, so the tests can check it afterwards
    calls = {"embedded": None, "saved_chunks": None, "vectors": None}

    def fake_embed_texts(client, texts):
        calls["embedded"] = texts
        # Vector number i is [i], so a test can see which vector went where
        return [[float(i)] for i in range(len(texts))]

    def fake_save_document(conn, document, chunks):
        calls["saved_chunks"] = chunks
        # Ids from 100, so a mix-up with chunk_index (0, 1, 2...) cannot pass
        return 7, [100 + chunk.chunk_index for chunk in chunks]

    def fake_save_vectors(db, chunk_ids, vectors):
        calls["vectors"] = dict(zip(chunk_ids, vectors))

    # Swap the names INSIDE pipeline.py, where ingest_file looks them up.
    # nullcontext() works in a with block like a connection, and gives None.
    monkeypatch.setattr(pipeline, "get_embedding_client", lambda: None)
    monkeypatch.setattr(pipeline, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(pipeline, "get_connection", nullcontext)
    monkeypatch.setattr(pipeline, "save_document", fake_save_document)
    monkeypatch.setattr(pipeline, "save_vectors", fake_save_vectors)
    return calls


# Test 1: each vector is saved under the id Postgres handed out for its own chunk
def test_vectors_go_under_the_ids_from_postgres(fakes):
    document_id = pipeline.ingest_file("notes.txt", LONG_TEXT)

    chunks = fakes["saved_chunks"]
    assert len(chunks) > 1  # with one chunk, the order would prove nothing
    assert document_id == 7
    # Vector i was made from the text of chunk i...
    assert fakes["embedded"] == [chunk.content for chunk in chunks]
    # ...and is saved under the id of chunk i
    assert fakes["vectors"] == {100 + i: [float(i)] for i in range(len(chunks))}


# Test 2: the embedding fails ON PURPOSE here. Nothing may reach Postgres
def test_embedding_failure_saves_nothing(fakes, monkeypatch):
    def broken_embed_texts(client, texts):
        raise RuntimeError("Grunden is down")

    monkeypatch.setattr(pipeline, "get_vector_db", lambda: None)
    monkeypatch.setattr(pipeline, "embed_texts", broken_embed_texts)

    with pytest.raises(RuntimeError, match="Grunden is down"):
        pipeline.ingest_file("notes.txt", LONG_TEXT)

    assert fakes["saved_chunks"] is None


# Test 3: a text too short for a chunk stops before the API and the database
def test_too_short_text_stops_early(fakes):
    with pytest.raises(ValueError, match="too little text"):
        pipeline.ingest_file("short.txt", SHORT_TEXT)

    assert fakes["embedded"] is None
    assert fakes["saved_chunks"] is None
