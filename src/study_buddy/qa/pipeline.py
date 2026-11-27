"""
The question chain: a question goes in, an Answer with sources comes out.

Who calls it: POST /ask (ticket #31). The endpoint stays thin and only
handles HTTP. The work happens here, so it can be tested without FastAPI.

1: retrieve() finds the nearest chunks (ticket #29)
2: generate() answers from those chunks only (ticket #30)

answer_question opens its own connections, like ingest_file does on the
upload side, so the caller only passes the question. The Postgres connection
is closed before the agent is called, so it is not held open while the
model writes its answer.
"""

from study_buddy.embedding.embed import get_embedding_client
from study_buddy.models import Answer
from study_buddy.qa.generation import generate
from study_buddy.qa.retrieval import DEFAULT_TOP_K, retrieve
from study_buddy.storage.postgres import get_connection
from study_buddy.storage.vector_store import get_vector_db


def answer_question(question: str, top_k: int = DEFAULT_TOP_K) -> Answer:
    """
    Answer one question from the uploaded material.

    Raises ValueError for an empty question (from retrieve). With no chunks
    found, the Answer says it doesn't know and has no sources.
    """
    with get_connection() as conn:
        sources = retrieve(
            question,
            client=get_embedding_client(),
            db=get_vector_db(),
            conn=conn,
            top_k=top_k,
        )

    return generate(question, sources)
