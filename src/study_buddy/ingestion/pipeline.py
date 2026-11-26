# pipeline.py script
# One file goes in, chunks are stored in postgres and vectors in LanceDB
# Code: English
# Comments: English

"""
Ingestion pipeline.

Who calls it: POST /upload-endpoint (ticket #35) and NOTHING else.
This is the ONLY place that writes to BOTH databases.

The order of the entire flow is:
1: load the file into a Document (Ticket #24)
2: cut the Document into Chunks (Ticket #25)
3: embed the chunk texts
4: save the Document and its Chunks in Postgres that hands out the ids (Ticket #26)
5: save the vectors in LanceDB under those ids (Ticket #28)

Embedding comes BEFORE postgres since the API call is the step most likely to fail
and IF it fails here then NOTHING has been saved yet. If the LanceDB write fails
AFTER postgres, then the chunks stay without vectors.

Phase 3s reconciliation will find those chunks without vectors/vectors without chunks.
"""

from study_buddy.embedding.embed import embed_texts, get_embedding_client
from study_buddy.ingestion.chunker import chunk_document
from study_buddy.ingestion.loaders.text import load_text_file
from study_buddy.storage.postgres import get_connection, save_document
from study_buddy.storage.vector_store import get_vector_db, save_vectors


# Function to ingest files.
def ingest_file(filename: str, data: bytes) -> int:
    """
    Runs one file through the whole pipeline and return the documents id.

    Raises a ValueError if the loader refuses the file, or if the text is too
    short to give a single chunk (less than MIN_SECTION_CHARS constant).
    """
    # 1 and 2: File --> Document --> Chunks
    # in the chunk_index order (0, 1, 2, ... , 69, ... ...)
    document = load_text_file(filename, data)
    chunks = chunk_document(document)

    # The loader refuses an empty file,
    # but a very short text still gives no chunks.
    # Stop here, BEFORE the API call and the database.
    if not chunks:
        raise ValueError(
            f"Cannot ingest '{filename}': contains too little text to search."
        )

    # 3: One vector per chunk. embed_texts keeps the order of the texts, so that
    # vectors[i] belongs to chunks[i].
    texts = [chunk.content for chunk in chunks]
    vectors = embed_texts(get_embedding_client(), texts)

    # 4: Postgres FIRST, since it hands out the chunk ids, in chunk_index order.
    with get_connection() as conn:
        document_id, chunk_ids = save_document(conn, document, chunks)

    # 5: Then LanceDB, under the ids Postgres just handed out.
    save_vectors(get_vector_db(), chunk_ids, vectors)

    return document_id
