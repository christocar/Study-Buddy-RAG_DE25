"""
Generation: the agent answers the question from the retrieved chunks only.

The agent gets the question and the chunks, each marked with its chunk_id.
It returns its answer and the chunk ids it used. The code then picks those
chunks from the ones Retrieval found, so a source can never be made up:
an id the agent invents, that was not among the chunks, is dropped.

No chunks at all means there is nothing to answer from. Then the agent is
not called, and the answer says so straight away.

The agent is created once, when the module is imported. defer_model_check
waits with the model and its API key until the first question, so importing
this module in CI needs no key. Tests swap the model with
generation_agent.override(model=TestModel(...)).
"""

import os

from pydantic import BaseModel
from pydantic_ai import Agent

from study_buddy.models import Answer, Source
from study_buddy.qa.agent import DEFAULT_MODEL

NO_ANSWER = "I don't know. The uploaded material doesn't cover this."

INSTRUCTIONS = f"""
You are Study Buddy, a study assistant. Answer the question using ONLY the
numbered chunks you are given. Do not use any other knowledge.

- Answer briefly and clearly, in the same language as the question.
- In used_chunk_ids, list the chunk_id of every chunk your answer is based on.
- If the chunks do not contain the answer, reply exactly: {NO_ANSWER}
  and leave used_chunk_ids empty.
"""


class AgentReply(BaseModel):
    """What the agent hands back: its answer and the chunks it used."""

    answer: str
    used_chunk_ids: list[int]


generation_agent = Agent(
    os.getenv("LLM_MODEL", DEFAULT_MODEL),
    output_type=AgentReply,
    instructions=INSTRUCTIONS,
    defer_model_check=True,
)


def format_chunks(sources: list[Source]) -> str:
    """Write the chunks as numbered text blocks the agent can refer to."""
    blocks = []
    for source in sources:
        location = f", {source.source_location}" if source.source_location else ""
        blocks.append(
            f"[chunk_id={source.chunk_id}] ({source.filename}{location})\n"
            f"{source.content}"
        )
    return "\n\n".join(blocks)


def generate(question: str, sources: list[Source]) -> Answer:
    """
    Answer the question from the sources only, and return an Answer.

    Answer.sources holds the chunks the agent says it used, in the order
    Retrieval found them (closest first). With no sources, the agent is not
    called and the answer is NO_ANSWER.
    """
    if not sources:
        return Answer(answer=NO_ANSWER, sources=[])

    prompt = f"Question: {question}\n\nChunks:\n\n{format_chunks(sources)}"
    reply = generation_agent.run_sync(prompt).output

    used = set(reply.used_chunk_ids)
    return Answer(
        answer=reply.answer,
        sources=[source for source in sources if source.chunk_id in used],
    )
