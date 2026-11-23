# uv guide: Study Buddy
*Johnny. Last updated 2026-11-22. Same setup as in the Data warehouse lab. The commands are tested against the repo with uv 0.12 and 0.13.*

Purpose: how we add packages, keep the environment in sync and get out of the most common uv errors. Where the files live is in the repo structure. This is the guide for everyday use.

## TL;DR

**We don't write `pyproject.toml` by hand.** It grows with `uv add`. `pyproject.toml` is the **floor** (what we need, at least version X). `uv.lock` is the **photograph** (exactly what we have). Both are always committed in the same commit. After every `git pull`: `uv sync`. And never `uv pip install`, it only installs on your machine and writes nothing in either file. Works on one computer out of four.

**Every package belongs to a group.** The groups control what each Docker container installs, so a package in the wrong group is missing in the container even though everything works locally.

**Jump straight to:**

1. [The groups](#the-groups)
2. [Every day](#every-day)
3. [How the groups carry Docker](#how-the-groups-carry-docker)
4. [The panic emergency](#the-panic-emergency)

## The groups

| Group | Contains now | Installed in |
|---|---|---|
| `backend` | FastAPI, LanceDB, psycopg, PydanticAI, pypdf | the backend container |
| `frontend` | Streamlit, httpx | the frontend container |
| `dev` | ruff, pytest, ipykernel | only on your computer and in CI |

**Which group?** The group for the container where the code runs. Everything that is imported in `ingestion/`, `storage/`, `qa/` or `api/` belongs to `backend`. Everything in `frontend/` belongs to `frontend`. Tools that only run on your computer or in CI belong to `dev`.

**If both containers need the same package:** add it to both groups. The lock file still gives the same version everywhere.

Locally, `uv sync` installs all groups, because `pyproject.toml` has `default-groups = "all"`. Python 3.13 is locked in both `.python-version` and `pyproject.toml`, and if it is missing on your computer uv fetches it itself.

## Every day

```bash
uv sync                                    # after every git pull: install what someone else has added
uv add --group backend <package>           # new package, in your branch
uv add --dev <package>                     # --dev is shorthand for --group dev
uv remove --group backend <package>        # remove, from the same group it was added to
uv run python scratch/johnny/test.py       # run with the project's Python and packages
uv run --env-file .env python scratch/johnny/test.py   # same, with the keys in .env loaded
```

**A new package is its own commit**, with both files:

```bash
git add pyproject.toml uv.lock
git commit -m "chore(deps): add tiktoken to backend"
```

**An extra to a package that already exists:** `uv add --group backend "pydantic-ai-slim[cohere]"`. uv adds `cohere` among the extras that are already there, the old ones don't disappear. The quotes are needed for the square brackets.

**If you remove from the wrong group** uv just says the package isn't there. Check in `pyproject.toml` which group it is in.

## How the groups carry Docker

```text
pyproject.toml + uv.lock (one photograph for the whole repo)
   │
   ├─ Dockerfile.backend    uv sync --locked --no-default-groups --group backend     94 packages
   │
   ├─ Dockerfile.frontend   uv sync --locked --no-default-groups --group frontend    37 packages
   │
   └─ your computer and CI  uv sync                                                  134 packages
```

Tested against the repo: the frontend group installs 37 packages and none of FastAPI, LanceDB, psycopg or Pydantic. The backend group has neither Streamlit, ruff nor pytest. The same lock file gives the same versions in both containers and on your computer. `--locked` stops the build if `uv.lock` doesn't match `pyproject.toml`, instead of quietly re-resolving the versions.

## The panic emergency

**`ModuleNotFoundError` after `git pull`.** Someone has added a package. `uv sync`.

**`ModuleNotFoundError: No module named 'study_buddy'`.** The package is not installed in the environment. Run `uv sync` from the repo root. If you run plain `python` instead of `uv run python` you are using the wrong Python.

**`streamlit: command not found`** (or `pytest`, `ruff`). You are not standing in the project's environment. Run with `uv run streamlit ...`, or activate the environment: `source .venv/Scripts/activate` in Git Bash, `.venv\Scripts\activate` in PowerShell, `source .venv/bin/activate` on Mac.

**Error about a missing key**, like `ANTHROPIC_API_KEY`. You forgot `--env-file .env`, or the line is missing in your `.env`. Compare with `.env.example`.

**`No solution found when resolving dependencies`.** The package you added clashes with another, since all groups share the same lock file. Read the error **from the bottom up**: the last line says which two requirements clash.

**`uv.lock` changed more than expected.** A couple of lines in the file change the first time someone with a newer uv runs `uv add`, among them `revision` at the top. Harmless, tested both ways between uv 0.12 and 0.13. Commit it too.

**Conflict in `uv.lock`** during a rebase (two people added packages in the same group). Don't fix `uv.lock` by hand and **never** delete it, then all versions lose their anchors at once. Take main's photograph and re-photograph:

```bash
git checkout origin/main -- uv.lock     # main's version of uv.lock
# resolve the conflict in pyproject.toml by hand: keep both packages
uv lock                                 # new photograph with both
git add pyproject.toml uv.lock
git rebase --continue
```

If you added packages in different groups there is usually no conflict at all. Git merges the files itself, and the lock file holds (tested).

**Sources:** [uv: dependency groups](https://docs.astral.sh/uv/concepts/projects/dependencies/) · [uv: locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) · [uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/)
