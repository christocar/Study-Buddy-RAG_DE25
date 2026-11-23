# Good to have quick commands

Document is meant to work and be used as a quick cheatsheet for basic and quick terminal commands.

* **Formatting and linting:**
    * https://docs.astral.sh/ruff/linter/
    * https://docs.astral.sh/ruff/formatter/
```bash
uv run ruff check .
uv run ruff format --check .
```


* **Run test suite:**
```bash
uv run pytest       # For the entire suite
uv run pytest -q    # If you want to run the entire suite but not be hit with a wall of text in terminal
```

* 