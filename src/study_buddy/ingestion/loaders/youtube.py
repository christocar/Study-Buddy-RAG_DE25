# youtube.py, Turn a Youtube link into a document.
# Code: English
# Comments: English

"""
The loader script for Youtube links.

Who calls it: POST /youtube in api/youtube.py (Ticket #50).

What it hands over: ONE Document with one Section per 60 sec of the transcript.
Each Section keeps its start as {"second": 125}, so a source can point back
into the video.
"""

import json
import re
import urllib.parse
import urllib.request

from youtube_transcript_api import (
    CouldNotRetrieveTranscript,
    FetchedTranscript,
    FetchedTranscriptSnippet,
    NoTranscriptFound,
    RequestBlocked,
    YouTubeTranscriptApi,
)

from study_buddy.models import Document, Section

# Prioritized order, fetch() already prefers manual over auto-generated.
# This COULD be made a constant that lets the user choose what kind of
# language they want to get the transcript as, just an idea for later
# phases if we have got time. @indira, @aira, @christoffer
PREFERRED_LANGUAGES = ["en", "en-US", "en-GB"]

# One section per this many seconds of speech.
BLOCK_SECONDS = 60

# A video ID is always 11x characters long in either letters, digits, - and _
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


# function to extract the YT videos id
def extract_video_id(url_or_id: str) -> str:
    """
    Accepts ANY common Youtube link or raw 11-character id and
    returns the video id.

    Query junk like ?si= .. etc is ignored.

    Raises ValueError if no video id can be found.
    """
    candidate = url_or_id.strip()

    if _VIDEO_ID_RE.match(candidate):
        return candidate

    parsed = urllib.parse.urlparse(candidate)
    host = parsed.netloc.lower().removeprefix("www.").removeprefix("m.")
    if host == "youtu.be":
        video_id = parsed.path.lstrip("/").split("/")[0]
    elif host in ("youtube.com", "youtube-nocookie.com"):
        if parsed.path == "/watch":
            video_id = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
        else:
            # /embed/<id>, /shorts/<id>, /live/<id>, /v/<id>
            parts = [part for part in parsed.path.split("/") if part]
            video_id = parts[1] if len(parts) >= 2 else ""
    else:
        video_id = ""

    if not _VIDEO_ID_RE.match(video_id):
        raise ValueError(f"Was not able to extract a video id from: {url_or_id!r}")
    return video_id


# Function to fetch the title
def fetch_title(video_id: str) -> str | None:
    """
    Best effort title from YouTubes own public oEmbed endpoint (no API key required here).
    """
    oembed = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(
        f"https://www.youtube.com/watch?v={video_id}", safe=""
    )
    try:
        with urllib.request.urlopen(oembed, timeout=10) as response:
            return json.load(response).get("title")
    except (OSError, ValueError):
        # No network, a HTTP error or a timeout is an OSError.
        # A bad JSON is a ValueError.
        # The title is nice to have but never fail the load over it.
        return None


# Function to manually get an english transcript, if not possible
# then go for an auto-generated one.
def get_english_transcript(
    api: YouTubeTranscriptApi, video_id: str
) -> FetchedTranscript:
    """
    Manual English first, then auto generated English,
    the last resort is to get any transcript that is translated to English..
    Hopefully.
    """
    try:
        return api.fetch(video_id, languages=PREFERRED_LANGUAGES)
    except NoTranscriptFound:
        for transcript in api.list(video_id):
            if transcript.is_translatable:
                return transcript.translate("en").fetch()
        raise


# Function for slug generation
def slugify(text: str, max_len: int = 60) -> str:
    """
    'Cool Data Engineer Bella: Part 1337!' becomes:
    'cool-data-engineer-bella-part-1337'
    """
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-")


# Priv function - FAAFO
def _to_section(texts: list[str], start: float) -> Section:
    """
    Joins the text of one stratch into a Section that knows its second.
    """
    # New lines and double spaces inside the snippets of text become single spaces
    text = re.sub(r"\s+", " ", " ".join(texts)).strip()
    return Section(text=text, source_location={"second": int(start)})


# Function to BUILD our sections per BLOCK_SECONDS constant.
def build_section(snippets: list[FetchedTranscriptSnippet]) -> list[Section]:
    """
    Merges the transcripts short snippets into ONE Section per BLOCK_SECONDS.
    A new Section starts at the FIRST snippet past the next full minute.
    """
    sections: list[Section] = []
    texts: list[str] = []
    block_start_at = 0.0
    next_cut = BLOCK_SECONDS

    for snippet in snippets:
        if snippet.start >= next_cut and texts:
            sections.append(_to_section(texts, block_start_at))
            texts = []
            block_start_at = snippet.start
            next_cut = (int(snippet.start) // BLOCK_SECONDS + 1) * BLOCK_SECONDS
        texts.append(snippet.text)

    # The last stretch of transcript has no 'end minute'
    if texts:
        sections.append(_to_section(texts, block_start_at))

    return sections


# Function to turn youtube link into a document with Sections á 60sec blocks.
def load_youtube(url: str) -> Document:
    """
    Turn a Youtube link into a Document with one Section à 60 sec.

    Throws ValueError if the link is not Youtube, if the video has NO usable
    transcript OR if the transcript is empty.
    /youtube turns that into a 400 code.

    RequestBlocked goes through as it is.

    NOTE: Youtube COULD block us and /youtube turns that in to a 503 code
    """
    # Step 1: Link -> video id. Anything that is NOT Youtube is a ValueError.
    video_id = extract_video_id(url)

    # Step 2: Fetch the transcript. The librarys errors share the parent:
    # CouldNotRetrieveTranscript + RequestBlocked is one of them.
    # So a RequestBlocked MUST come first
    try:
        fetched = get_english_transcript(YouTubeTranscriptApi(), video_id)
    except RequestBlocked:
        raise
    except CouldNotRetrieveTranscript as error:
        raise ValueError(
            f"Could NOT load the video '{video_id}': no usable English transcript "
            f"({type(error).__name__})."
        ) from error

    # Step 3: Snippets -> into one Section per 60 seconds
    sections = build_section(fetched.snippets)
    if not sections:
        raise ValueError(
            f"Could NOT load the video '{video_id}': there is no transcript."
        )

    # Step 4: The tilename finds the video again:
    # The title as a slug, video id last.
    # A title with ONLY non LATIN letters gives us an empty slug.
    title = fetch_title(video_id)
    slug = slugify(title) if title else ""
    filename = f"{slug}-{video_id}" if slug else video_id

    return Document(filename=filename, source_type="youtube", sections=sections)
