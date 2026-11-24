"""Tests for the hello world agent. No real API calls, so CI needs no key."""

import pytest
from pydantic_ai import models
from pydantic_ai.models.test import TestModel

from study_buddy.qa.agent import ask, build_agent

# Stop the tests if anything tries to call a real model
models.ALLOW_MODEL_REQUESTS = False


def test_ask_returns_the_model_answer():
    answer = ask("What is RAG?", model=TestModel(custom_output_text="RAG answer"))
    assert answer == "RAG answer"


def test_agent_reads_model_name_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_MODEL", "test")
    agent = build_agent()
    assert agent.model is not None
