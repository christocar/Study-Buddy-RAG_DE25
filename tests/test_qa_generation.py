"""
Tests for generation, with TestModel instead of a real model.

TestModel cannot test WHAT a model says, only that our code handles the
reply right. Whether the real model says it doesn't know is checked by hand,
with a real key.
"""

import pytest
from pydantic_ai import capture_run_messages, models
from pydantic_ai.models.test import TestModel

from study_buddy.models import Source
from study_buddy.qa.generation import NO_ANSWER, generate, generation_agent

# Stop the tests if anything tries to call a real model
models.ALLOW_MODEL_REQUESTS = False

SOURCES = [
    Source(chunk_id=20, filename="keys.md", content="A primary key is unique."),
    Source(chunk_id=30, filename="keys.md", content="A foreign key points."),
]


def reply(answer: str, used_chunk_ids: list[int]) -> TestModel:
    """A TestModel that hands back exactly this reply from the agent."""
    return TestModel(
        custom_output_args={"answer": answer, "used_chunk_ids": used_chunk_ids}
    )


def test_returns_the_answer_and_the_sources_it_used():
    with generation_agent.override(model=reply("It is unique.", [20])):
        answer = generate("What is a primary key?", SOURCES)

    assert answer.answer == "It is unique."
    assert [source.chunk_id for source in answer.sources] == [20]


def test_sources_keep_the_retrieval_order():
    # The agent lists 30 before 20, but the dropdown keeps closest first
    with generation_agent.override(model=reply("Both.", [30, 20])):
        answer = generate("Keys?", SOURCES)

    assert [source.chunk_id for source in answer.sources] == [20, 30]


def test_an_invented_chunk_id_is_dropped():
    with generation_agent.override(model=reply("Made up.", [20, 999])):
        answer = generate("Keys?", SOURCES)

    assert [source.chunk_id for source in answer.sources] == [20]


def test_no_sources_says_it_does_not_know_without_calling_the_agent():
    # A real model here would fail the test, since ALLOW_MODEL_REQUESTS is False
    answer = generate("What is a primary key?", [])

    assert answer.answer == NO_ANSWER
    assert answer.sources == []


def test_the_agent_gets_the_question_and_the_chunks():
    model = reply("It is unique.", [20])
    with capture_run_messages() as messages, generation_agent.override(model=model):
        generate("What is a primary key?", SOURCES)

    prompt = messages[0].parts[0].content
    assert "Question: What is a primary key?" in prompt
    assert "[chunk_id=20] (keys.md)" in prompt
    assert "A foreign key points." in prompt


@pytest.mark.parametrize("missing", [[], [999]])
def test_no_used_chunks_gives_no_sources(missing):
    with generation_agent.override(model=reply(NO_ANSWER, missing)):
        answer = generate("Something else?", SOURCES)

    assert answer.sources == []
