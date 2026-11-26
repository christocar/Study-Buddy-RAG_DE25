from fastapi.testclient import TestClient

from study_buddy.api import upload
from study_buddy.api.main import app

client = TestClient(app)


def fake_ingest_file(filename, data):
    # a fake pipeline: no database, no API key, always says "document 42"
    return 42


def fake_ingest_that_refuses(filename, data):
    # the real pipeline raises ValueError for files it can't take
    raise ValueError(f"Cannot load '{filename}': expected a .txt or .md file")


def test_upload_returns_document_id(monkeypatch):
    # swap the real pipeline for our fake during this test
    monkeypatch.setattr(upload, "ingest_file", fake_ingest_file)

    response = client.post("/upload", files={"file": ("notes.txt", b"hello")})

    assert response.status_code == 200
    assert response.json() == {"document_id": 42, "filename": "notes.txt"}


def test_refused_file_gives_400_with_the_reason(monkeypatch):
    monkeypatch.setattr(upload, "ingest_file", fake_ingest_that_refuses)

    response = client.post("/upload", files={"file": ("lecture.pdf", b"%PDF")})

    assert response.status_code == 400
    assert "expected a .txt or .md" in response.json()["detail"]
