import httpx

from study_buddy.frontend import api_client


def fake_backend(handler, monkeypatch):
    # route every httpx.post to our handler instead of a real backend
    def fake_post(url, **kwargs):
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            return client.post(url, **kwargs)

    monkeypatch.setattr(api_client.httpx, "post", fake_post)


def test_upload_file_sends_the_file(monkeypatch):
    def handler(request):
        assert request.url.path == "/upload"
        return httpx.Response(200, json={"document_id": 3, "filename": "notes.txt"})

    fake_backend(handler, monkeypatch)
    assert api_client.upload_file("notes.txt", b"hi")["document_id"] == 3


def test_ask_sends_the_question(monkeypatch):
    def handler(request):
        assert request.url.path == "/ask"
        assert request.read() == b'{"question":"What is RAG?"}'
        return httpx.Response(200, json={"answer": "RAG is...", "sources": []})

    fake_backend(handler, monkeypatch)
    assert api_client.ask("What is RAG?")["answer"] == "RAG is..."


def test_error_message_for_a_refused_file_and_a_down_backend():
    request = httpx.Request("POST", "http://x/upload")
    response = httpx.Response(
        400, json={"detail": "the file is empty"}, request=request
    )
    refused = httpx.HTTPStatusError("bad", request=request, response=response)

    assert api_client.error_message(refused) == "the file is empty"
    assert "Can't reach the backend" in api_client.error_message(httpx.ConnectError(""))
