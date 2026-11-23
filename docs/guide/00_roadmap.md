# Roadmap: Study Buddy
*Johnny. Last updated 2026-11-22. Draft for the group meeting Monday 23 November. The tracks build on Indira's list from 21 November.*

What we are building, and in which phase. Every task with its "done when" is in `00_tasks.md` and becomes an issue on the board.

## TL;DR

The app is a RAG chain in four tracks: **Ingestion**, **Storage**, **Retrieval & Generation** and **Frontend & Ops**.
All four build in parallel, phase by phase. After phase 1 the whole chain works: a .txt is uploaded and a question gets an answer with the right source.
Every phase after that makes the chain better.

**Jump straight to:**

1. [The flow and the tracks](#the-flow-and-the-tracks)
2. [The phases](#the-phases)
3. [To decide at the meeting](#to-decide-at-the-meeting)

## The flow and the tracks

```text
UPLOAD
  Streamlit ──file──► Ingestion ──────────────────────────────► Storage
  Frontend            extraction ─► chunking ─► embedding       Postgres: documents and chunks
                                                                LanceDB:  vectors
                                                                 │
ASK                                                              │
  Streamlit ─question─► Retrieval & Generation                   │
  Frontend              retrieval ◄──────────────────────────────┘
      ▲                 generation: the agent answers only from the chunks
      │                  │
      └─ answer + sources ┘

Ops around everything: Docker compose runs the chain, CI tests every PR, CD and Azure in phase 3.
```

| Track | What it does | Folder in the repo |
|---|---|---|
| **Ingestion** | Receives a file, pulls out the text (extraction), splits it into chunks (chunking) and turns them into vectors (embedding) | `ingestion/` |
| **Storage** | Saves documents and chunks in Postgres and the vectors in LanceDB, with the same `chunk_id` | `storage/`, `sql/` |
| **Retrieval & Generation** | Finds the chunks that are most similar to the question (retrieval) and lets the agent answer only from them, with sources (generation). R and G in RAG | `qa/` |
| **Frontend & Ops** | The Streamlit app the user sees, and everything that makes the app run: Docker, CI/CD and Azure | `frontend/`, `docker/`, `.github/` |

## The phases

| Phase | Done | Ingestion | Storage | Retrieval & Generation | Frontend & Ops |
|---|---|---|---|---|---|
| **0** | Tue 24 Nov | Choose embedding model, embedding function | The Pydantic models and `schema.sql` that all tracks build against | Choose LLM, hello world agent | Docker compose, FastAPI app shell, kanban, way of working |
| **1** | Fri 27 Nov | Loader for .txt and .md, chunking, ingestion pipeline, `/upload` | Postgres insert and select, LanceDB insert and search | Retrieval, generation with sources, `/ask` | Streamlit upload, chat with sources dropdown, YouTube test from Azure |
| **2** | Fri 4 Dec | PDF loader, loader router | Document status, `GET /documents` | Prompt versioning, tracing in Logfire | README v1, import-linter in CI |
| **3** | Tue 8 Dec | YouTube loader, background ingestion | Reconciliation between Postgres and LanceDB | Evals, LLM-as-a-judge | CD and deploy to Azure |
| **4** | From KC | Everyone: cleanup, README, slides, demo and reflection | | | |

- **After phase 0:** everyone can run `docker compose up`, the models are chosen, and the Pydantic models for documents, chunks and answers are merged. Then everyone builds against the same shape.
- **After phase 1:** a .txt or .md is uploaded, a question gets an answer, and the right chunk shows up as the source.
- **After phase 2:** PDF works too, everything runs in Docker and the README exists.
- **After phase 3:** whatever we have managed of YouTube, Logfire, evals and Azure is merged. After that, code freeze, only bug fixes.
- **Phase 4:** presentation and submission.

## To decide at the meeting

- [ ] **The tracks.** Who takes which? Proposal: everyone says their preferred track, then we adjust. I would gladly take Ingestion, where I have built chunking and ingestion before.
- [ ] **The Pydantic models and `schema.sql`.** Who writes them? Proposal: Storage, and Ingestion and Retrieval & Generation review. Merged by Tuesday at the latest, since everyone builds against them.
- [ ] **Endpoints.** Proposal: each track writes its own endpoint in its own file in `api/`, and Frontend & Ops sets up the app shell in phase 0. An endpoint is a few lines that receive the call and call the track's function, so nobody should have to wait for one person who writes all of them.
- [ ] **Labels on the board.** Proposal: phase (`phase-1`) and track (`ingestion`).
- [ ] **The dates.** Proposal: the table under [The phases](#the-phases).
- [ ] **Presentation and submission.** The dates come from KC. Proposal: we ask the same day, so we know how long phase 4 will be.

---

*Owning a track, after Indira's idea: the owner keeps track of the track's tasks and asks for help early when it is lagging. Everyone may take a task from another track, but sign up on the issue and tell the owner first. If we pair program, `Co-authored-by: Name <email>` is written last in the commit message.*
