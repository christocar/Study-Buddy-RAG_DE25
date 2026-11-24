# Good to have quick commands

Document is meant to work and be used as a quick cheatsheet for basic and quick terminal commands.

- **Formatting and linting:**
  - https://docs.astral.sh/ruff/linter/
  - https://docs.astral.sh/ruff/formatter/

```bash
uv run ruff check .
uv run ruff format --check .
```

- **Run test suite:**

```bash
uv run pytest       # For the entire suite
uv run pytest -q    # If you want to run the entire suite but not be hit with a wall of text in terminal
```

- **Run the app locally (without Docker):**
  - https://fastapi.tiangolo.com/fastapi-cli/

```bash
uv run fastapi dev src/study_buddy/api/main.py      # Backend, reloads on save. http://localhost:8000/health and /docs
uv run streamlit run src/study_buddy/frontend/app.py   # Frontend, in a second terminal. http://localhost:8501
```

- **Run the app with Docker:**
  - https://docs.docker.com/compose/reference/

```bash
cp .env.example .env          # Once. Compose needs a .env file to exist
docker compose up --build     # Build and start everything. Frontend http://localhost:8501, backend http://localhost:8000
docker compose up -d --build  # Same, but in the background so you keep your terminal
docker compose logs -f backend   # Follow the backend's logs (Ctrl+C to stop following)
docker compose ps             # What's running?
docker compose down           # Stop and remove the containers (your data volumes stay)
```
