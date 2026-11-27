from study_buddy.frontend.sources import source_label, source_place


def test_place_for_page_second_and_text_file():
    assert source_place({"source_location": {"page": 3}}) == "page 3"
    assert source_place({"source_location": {"second": 125}}) == "2:05"
    assert source_place({"source_location": None}) == ""


def test_label_shows_file_place_and_a_short_preview():
    source = {
        "filename": "lecture.pdf",
        "source_location": {"page": 3},
        "content": "word " * 50,  # long, so the preview gets cut
    }
    label = source_label(1, source)
    assert label.startswith("[1] lecture.pdf · page 3 — “word word")
    assert label.endswith("…”")
