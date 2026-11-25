# conftest.py - Fixtures that more than one test file can use
# Code: Help with Claude but I made sure I understand the logic.


"""
pytest finds this file by itself, so a test just names the fixture as a parameter.

pg_conn: a connection to the Postgres in docker compose, for the tests of
tickets #26 and #27. Everything a test does is rolled back at the end, so no
rows are left in the local database.

CI has no Postgres and no POSTGRES_HOST, so these tests are skipped there.
"""

import os

import pytest

from study_buddy.storage.postgres import get_connection


@pytest.fixture
def pg_conn():
    # POSTGRES_HOST only exists when you run with --env-file. In CI it does not.
    if not os.environ.get("POSTGRES_HOST"):
        pytest.skip(
            "POSTGRES_HOST is not set, so there is no Postgres to test against. "
            "Run: uv run --env-file .env pytest"
        )

    # Two contexts in one line, opened left to right: first the connection,
    # then a transaction on it. force_rollback=True undoes everything when the
    # block ends, even if the test passed. save_document's own block then becomes a savepoint inside it.
    with get_connection() as conn, conn.transaction(force_rollback=True):
        # yield hands the connection to the test. The code after it (the end
        # of the with block) runs when the test is done.
        yield conn
