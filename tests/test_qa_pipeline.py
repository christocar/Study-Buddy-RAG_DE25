"""
Tests for answer_question: that it wires retrieve() into generate() and passes
the question to both. The connections and both steps are fakes, so there is
no API key, no Postgres and no model.
"""

from contextlib import nullcontext

from study_buddy.models import Answer, Source
from study_buddy.qa import pipeline
from study_buddy.qa.pipeline import answer_question

SOURCES = [Source(chunk_id=20, filename="keys.md", content="A primary key.")]


def test_retrieved_chunks_go_to_generate(monkeypatch):
    calls: dict = {}

    def fake_retrieve(question, *, client, db, conn, top_k):
        calls["retrieve"] = (question, top_k)
        return SOURCES

    def fake_generate(question, sources):
        calls["generate"] = (question, sources)
        return Answer(answer="Unique.", sources=sources)

    # The connections are never used by the fakes, so plain stand-ins will do
    monkeypatch.setattr(pipeline, "get_connection", lambda: nullcontext("conn"))
    monkeypatch.setattr(pipeline, "get_embedding_client", lambda: "client")
    monkeypatch.setattr(pipeline, "get_vector_db", lambda: "db")
    monkeypatch.setattr(pipeline, "retrieve", fake_retrieve)
    monkeypatch.setattr(pipeline, "generate", fake_generate)

    answer = answer_question("What is a primary key?", top_k=3)

    assert calls["retrieve"] == ("What is a primary key?", 3)
    assert calls["generate"] == ("What is a primary key?", SOURCES)
    assert answer.sources == SOURCES
