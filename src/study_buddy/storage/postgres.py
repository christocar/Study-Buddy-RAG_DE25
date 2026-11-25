# postgres.py - Saves documents and chunks in Postgres, and reads chunks back
# Code: Help with Claude. I made sure I understand the logic behind this script.

"""
Everything that talks to Postgres lives in this file.

Ticket #26 adds save_document(), which is called by ingest_file() in
ingestion/pipeline.py (ticket #34). Ticket #27 adds read_chunks_by_ids(),
which Retrieval calls right after the LanceDB search.

This file imports only from study_buddy.models. storage/ never imports from
ingestion/ or qa/.
As agreed upon in meeting.
"""

import os

import psycopg
from psycopg.types.json import Jsonb

from study_buddy.models import Chunk, Document


def get_connection() -> psycopg.Connection:
    """
    Open a connection to Postgres with the POSTGRES_* values from the environment.

    The caller owns the connection. The easiest way to use it is a with block:

        with get_connection() as conn:
            ...

    When the block ends without an error, psycopg commits (saves for real).
    If there is an error, it rolls back (throws the changes away). Either way
    the connection is closed at the end.
    """
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def save_document(
    conn: psycopg.Connection, document: Document, chunks: list[Chunk]
) -> tuple[int, list[int]]:
    """
    Save a document and its chunks. Returns (document_id, chunk_ids), where
    chunk_ids are in chunk_index order: the first id belongs to chunk_index 0.

    The vectors in LanceDB are saved under these chunk_ids, so the pipeline
    (ingest_file, ticket #34) needs them.

    All or nothing: the INSERTs run inside one transaction. If one fails, the
    document row is undone too. On a fresh connection the block commits by
    itself when it ends without an error.

    Raises ValueError for an empty list: a document with no chunks has nothing
    to find later.
    """
    if not chunks:
        raise ValueError(f"Cannot save '{document.filename}': no chunks.")

    # Sort first, so the ids come back in chunk_index order (0, 1, 2...)
    # even if the chunks were handed over in another order.
    ordered = sorted(chunks, key=lambda chunk: chunk.chunk_index)

    with conn.transaction():
        # Values go in as %s parameters, never into the SQL string with an f-string.
        document_id = conn.execute(
            "INSERT INTO documents (filename, source_type) VALUES (%s, %s) RETURNING id",
            (document.filename, document.source_type),
        ).fetchone()[0]

        chunk_ids = []
        for chunk in ordered:
            # A Python dict must be wrapped in Jsonb. None must stay None,
            # so it becomes a real NULL and not the JSON value null.
            location = (
                Jsonb(chunk.source_location)
                if chunk.source_location is not None
                else None
            )
            chunk_id = conn.execute(
                "INSERT INTO chunks (document_id, chunk_index, content, source_location) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (document_id, chunk.chunk_index, chunk.content, location),
            ).fetchone()[0]
            chunk_ids.append(chunk_id)

    return document_id, chunk_ids
