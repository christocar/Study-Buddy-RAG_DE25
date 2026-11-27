import httpx

from study_buddy.frontend import api_client


def fake_backend(handler, monkeypatch):
    # route every httpx call to our handler instead of a real backend
    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def fake_post(url, **kwargs):
        with real_client(transport=transport) as client:
            return client.post(url, **kwargs)

    monkeypatch.setattr(api_client.httpx, "post", fake_post)


def test_upload_file_returns_the_backends_answer(monkeypatch):
    def handler(request):
        assert request.url.path == "/upload"
        return httpx.Response(200, json={"document_id": 3, "filename": "notes.txt"})

    fake_backend(handler, monkeypatch)
    assert api_client.upload_file("notes.txt", b"hi") == {
        "document_id": 3,
        "filename": "notes.txt",
    }


def test_error_message_shows_the_backends_detail():
    request = httpx.Request("POST", "http://x/upload")
    response = httpx.Response(
        400,
        json={"detail": "Cannot load 'x.pdf': expected a .txt or .md file"},
        request=request,
    )
    error = httpx.HTTPStatusError("bad", request=request, response=response)
    assert "expected a .txt or .md" in api_client.error_message(error)


def test_error_message_when_backend_is_down():
    error = httpx.ConnectError("nope")
    assert "Can't reach the backend" in api_client.error_message(error)
