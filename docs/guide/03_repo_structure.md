# Repo structure: Study Buddy
*Johnny. Last updated 2026-11-22. Same setup as in the Data warehouse lab. The tree shows the repo after PR 2, plus what comes in phase 0.*

Purpose: where each file lives in the repo, and why it lives exactly there. The foundation is already in PR 2, so this is a map and not a build instruction.

## TL;DR

**One package, one lock file, one `.env`.** All Python code lives in the package `src/study_buddy/`, and each track has its own folder there. `uv sync` installs the package, so `from study_buddy.storage import ...` works the same from FastAPI, from a test and from a script in `scratch/`. All secrets are in `.env`, which is never committed.

**Two rules to remember:** Streamlit only speaks HTTP with the API and imports nothing from the other tracks. And the folder `src/study_buddy/` must never be removed, because it is the package.

**Jump straight to:**

1. [The tree](#the-tree)
2. [Which track lives where](#which-track-lives-where)
3. [Who may import what](#who-may-import-what)
4. [Secrets in .env](#secrets-in-env)
5. [scratch/](#scratch)
6. [Traps in .gitignore](#traps-in-gitignore)
7. [To decide at the meeting](#to-decide-at-the-meeting)

## The tree

What is marked *phase 0* doesn't exist yet. What is marked *proposal* is decided at the meeting.

```text
Study-Buddy-RAG_DE25/
├── src/study_buddy/            # The package. uv sync installs it, so the import works from anywhere
│   ├── __init__.py             # EMPTY. See "Who may import what"
│   ├── models.py               # Phase 0: the Pydantic models that all tracks build against (proposal)
│   ├── ingestion/              # Ingestion: extraction, chunking, embedding
│   │   └── loaders/            # One loader per file type: .txt and .md first, then PDF and YouTube
│   ├── storage/                # Storage: Postgres and LanceDB
│   ├── qa/                     # Retrieval & Generation: retrieval and the agent
│   ├── api/                    # FastAPI
│   │   ├── main.py             # Phase 0: app shell with GET /health. Collects the endpoint files below
│   │   ├── upload.py           # POST /upload, written by Ingestion (proposal)
│   │   ├── documents.py        # GET /documents, written by Storage (proposal)
│   │   └── ask.py              # POST /ask, written by Retrieval & Generation (proposal)
│   └── frontend/               # Streamlit
├── sql/                        # Phase 0: schema.sql with the tables documents and chunks
├── tests/                      # pytest. test_smoke.py keeps CI green until real tests exist
├── docker/                     # Phase 0: Dockerfile.backend and Dockerfile.frontend
├── docs/                       # quick_commands.md, and the guides when they are translated to English
├── scratch/                    # IGNORED. One subfolder per person
├── .github/workflows/ci.yml    # CI: ruff and pytest on every PR and after every merge to main
├── docker-compose.yml          # Phase 0: backend, frontend and Postgres
├── .env.example                # The names without values. Copy to .env
├── .gitattributes              # LF line endings in all text files, regardless of which OS wrote them
├── .gitignore
├── .python-version             # 3.13
├── pyproject.toml              # One package, the groups backend, frontend and dev
├── uv.lock
└── README.md
```

## Which track lives where

```text
Ingestion                ingestion/    api/upload.py
Storage                  storage/      sql/       api/documents.py
Retrieval & Generation   qa/           api/ask.py
Frontend & Ops           frontend/     docker/    .github/    api/main.py
```

- **Ingestion:** one loader per file type in `loaders/`. All loaders hand over the same `Document`, so chunking never needs to know whether the text came from a PDF or a video. The embedding function also lives here.
- **Storage:** `sql/schema.sql` creates the tables `documents` and `chunks`. The code that writes and reads them lives in `storage/`, together with the LanceDB table.
- **Retrieval & Generation:** retrieval turns the question into a vector with Ingestion's embedding function, the same function and the same model. Then it fetches the nearest chunks from Storage and gives them to the agent.
- **Frontend & Ops:** the Streamlit app in `frontend/`, the Dockerfiles in `docker/`, CI in `.github/` and the app shell in `api/main.py`.

**An endpoint is thin.** It receives the call, calls the track's function and sends back the answer. The logic lives in the track's folder, not in `api/`. Then it can be tested without starting FastAPI.

## Who may import what

```text
frontend/ ──HTTP──► api/ ──► ingestion/ ──► storage/
                    api/ ──► qa/ ─────────► storage/
                             qa/ ─────────► ingestion/   (embedding function)
```

The arrow means "imports from", and it only goes one way. `storage/` never imports from `ingestion/` or `qa/`, and nobody imports from `api/`.

**Why frontend/ imports nothing.** The frontend container only installs the group `frontend`, that is Streamlit and httpx. If a Streamlit page imports something from `storage/`, psycopg comes along, and psycopg is not in the container. On your computer `uv sync` has installed all groups, so no error shows there. It only crashes in the container.

**That is why `src/study_buddy/__init__.py` is empty.** Python runs that file every time anything in the package is imported, also `study_buddy.frontend`. If there is an import of `storage` there, the frontend container pulls in psycopg anyway. The same goes for `__init__.py` in every track folder.

Until phase 2 the rules are an agreement. In phase 2 we add import-linter to CI, so that an arrow in the wrong direction raises an alarm already in the PR.

## Secrets in .env

`.env.example` is checked in and has the names without values. Copy it to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Name | Used for |
|---|---|
| `ANTHROPIC_API_KEY` | Claude |
| `NVIDIA_API_KEY` | NVIDIA build |
| `LOGFIRE_TOKEN` | Tracing in Logfire |

The Postgres names come with Docker compose in phase 0, and the embedding model gets its names when it is chosen.

**A new name is added to `.env.example` in the same PR as the code that reads it.** Otherwise the next person crashes on a key they didn't know they needed.

The frontend needs no key at all, only the address of the API.

## scratch/

Your scrap space: a test of a loader, an API call, a notebook you don't want to show anyone. Everything in `scratch/` except `.gitkeep` is ignored by git, so it only exists on your computer.

- Make your own subfolder, `scratch/johnny/`, so that no file names clash.
- The package is installed, so `from study_buddy.ingestion.loaders import ...` works here too. Try a function without touching the real code.
- Run with `.env` loaded: `uv run --env-file .env python scratch/johnny/test_loader.py`
- **Never name a script after a package.** Python looks first in the folder where the script lives. `scratch/johnny/lancedb.py` that does `import lancedb` imports itself instead of LanceDB, and the error message says nothing about why.
- If something becomes worth keeping, you move it to `src/` or `tests/` in its own branch.

## Traps in .gitignore

`.gitignore` is GitHub's Python template at the top and our own block below. The duplicates between them do no harm.

**1. GitHub's template ignores certain folder names anywhere in the repo.** `lib/`, `downloads/`, `build/` and `env/` are ignored at all levels, not just in the root. A folder `ingestion/downloads/` for YouTube transcripts would never come along to GitHub, and git says nothing. Tested with `git check-ignore`. Choose another name.

**2. Ignore folders, not file types.** The example files for the tests are .txt, .md and .pdf. If we ignore `*.pdf` everywhere they only exist on the computer that created them. That is why `data/` and `scratch/` are ignored as folders, and only heavy formats like `*.parquet` and `*.zip` are ignored everywhere.

**3. You can't make an exception for a file in a folder that is already ignored.** That is why it says `scratch/*` with a star and not `scratch/`. The star ignores the contents but not the folder itself, and then git finds the exception `!scratch/.gitkeep`. The same goes for `data/*` and `.vscode/*`.

**4. `.gitignore` doesn't affect files git already tracks.** If `.env` has been committed once, it doesn't help that it is in `.gitignore`. Stop tracking it, but keep the file on your computer:

```bash
git rm --cached .env
git commit -m "chore(git): stop tracking .env"
```

If the file has managed to be pushed, the key is burned anyway. Replace it immediately and tell us in Discord.

**Why doesn't my file show up?**

```bash
git check-ignore -v src/study_buddy/ingestion/downloads/a.txt   # which line in .gitignore hides the file?
git status --ignored                                            # everything that is ignored right now
```

`check-ignore -v` answers with file, line number and pattern. No output means the file is not ignored, and then the problem is something else (have you run `git add`?).

## To decide at the meeting

- [ ] **Where do the Pydantic models live?** Proposal: `src/study_buddy/models.py`, one file in the package's root. All tracks in the backend import it, and it only imports Pydantic. If it lives in `storage/`, Ingestion has to import from Storage just to get the shape of a `Document`.
- [ ] **Where does LanceDB live locally?** Proposal: in `data/lancedb/`. `.gitignore` already ignores everything in `data/`, but the folder doesn't exist in the repo yet. `data/.gitkeep` is added in the same PR as the first code that writes there. In compose, LanceDB and Postgres live in volumes.
- [ ] **What are the tests called?** Proposal: all test files directly in `tests/`, with the track first in the name: `test_ingestion_chunking.py`, `test_storage_postgres.py`. Two files that are both called `test_models.py` in different subfolders stop pytest before any test has run (tested). Small example files that we have written ourselves go in `tests/fixtures/`.

**Sources:** [uv: project structure](https://docs.astral.sh/uv/concepts/projects/init/) · [uv: dependency groups](https://docs.astral.sh/uv/concepts/projects/dependencies/) · [Python: where import looks](https://docs.python.org/3/library/sys_path_init.html) · [pytest: import modes](https://docs.pytest.org/en/stable/explanation/pythonpath.html) · [git: gitignore](https://git-scm.com/docs/gitignore) · [GitHub's Python template](https://github.com/github/gitignore/blob/main/Python.gitignore)
