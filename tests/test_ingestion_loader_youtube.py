# test_ingestion_loader_youtube.py, tests for load_youtube()-function and its helpers
# Code: English
# Comments: English

"""
No network required, Youtue answers neither CI nor the cloud.
Snippets are built by hand, get_english_transcript() + fetch_title are swapped for fakes.
"""

import pytest
from youtube_transcript_api import (
    FetchedTranscript,
    FetchedTranscriptSnippet,
    RequestBlocked,
    TranscriptsDisabled,
)

from study_buddy.ingestion.loaders import youtube

VIDEO_ID = "KdeoPglfpb8"

# two snippets in the first min, one in the second min, one in the third min
SNIPPETS = [
    FetchedTranscriptSnippet(text="hello\nworld", start=0.5, duration=2.0),
    FetchedTranscriptSnippet(text="cool stuffs", start=30.0, duration=2.0),
    FetchedTranscriptSnippet(text="Second minute", start=61.2, duration=2.0),
    FetchedTranscriptSnippet(text="tres minutos", start=125.9, duration=2.0),
]


def fake_transcript(api, video_id):
    return FetchedTranscript(
        snippets=SNIPPETS,
        video_id=video_id,
        language="English",
        language_code="en",
        is_generated=True,
    )


@pytest.mark.parametrize(
    "link",
    [
        f"https://youtu.be/{VIDEO_ID}?si=abc987",
        f"https://www.youtube.com/watch?v={VIDEO_ID}&t=42",
        f"https://m.youtube.com/watch?v={VIDEO_ID}",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/embed/{VIDEO_ID}",
        VIDEO_ID,
    ],
)
def test_video_id_from_common_link_shape(link):
    assert youtube.extract_video_id(link) == VIDEO_ID


def test_link_that_isnt_youtube_refused():
    with pytest.raises(ValueError, match="video id"):
        youtube.extract_video_id("https://elonmusk.gov/696969123")


def test_snippets_become_one_section_per_minute():
    sections = youtube.build_section(SNIPPETS)

    assert [s.source_location for s in sections] == [
        {"second": 0},
        {"second": 61},
        {"second": 125},
    ]
    # the new line inside a snippet becomes a space
    assert sections[0].text == "hello world cool stuffs"


def test_load_youtube_builds_a_document(monkeypatch):
    monkeypatch.setattr(youtube, "get_english_transcript", fake_transcript)
    monkeypatch.setattr(
        youtube, "fetch_title", lambda video_id: "AI Ops: Week 6 incoming!"
    )

    document = youtube.load_youtube(f"https://youtu.be/{VIDEO_ID}")

    assert document.source_type == "youtube"
    assert document.filename == f"ai-ops-week-6-incoming-{VIDEO_ID}"
    assert len(document.sections) == 3


# Simulating an error with the video thats turned its transcripts off
def test_library_error_becomes_a_value_error(monkeypatch):
    def disabled(api, video_id):
        raise TranscriptsDisabled(video_id)

    monkeypatch.setattr(youtube, "get_english_transcript", disabled)

    with pytest.raises(ValueError, match="TranscriptsDisabled"):
        youtube.load_youtube(VIDEO_ID)


# Simulates an error where Youtube has blocked us. It should NOT turn into a ValueError
def test_requests_blocked_goes_through(monkeypatch):
    def blocked(api, video_id):
        raise RequestBlocked(video_id)

    monkeypatch.setattr(youtube, "get_english_transcript", blocked)

    with pytest.raises(RequestBlocked):
        youtube.load_youtube(VIDEO_ID)
