"""
The vectors in LanceDB: save them under their chunk ids, and search for the nearest.

LanceDB holds only chunk_id and the vector. Everything else about a chunk
(content, filename, source_location) lives in Postgres, so each fact has one
home. Retrieval searches here first and then reads the chunks with
read_chunks_by_ids() in storage/postgres.py.

The folder comes from LANCEDB_PATH in the environment, data/lancedb by default.
Tests pass their own temporary folder, so they never touch your real vectors.
"""

import os

import lancedb
import pyarrow as pa

from study_buddy.embedding.constants import EMBEDDING_DIM

DEFAULT_LANCEDB_PATH = "data/lancedb"
TABLE_NAME = "chunk_vectors"

# A fixed length on the vector column: LanceDB refuses a vector of the wrong size.
SCHEMA = pa.schema(
    [
        pa.field("chunk_id", pa.int64()),
        pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
    ]
)


def get_vector_db(path: str | None = None) -> lancedb.DBConnection:
    """Open the LanceDB folder. LanceDB creates it if it does not exist."""
    return lancedb.connect(path or os.getenv("LANCEDB_PATH", DEFAULT_LANCEDB_PATH))


def _get_table(db: lancedb.DBConnection) -> lancedb.table.Table:
    """Open the table, or create it empty the first time."""
    return db.create_table(TABLE_NAME, schema=SCHEMA, exist_ok=True)


def _check_dim(vector: list[float]) -> None:
    if len(vector) != EMBEDDING_DIM:
        raise ValueError(
            f"Vector has {len(vector)} numbers, expected EMBEDDING_DIM={EMBEDDING_DIM}."
        )


def save_vectors(
    db: lancedb.DBConnection, chunk_ids: list[int], vectors: list[list[float]]
) -> None:
    """
    Save one vector per chunk id. chunk_ids[0] belongs to vectors[0], and so on,
    which is the order save_document() in storage/postgres.py returns the ids in.

    Raises ValueError if the two lists have different lengths, or if a vector
    is not EMBEDDING_DIM long. An empty list saves nothing.
    """
    if len(chunk_ids) != len(vectors):
        raise ValueError(f"Got {len(chunk_ids)} chunk ids but {len(vectors)} vectors.")
    if not chunk_ids:
        return

    for vector in vectors:
        _check_dim(vector)

    rows = [
        {"chunk_id": chunk_id, "vector": vector}
        for chunk_id, vector in zip(chunk_ids, vectors)
    ]
    _get_table(db).add(rows)


def search_vectors(
    db: lancedb.DBConnection, vector: list[float], limit: int = 5
) -> list[int]:
    """
    Return the chunk ids of the vectors nearest to `vector`, closest first.

    Cosine distance compares the direction of the vectors, not their length,
    which is the usual choice for text embeddings. An empty table gives an
    empty list.
    """
    _check_dim(vector)
    rows = (
        _get_table(db)
        .search(vector)
        .distance_type("cosine")
        .limit(limit)
        .select(["chunk_id"])
        .to_list()
    )
    return [row["chunk_id"] for row in rows]
