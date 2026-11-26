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
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from study_buddy.models import Chunk, Document, Source


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


def read_chunks_by_ids(conn: psycopg.Connection, chunk_ids: list[int]) -> list[Source]:
    """
    Read chunks back by id. Returns one Source per chunk, with the chunk's
    content and source_location and the filename of its document.

    Called by Retrieval, right after the LanceDB search. LanceDB gives the ids
    closest first, and the sources dropdown shows them in that order, so the
    result is in the SAME order as chunk_ids.

    An id that does not exist in Postgres is skipped, so the result can be
    shorter than chunk_ids. That can happen when LanceDB has a vector without a
    chunk (phase 3 reconciliation finds those). An id that is asked for twice
    comes back once, at its first place. An empty list gives an empty list.
    """
    if not chunk_ids:
        return []

    # filename lives in documents, not in chunks, so the two tables are joined.
    # ANY(%s) takes the whole list as one parameter. The AS names must match
    # the field names of Source, because class_row(Source) builds a Source
    # straight from each row. psycopg already turns JSONB into a dict and NULL
    # into None, which is what Source.source_location expects.
    with conn.cursor(row_factory=class_row(Source)) as cur:
        sources = cur.execute(
            "SELECT c.id AS chunk_id, d.filename, c.source_location, c.content "
            "FROM chunks AS c JOIN documents AS d ON d.id = c.document_id "
            "WHERE c.id = ANY(%s)",
            (chunk_ids,),
        ).fetchall()

    # SQL gives no promise about row order, so put the Sources back in the
    # order of chunk_ids. dict.fromkeys keeps the first place of each id.
    by_id = {source.chunk_id: source for source in sources}
    return [
        by_id[chunk_id] for chunk_id in dict.fromkeys(chunk_ids) if chunk_id in by_id
    ]