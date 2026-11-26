"""The only place the frontend talks to the backend. Every page calls these functions."""

import os

import httpx

# in docker this becomes http://backend:8000, locally it's localhost
API_URL = os.getenv("API_URL", "http://localhost:8000")


def check_health() -> dict:
    response = httpx.get(f"{API_URL}/health", timeout=5)
    response.raise_for_status()
    return response.json()


def upload_file(filename: str, content: bytes) -> dict:
    # ingestion can take a while (chunking + embeddings), so a longer timeout
    response = httpx.post(
        f"{API_URL}/upload", files={"file": (filename, content)}, timeout=120
    )
    response.raise_for_status()
    return response.json()


def error_message(error: httpx.HTTPError) -> str:
    # show the backend's own message ("Cannot load ...: the file is empty.") if there is one
    if isinstance(error, httpx.HTTPStatusError):
        try:
            return error.response.json()["detail"]
        except (ValueError, KeyError):
            return f"Backend error {error.response.status_code}"
    return f"Can't reach the backend at {API_URL}"
