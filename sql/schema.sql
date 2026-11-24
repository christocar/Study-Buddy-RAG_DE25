-- Postgres runs this file once, when the database volume is empty.
-- Change it later and you must reset the volume: docker compose down -v

CREATE TABLE IF NOT EXISTS documents (
    id            SERIAL PRIMARY KEY,
    filename      VARCHAR(255) NOT NULL,
    source_type   VARCHAR(20)  NOT NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT now(),
    status        VARCHAR(20),
    error_message TEXT,
    file_hash     VARCHAR(64)  UNIQUE
);

CREATE TABLE IF NOT EXISTS chunks (
    id              SERIAL PRIMARY KEY,
    document_id     INTEGER   NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chunk_index     INTEGER   NOT NULL,
    content         TEXT      NOT NULL,
    source_location JSONB,
    created_at      TIMESTAMP NOT NULL DEFAULT now(),
    char_count      INTEGER,
    UNIQUE (document_id, chunk_index)
);

/*
ON DELETE CASCADE - If a document is deleted, its chunks are deleted automatically. Without it, Postgres refuses to delete a document that still has chunks.
*/