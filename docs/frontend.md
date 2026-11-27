# Frontend: upload and ask

_Indira · #35, #32, #33_

```text
UPLOAD  1_Upload.py → api_client.upload_file() → POST /upload → ingest_file()
ASK     2_Ask.py    → api_client.ask()         → POST /ask    → retrieve() → generate()
```

## Rules

- **All backend calls go in `api_client.py`.** Pages never use `httpx` themselves.
- **Endpoints with blocking work are plain `def`**, not `async def`, so the backend doesn't freeze.
- **Pages read plain dicts**, not `models.py`. The frontend container has no Pydantic.
- **New page?** Put it in `frontend/pages/`. The number sets the sidebar order.

## Known issue

Uploading the same file twice gives duplicate sources (no `file_hash` yet, phase 2). Reset with `docker compose down -v`.

## Try it

```bash
docker compose up --build
```

http://localhost:8501 → **Upload** a .txt → **Ask** about it. Needs your keys in `.env`.
