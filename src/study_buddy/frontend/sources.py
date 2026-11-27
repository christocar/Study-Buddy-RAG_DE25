"""Turns a source into short text for the sources list."""


def format_seconds(seconds: int) -> str:
    # 125 -> "2:05"
    return f"{seconds // 60}:{seconds % 60:02d}"


def source_place(source: dict) -> str:
    # {"page": 3} -> "page 3", {"second": 125} -> "2:05", None -> "" (.txt / .md)
    location = source.get("source_location") or {}
    if "page" in location:
        return f"page {location['page']}"
    if "second" in location:
        return format_seconds(int(location["second"]))
    return ""


def source_preview(source: dict, length: int = 70) -> str:
    # the start of the chunk on one line, so sources from the same file look different
    text = " ".join(source["content"].split())
    return text if len(text) <= length else text[:length].rstrip() + "…"


def source_label(number: int, source: dict) -> str:
    # [1] notes.md · page 3 — "the start of the chunk…"
    place = source_place(source)
    where = f"{source['filename']} · {place}" if place else source["filename"]
    return f"[{number}] {where} — “{source_preview(source)}”"
