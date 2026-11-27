"""
Tests for POST /ask. answer_question is swapped for a fake, so there is no
API key, no database and no model: only the HTTP side is tested here.
"""

from fastapi.testclient import TestClient

from study_buddy.api import ask
from study_buddy.api.main import app
from study_buddy.models import Answer, Source

client = TestClient(app)

ANSWER = Answer(
    answer="A primary key is unique.",
    sources=[
        Source(
            chunk_id=20,
            filename="keys.md",
            source_location=None,
            content="A primary key identifies each row.",
        )
    ],
)


def test_ask_returns_the_answer_and_its_sources(monkeypatch):
    asked: list[str] = []

    def fake_answer_question(question):
        asked.append(question)
        return ANSWER

    monkeypatch.setattr(ask, "answer_question", fake_answer_question)

    response = client.post("/ask", json={"question": "What is a primary key?"})

    assert response.status_code == 200
    assert response.json() == ANSWER.model_dump()
    assert asked == ["What is a primary key?"]


def test_no_sources_is_still_a_200(monkeypatch):
    no_answer = Answer(answer="I don't know.", sources=[])
    monkeypatch.setattr(ask, "answer_question", lambda question: no_answer)

    response = client.post("/ask", json={"question": "Capital of France?"})

    assert response.status_code == 200
    assert response.json()["sources"] == []


def test_empty_question_gives_422():
    # Field(min_length=1) refuses it before answer_question is called
    response = client.post("/ask", json={"question": ""})

    assert response.status_code == 422


def test_missing_question_gives_422():
    response = client.post("/ask", json={})

    assert response.status_code == 422


def test_refused_question_gives_400_with_the_reason(monkeypatch):
    def fake_refuses(question):
        raise ValueError("The question is empty.")

    monkeypatch.setattr(ask, "answer_question", fake_refuses)

    response = client.post("/ask", json={"question": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "The question is empty."
