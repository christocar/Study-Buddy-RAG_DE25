from fastapi.testclient import TestClient
from youtube_transcript_api import RequestBlocked

from study_buddy.api import youtube
from study_buddy.api.main import app
from study_buddy.models import Document, Section

client = TestClient(app)

LINK = "https://youtu.be/KdeoPglfpb8"


def fake_load_youtube(url):
    # Fake loader, no network, always using the same video
    return Document(
        filename="ai-ops-week-6-KdeoPglfpb8",
        source_type="youtube",
        sections=[Section(text="hello world", source_location={"second": 0})],
    )


def test_youtube_returns_document_id(monkeypatch):
    monkeypatch.setattr(youtube, "load_youtube", fake_load_youtube)
    monkeypatch.setattr(youtube, "ingest_document", lambda document: 69)

    response = client.post("/youtube", json={"url": LINK})

    assert response.status_code == 200
    assert response.json() == {
        "document_id": 69,
        "filename": "ai-ops-week-6-KdeoPglfpb8",
    }


# Simulating an error where loader refuses the link
def test_refused_link_gives_400_with_the_reason(monkeypatch):
    def refuses(url):
        raise ValueError("Wasn't able to extract a video id from 'x'")

    monkeypatch.setattr(youtube, "load_youtube", refuses)

    response = client.post("/youtube", json={"url": "x"})

    assert response.status_code == 400
    assert "video id" in response.json()["detail"]


# Simulates an error where Youtube blocks the server.
def test_blocked_gives_code_503(monkeypatch):
    def blocked(url):
        raise RequestBlocked("KdeoPglfpb8")

    monkeypatch.setattr(youtube, "load_youtube", blocked)

    response = client.post("/youtube", json={"url": LINK})

    assert response.status_code == 503
