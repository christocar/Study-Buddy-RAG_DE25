# pipeline.py script
# One file goes in, chunks are stored in postgres and vectors in LanceDB
# Code: English
# Comments: English

"""
Ingestion pipeline.

Who calls it: POST /upload-endpoint through ingest_file (ticket #35)
AND POST /youtube (Ticket #50) through ingest_document.
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
from study_buddy.models import Document
from study_buddy.storage.postgres import get_connection, save_document
from study_buddy.storage.vector_store import get_vector_db, save_vectors


# Function to ingest a complete and finished Document
def ingest_document(document: Document) -> int:
    """
    Runs a Document through chunking, embedding, saving and then
    returns the documents id.

    Raises ValueError if the text is too short for a single chunk.

    (Less than MIN_SECTION_CHARS constant)
    """
    # Step 2: Document --> Chunks
    # In the chunk_index order (0, 1, 2, ..., 69, etc)
    chunks = chunk_document(document)

    # Loader REFUSES an empty file.
    # text under MIN_SECTION_CHARS constant still gives 0 chunks.
    # Stops here before the API call and the database
    if not chunks:
        raise ValueError(
            f"Can't ingest: {document.filename}. It contains too little text to search."
        )

    # Step 3: One vector per chunk, embed_texts keeps the order of the texts
    # This way, vectors[i] will belong to chunks[i]
    texts = [chunk.content for chunk in chunks]
    vectors = embed_texts(get_embedding_client(), texts)

    # Step 4: SAVE TO THE TRUTH FIRST(postgres).
    with get_connection() as conn:
        document_id, chunk_ids = save_document(conn, document, chunks)

    # Step 5: LanceDB under the ids Postgres just gave out.
    save_vectors(get_vector_db(), chunk_ids, vectors)

    return document_id


# Function to ingest files.
def ingest_file(filename: str, data: bytes) -> int:
    """
    Runs one file through the whole pipeline and return the documents id.

    Raises a ValueError if the loader refuses the file, or if the text is too
    short to give a single chunk (less than MIN_SECTION_CHARS constant).
    """
    # Step 1: File --> Document, then the rest of the way in ingest_document
    document = load_text_file(filename, data)
    return ingest_document(document)
