# Upload flow: `/upload` + upload page

_Indira · #35 POST /upload and #32 Upload page_

A file goes from the browser, through FastAPI and into the ingestion pipeline. This doc shows which part does what.

## The flow

```text
You pick notes.txt in Streamlit
      │
      ▼
frontend/pages/1_Upload.py     the page with the file picker + Upload button
      │  upload_file(name, bytes)
      ▼
frontend/api_client.py         the ONLY file in the frontend that calls the backend
      │  HTTP POST /upload
      ▼
api/upload.py                  thin endpoint: takes the file, calls the pipeline
      │  ingest_file(filename, data)
      ▼
ingestion/pipeline.py          Johnny's pipeline: load → chunk → embed → Postgres + LanceDB
      │
      ▼
{"document_id": 1, "filename": "notes.txt"}  →  the page shows "Uploaded"
```

## #35 POST /upload (`api/upload.py`)

- **Thin on purpose.** It reads the file and hands it to `ingest_file()`. All the real work lives in the pipeline.
- **A plain `def`, not `async def`.** The pipeline is blocking (embedding call, Postgres, LanceDB). Inside `async def` it would freeze the whole backend during an upload: Johnny measured `/health` waiting 2.7 s. With `def`, FastAPI runs the endpoint in a thread and the rest of the backend stays responsive. That's why it reads the file with `file.file.read()`, not `await file.read()`.
- **No repeated validation.** File type, empty file and UTF-8 are already checked by Aira's loader. If the pipeline refuses a file, it raises `ValueError`, and `/upload` turns that into a **400** with the pipeline's own reason.
- **Answers with:** `{"document_id": 1, "filename": "notes.txt"}`
- Included in `api/main.py` with `app.include_router(upload.router)`.

| You send                                          | You get                                                                          |
| ------------------------------------------------- | -------------------------------------------------------------------------------- |
| a `.txt` / `.md` with real text                   | `200` + `document_id`                                                            |
| `.pdf`, an empty file, too little text, not UTF-8 | `400` + the reason, e.g. `"Cannot load 'x.pdf': expected a .txt or .md file..."` |

## #32 Upload page (`frontend/`)

- **`api_client.py`**: every call to the backend lives here (`check_health()`, `upload_file()`, `error_message()`). Pages never use `httpx` themselves. One place for `API_URL`, one place for error handling. The chat page adds `ask()` here later.
- **`pages/1_Upload.py`**: file picker (only `.txt` / `.md`), an Upload button and a spinner. It shows the `document_id` on success, or the backend's reason in red.
- **`app.py`**: the home page. It now uses `api_client` too, and points to Upload/Chat in the sidebar.
- Streamlit turns every file in `pages/` into a page in the sidebar automatically.

## Tests (no database or API key needed)

- **`tests/test_api_upload.py`**: uses `monkeypatch` to swap `ingest_file` for a fake. The happy path checks that the file really reaches the pipeline as `("notes.txt", b"hello")` and that the `document_id` comes back. The second test checks that a `ValueError` becomes a 400 with the reason.
- **`tests/test_frontend_api_client.py`**: uses `httpx.MockTransport` as a fake backend, then checks `upload_file()` and the error messages.

The real pipeline has its own tests. These only test the endpoint and the page's calls.

## Try it yourself

```bash
docker compose up --build
```

- **Page:** http://localhost:8501 → **Upload** → pick a `.txt` → **Upload**
- **API only:** http://localhost:8000/docs → **POST /upload** → _Try it out_

You need your keys in `.env`, because the real pipeline calls the embedding API. Use a file with a few sentences: a very short text gives no chunks, and you get a 400.

## Good to know

- **Phase 1 = `.txt` and `.md` only.** PDF comes in phase 2. The loader router will pick the right loader, and `/upload` doesn't need to change.
- **The same file uploaded twice becomes two documents.** Nothing writes `file_hash` yet, so there's no duplicate check. That's a phase 2 issue.
- **Blocking code in an endpoint → plain `def`.** The same rule applies to `POST /ask`, since `generate()` uses `run_sync`.
- **Adding your own endpoint?** Copy the pattern: your own file in `api/`, a `router = APIRouter()`, and one `include_router` line in `main.py`.
- **Adding a frontend call?** Put it in `api_client.py`, not in the page.
