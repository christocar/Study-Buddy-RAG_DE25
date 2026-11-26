"""
Retrieval: the question goes in, the nearest chunks come out as Sources.

Three steps, each owned by another part of the repo:

1. embed_texts() turns the question into a vector, with the SAME function and
   model the chunks went through (embedding/embed.py).
2. search_vectors() finds the nearest chunk ids in LanceDB, closest first
   (storage/vector_store.py).
3. read_chunks_by_ids() reads those chunks from Postgres and keeps the order
   (storage/postgres.py).

The caller opens the embedding client, LanceDB and the Postgres connection and
passes them in. Tests can then pass fakes, so they need no API and no Postgres.
"""

import lancedb
import psycopg
from openai import OpenAI

from study_buddy.embedding.embed import embed_texts
from study_buddy.models import Source
from study_buddy.storage.postgres import read_chunks_by_ids
from study_buddy.storage.vector_store import search_vectors

DEFAULT_TOP_K = 5


def retrieve(
    question: str,
    *,
    client: OpenAI,
    db: lancedb.DBConnection,
    conn: psycopg.Connection,
    top_k: int = DEFAULT_TOP_K,
) -> list[Source]:
    """
    Return the top_k chunks nearest to the question, closest first.

    Can return fewer than top_k: when LanceDB has fewer vectors, or when an id
    is missing in Postgres. An empty list means nothing was found, and
    Generation then says it does not know.

    Raises ValueError for an empty question, so no embedding call is wasted.
    """
    if not question.strip():
        raise ValueError("The question is empty.")

    [question_vector] = embed_texts(client, [question])
    chunk_ids = search_vectors(db, question_vector, limit=top_k)
    return read_chunks_by_ids(conn, chunk_ids)
