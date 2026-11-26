"""
Tests for retrieval. No real API and no Postgres:

- The embedding client is a fake that returns vectors we choose. The REAL
  embed_texts() still runs, so the test checks that the question goes through it.
- LanceDB is real, in a temporary folder, with the vectors saved by the test.
- read_chunks_by_ids() is replaced by a fake that reads from a dict, with the
  same shape as Aira's function: ids in, Sources out in the same order.
"""

from types import SimpleNamespace

import pytest

from study_buddy.embedding.constants import EMBEDDING_DIM
from study_buddy.models import Source
from study_buddy.qa import retrieval
from study_buddy.qa.retrieval import retrieve
from study_buddy.storage.vector_store import get_vector_db, save_vectors


def one_hot(position: int) -> list[float]:
    """A vector that points in one direction only: 1.0 at `position`, 0.0 elsewhere."""
    vector = [0.0] * EMBEDDING_DIM
    vector[position] = 1.0
    return vector


class FakeEmbeddingClient:
    """Answers client.embeddings.create() like the OpenAI package, without a network."""

    def __init__(self, vector: list[float]):
        self.vector = vector
        self.inputs: list[list[str]] = []  # every input it was asked to embed
        self.embeddings = self  # so client.embeddings.create() lands on self.create()

    def create(self, model, input, encoding_format):
        self.inputs.append(input)
        data = [
            SimpleNamespace(index=i, embedding=self.vector) for i in range(len(input))
        ]
        return SimpleNamespace(data=data)


# Three chunks as they would be in Postgres, keyed on chunk_id
CHUNKS = {
    10: Source(chunk_id=10, filename="sql.md", content="SELECT reads rows."),
    20: Source(chunk_id=20, filename="keys.md", content="A primary key is unique."),
    30: Source(chunk_id=30, filename="keys.md", content="A foreign key points."),
}


@pytest.fixture
def db(tmp_path):
    db = get_vector_db(str(tmp_path))
    save_vectors(db, [10, 20, 30], [one_hot(0), one_hot(1), one_hot(2)])
    return db


@pytest.fixture
def fake_postgres(monkeypatch):
    """Replace read_chunks_by_ids in retrieval.py and remember which ids it got."""
    asked_for: list[list[int]] = []

    def fake_read_chunks_by_ids(conn, chunk_ids):
        asked_for.append(chunk_ids)
        return [CHUNKS[chunk_id] for chunk_id in chunk_ids if chunk_id in CHUNKS]

    monkeypatch.setattr(retrieval, "read_chunks_by_ids", fake_read_chunks_by_ids)
    return asked_for


def test_returns_the_nearest_chunks_as_sources_closest_first(db, fake_postgres):
    # The question points mostly like chunk 20, a little like chunk 30
    question_vector = one_hot(1)
    question_vector[2] = 0.3
    client = FakeEmbeddingClient(question_vector)

    sources = retrieve(
        "What is a primary key?", client=client, db=db, conn=None, top_k=2
    )

    assert [source.chunk_id for source in sources] == [20, 30]
    assert sources[0].content == "A primary key is unique."
    assert fake_postgres == [[20, 30]]


def test_the_question_goes_through_embed_texts(db, fake_postgres):
    client = FakeEmbeddingClient(one_hot(0))

    retrieve("What does SELECT do?", client=client, db=db, conn=None)

    assert client.inputs == [["What does SELECT do?"]]


def test_empty_lancedb_gives_no_sources(tmp_path, fake_postgres):
    empty_db = get_vector_db(str(tmp_path))
    client = FakeEmbeddingClient(one_hot(0))

    assert retrieve("Anything?", client=client, db=empty_db, conn=None) == []


def test_empty_question_is_refused_before_any_embedding(db, fake_postgres):
    client = FakeEmbeddingClient(one_hot(0))

    with pytest.raises(ValueError, match="empty"):
        retrieve("   ", client=client, db=db, conn=None)
    assert client.inputs == []
