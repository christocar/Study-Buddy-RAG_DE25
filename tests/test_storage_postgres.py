# test_storage_postgres.py - Tests for save_document() and read_chunks_by_ids() against the real Postgres in compose
#
# These tests need Postgres. They use the pg_conn fixture from conftest.py, which
# skips them when POSTGRES_HOST is not set (CI) and rolls everything back at the end.
# Run them with: uv run --env-file .env pytest tests/test_storage_postgres.py -v

import psycopg
import pytest

from study_buddy.models import Answer, Chunk, Document, Section, Source
from study_buddy.storage.postgres import read_chunks_by_ids, save_document


# Small helpers so each test only shows what it is about
def make_document(filename="notes.txt"):
    return Document(filename=filename, source_type="txt", sections=[Section(text="x")])


def make_chunks(n):
    return [Chunk(chunk_index=i, content=f"chunk {i}") for i in range(n)]


# T1: one document id and one id per chunk come back
def test_save_returns_document_id_and_chunk_ids(pg_conn):
    document_id, chunk_ids = save_document(pg_conn, make_document(), make_chunks(3))

    assert isinstance(document_id, int)
    assert len(chunk_ids) == 3
    assert all(isinstance(chunk_id, int) for chunk_id in chunk_ids)


# T2: the rows are really in the tables
def test_rows_are_really_saved(pg_conn):
    document_id, _ = save_document(pg_conn, make_document("week1.txt"), make_chunks(2))

    doc_row = pg_conn.execute(
        "SELECT filename, source_type FROM documents WHERE id = %s", (document_id,)
    ).fetchone()
    contents = pg_conn.execute(
        "SELECT content FROM chunks WHERE document_id = %s ORDER BY chunk_index",
        (document_id,),
    ).fetchall()

    assert doc_row == ("week1.txt", "txt")
    assert contents == [("chunk 0",), ("chunk 1",)]


# T3: the id at place i belongs to the chunk with chunk_index i
def test_chunk_ids_come_back_in_chunk_index_order(pg_conn):
    _, chunk_ids = save_document(pg_conn, make_document(), make_chunks(3))

    for index, chunk_id in enumerate(chunk_ids):
        row = pg_conn.execute(
            "SELECT chunk_index FROM chunks WHERE id = %s", (chunk_id,)
        ).fetchone()
        assert row[0] == index


# T4: chunks handed over as 2, 0, 1 still give ids in the order 0, 1, 2
def test_chunks_out_of_order_still_give_ids_in_order(pg_conn):
    chunks = make_chunks(3)
    out_of_order = [chunks[2], chunks[0], chunks[1]]

    _, chunk_ids = save_document(pg_conn, make_document(), out_of_order)

    for index, chunk_id in enumerate(chunk_ids):
        row = pg_conn.execute(
            "SELECT chunk_index, content FROM chunks WHERE id = %s", (chunk_id,)
        ).fetchone()
        assert row == (index, f"chunk {index}")


# T5: {"page": 3} comes back as a dict, and None is a real NULL
def test_source_location_round_trip(pg_conn):
    chunks = [
        Chunk(chunk_index=0, content="a", source_location={"page": 3}),
        Chunk(chunk_index=1, content="b"),
    ]

    _, chunk_ids = save_document(pg_conn, make_document(), chunks)

    rows = pg_conn.execute(
        "SELECT source_location FROM chunks WHERE id = ANY(%s) ORDER BY chunk_index",
        (chunk_ids,),
    ).fetchall()
    assert rows == [({"page": 3},), (None,)]


# T6: tricky text is saved as plain text. This proves %s parameters work
def test_tricky_text_is_saved_as_plain_text(pg_conn):
    tricky = "O'Brien; DROP TABLE chunks;--"
    chunks = [Chunk(chunk_index=0, content=tricky)]

    document_id, chunk_ids = save_document(
        pg_conn, make_document("O'Brien.txt"), chunks
    )

    # If the text had been run as SQL, the chunks table would be gone
    content = pg_conn.execute(
        "SELECT content FROM chunks WHERE id = %s", (chunk_ids[0],)
    ).fetchone()[0]
    filename = pg_conn.execute(
        "SELECT filename FROM documents WHERE id = %s", (document_id,)
    ).fetchone()[0]
    assert content == tricky
    assert filename == "O'Brien.txt"


