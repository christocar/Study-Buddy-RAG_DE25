# Tasks: Study Buddy
*Johnny. Last updated 2026-11-22. Basis for issues on the board. Archived when the board is filled.*

One row is one task and becomes one issue, with labels for phase and track. Which phase does what is in `00_roadmap.md`.

**Jump straight to:**

1. [Ingestion](#ingestion)
2. [Storage](#storage)
3. [Retrieval & Generation](#retrieval--generation)
4. [Frontend & Ops](#frontend--ops)

## Ingestion

*The folder `ingestion/` and the endpoint `POST /upload`.*

| Phase | Task | Done when |
|---|---|---|
| 0 | **Embedding model**: choose and test | The model, max number of tokens and vector dimension are decided |
| 0 | **Embedding function** | Texts in, vectors out. Retrieval can call it |
| 1 | **Extraction**: loader for .txt and .md | A file becomes a `Document` |
| 1 | **Chunking** per section | A test shows that no chunk spans two sections |
| 1 | **Ingestion pipeline**: file, chunks, vectors, into Storage | A .txt ends up in Postgres and LanceDB with the same `chunk_id` |
| 1 | **Endpoint** `POST /upload` | File in, document id out |
| 2 | **Extraction**: PDF loader page by page | Every chunk knows its page |
| 2 | **Loader router**: the right loader per file type | .txt, .md and .pdf go through the same `/upload` |
| 3 | **Extraction**: YouTube loader with cached transcripts, .txt as fallback | A link becomes a `Document`, and every chunk knows its second |
| 3 | **Background ingestion** | `/upload` responds immediately, and the ingestion continues in the background |

## Storage

*The folders `storage/` and `sql/`, and the endpoint `GET /documents`.*

| Phase | Task | Done when |
|---|---|---|
| 0 | **The Pydantic models** for documents, chunks and answers, and **`schema.sql`** | Merged, reviewed by Ingestion and Retrieval & Generation |
| 1 | **Postgres**: insert and select with `%s` parameters | Save documents and chunks, fetch chunks by id. Tested against Postgres in compose |
| 1 | **Vector store**: the LanceDB table with insert and vector search | One vector in, nearest `chunk_id` out |
| 2 | **Document status**: processing, ready, failed | Every document has a status |
| 2 | **Endpoint** `GET /documents` | The list of documents and their status |
| 3 | **Reconciliation** between Postgres and LanceDB | Shows documents without chunks and vectors without a chunk |

## Retrieval & Generation

*The folder `qa/` and the endpoint `POST /ask`.*

| Phase | Task | Done when |
|---|---|---|
| 0 | **LLM**: choose model | Chosen, and the key's name is in `.env.example` |
| 0 | **Agent**: hello world in PydanticAI | Answers a question locally |
| 1 | **Retrieval**: the question becomes a vector, the nearest chunks are fetched | A question gives chunks with text |
| 1 | **Generation**: the agent answers only from the chunks, with sources | Says it doesn't know when the chunks lack the answer |
| 1 | **Endpoint** `POST /ask` | Question in, answer and sources out |
| 2 | **Prompt versioning** | The prompts are versioned, not hardcoded in the code |
| 2 | **Tracing** with Logfire on FastAPI and PydanticAI | A question shows up as a trace in Logfire |
| 3 | **Evals**: golden set with 15-20 questions and answer key | The questions can be run and give a result |
| 3 | **LLM-as-a-judge** | The judge checks that the answer matches the chunks |
| 3 | **Quiz** and **timestamp links** to the right second in a video | If time allows |

## Frontend & Ops

*The folders `frontend/`, `docker/` and `.github/`, and the app shell in `api/main.py`.*

| Phase | Task | Done when |
|---|---|---|
| 0 | **Repo**, `pyproject` with groups and **CI** with ruff and pytest | Done in PR 2 |
| 0 | **Kanban board** with labels for phase and track | Phase 1 tasks are on the board |
| 0 | **Docker compose**: backend, frontend and Postgres | `docker compose up` starts all three for all four of us |
| 0 | **App shell**: FastAPI with `GET /health` | `/health` responds in the container |
| 0 | **Way of working** | Approved by all four |
| 1 | **Streamlit**: upload | The file reaches `/upload` |
| 1 | **Streamlit**: chat and sources dropdown | The answer is shown, and under it the document, location and text for each chunk |
| 1 | **YouTube test day**, locally and from Azure | We know whether YouTube lets calls through from Azure |
| 2 | **README v1** with screenshots | Someone outside the group can start the app |
| 2 | **Import-linter** in CI | CI raises an alarm when a track imports from another where we have said it must not |
| 3 | **CD** with GitHub Actions | A merge to `main` deploys |
| 3 | **Deployment** in Azure with a protected public URL | The app can be reached, but not by just anyone |
| 3 | **Quiz page** | If time allows |
