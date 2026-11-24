"""Hello world agent for the Retrieval & Generation track.

The model name comes from LLM_MODEL in .env, so switching model is a config
change and not a code change. Tests pass their own model, so they never call
the real API.
"""

import os

from pydantic_ai import Agent
from pydantic_ai.models import Model

DEFAULT_MODEL = "anthropic:claude-haiku-5-5"

INSTRUCTIONS = (
    "You are Study Buddy, a study assistant for students. "
    "Answer briefly and clearly in the same language as the question."
)


def build_agent(model: Model | str | None = None) -> Agent:
    """Create the agent. Without a model, LLM_MODEL from the environment is used."""
    return Agent(
        model or os.getenv("LLM_MODEL", DEFAULT_MODEL),
        instructions=INSTRUCTIONS,
    )


def ask(question: str, model: Model | str | None = None) -> str:
    """Ask the agent one question and return the answer as text."""
    result = build_agent(model).run_sync(question)
    return result.output


if __name__ == "__main__":
    print(ask("Explain in one sentence what RAG is."))