# T7: the second document's ids keep counting, but its chunk_index starts at 0
def test_second_document_keeps_counting_ids_but_restarts_chunk_index(pg_conn):
    _, first_ids = save_document(pg_conn, make_document("a.txt"), make_chunks(3))
    _, second_ids = save_document(pg_conn, make_document("b.txt"), make_chunks(3))

    assert second_ids[0] > first_ids[-1]
    row = pg_conn.execute(
        "SELECT chunk_index FROM chunks WHERE id = %s", (second_ids[0],)
    ).fetchone()
    assert row[0] == 0


# T8: a document with no chunks has nothing to find, so it is refused
def test_empty_chunk_list_is_refused(pg_conn):
    with pytest.raises(ValueError, match="no chunks"):
        save_document(pg_conn, make_document(), [])


# T9: two chunks claim the same place. Postgres refuses the second one, and the
# document row is undone too: all or nothing
def test_failure_halfway_saves_nothing(pg_conn):
    chunks = [
        Chunk(chunk_index=0, content="a"),
        Chunk(chunk_index=0, content="b"),
    ]

    with pytest.raises(psycopg.errors.UniqueViolation):
        save_document(pg_conn, make_document("broken.txt"), chunks)

    count = pg_conn.execute(
        "SELECT count(*) FROM documents WHERE filename = %s", ("broken.txt",)
    ).fetchone()[0]
    assert count == 0


# ---- read_chunks_by_ids (ticket #27) ----


# T10: each Source has the chunk's content, location and its document's filename
def test_read_returns_sources_with_filename(pg_conn):
    chunks = [
        Chunk(chunk_index=0, content="first", source_location={"page": 3}),
        Chunk(chunk_index=1, content="second"),
    ]
    _, chunk_ids = save_document(pg_conn, make_document("week1.txt"), chunks)

    sources = read_chunks_by_ids(pg_conn, chunk_ids)

    assert sources == [
        Source(
            chunk_id=chunk_ids[0],
            filename="week1.txt",
            source_location={"page": 3},
            content="first",
        ),
        Source(
            chunk_id=chunk_ids[1],
            filename="week1.txt",
            source_location=None,
            content="second",
        ),
    ]


# T11: the result follows the order of the ids, not the order in the table
def test_read_keeps_the_order_of_the_ids(pg_conn):
    _, chunk_ids = save_document(pg_conn, make_document(), make_chunks(3))
    asked = [chunk_ids[2], chunk_ids[0], chunk_ids[1]]

    sources = read_chunks_by_ids(pg_conn, asked)

    assert [source.chunk_id for source in sources] == asked
    assert [source.content for source in sources] == ["chunk 2", "chunk 0", "chunk 1"]


# T12: chunks of two documents each get their own document's filename (the join)
def test_read_across_two_documents(pg_conn):
    _, first_ids = save_document(pg_conn, make_document("a.txt"), make_chunks(1))
    _, second_ids = save_document(pg_conn, make_document("b.txt"), make_chunks(1))

    sources = read_chunks_by_ids(pg_conn, [second_ids[0], first_ids[0]])

    assert [source.filename for source in sources] == ["b.txt", "a.txt"]


# T13: an empty list gives an empty list
def test_read_empty_list(pg_conn):
    assert read_chunks_by_ids(pg_conn, []) == []


# T14: an id that is not in Postgres is skipped, the others still come back
def test_read_skips_unknown_id(pg_conn):
    _, chunk_ids = save_document(pg_conn, make_document(), make_chunks(2))
    unknown_id = max(chunk_ids) + 1000

    sources = read_chunks_by_ids(pg_conn, [chunk_ids[0], unknown_id, chunk_ids[1]])

    assert [source.chunk_id for source in sources] == chunk_ids


# T15: an id asked for twice comes back once, at its first place
def test_read_returns_a_repeated_id_once(pg_conn):
    _, chunk_ids = save_document(pg_conn, make_document(), make_chunks(2))

    sources = read_chunks_by_ids(pg_conn, [chunk_ids[1], chunk_ids[0], chunk_ids[1]])

    assert [source.chunk_id for source in sources] == [chunk_ids[1], chunk_ids[0]]


# T16: the result fits the model. Answer accepts it as its sources
def test_read_result_fits_answer(pg_conn):
    _, chunk_ids = save_document(pg_conn, make_document(), make_chunks(2))

    sources = read_chunks_by_ids(pg_conn, chunk_ids)

    assert all(isinstance(source, Source) for source in sources)
    answer = Answer(answer="Because of the notes.", sources=sources)
    assert answer.sources == sources
