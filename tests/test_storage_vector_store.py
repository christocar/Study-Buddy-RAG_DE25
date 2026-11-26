"""Tests for the LanceDB vector store. Each test gets its own temporary folder."""

import pytest

from study_buddy.embedding.constants import EMBEDDING_DIM
from study_buddy.storage.vector_store import get_vector_db, save_vectors, search_vectors


def one_hot(position: int) -> list[float]:
    """A vector that points in one direction only: 1.0 at `position`, 0.0 elsewhere."""
    vector = [0.0] * EMBEDDING_DIM
    vector[position] = 1.0
    return vector


@pytest.fixture
def db(tmp_path):
    # tmp_path is a new empty folder per test, removed by pytest afterwards
    return get_vector_db(str(tmp_path))


def test_search_finds_the_saved_vector_first(db):
    save_vectors(db, [10, 20, 30], [one_hot(0), one_hot(1), one_hot(2)])

    # Mostly direction 1, a little direction 2: chunk 20 is nearest, then 30
    query = one_hot(1)
    query[2] = 0.3

    assert search_vectors(db, query, limit=2) == [20, 30]


def test_vectors_are_still_there_after_reopening(tmp_path):
    save_vectors(get_vector_db(str(tmp_path)), [7], [one_hot(5)])

    assert search_vectors(get_vector_db(str(tmp_path)), one_hot(5)) == [7]


def test_search_in_empty_table_gives_empty_list(db):
    assert search_vectors(db, one_hot(0)) == []


def test_wrong_vector_length_is_refused(db):
    with pytest.raises(ValueError, match="EMBEDDING_DIM"):
        save_vectors(db, [1], [[0.1, 0.2, 0.3]])


def test_different_list_lengths_are_refused(db):
    with pytest.raises(ValueError, match="chunk ids"):
        save_vectors(db, [1, 2], [one_hot(0)])
