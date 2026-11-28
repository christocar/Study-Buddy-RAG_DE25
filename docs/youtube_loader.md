# Youtube: a link to a video that becomes a document

_Johnny  #50_

```text
YOUTUBE  POST /youtube -> load_youtube() -> ingest_document() -> Postgres + LanceDB
```

## How to use it

There is no field for links in the frontend as of yet (2026-11-28). Until there is, a video is added through the backend, and you ask about it on the **Ask** page as usual with `docker compose up -d` running:

**Swagger UI**, works on every machine: http://localhost:8000/docs -> `POST /youtube` -> **Try it out** -> paste the link as `"url"` -> **Execute**.

**curl**, in Git Bash or a Mac or Linux terminal:

```bash
curl -s -X POST http://localhost:8000/youtube \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=<VIDEO_ID_HERE>"}'
```

## Links it takes

`watch?v=<id>`, `youtu.be/<id>`, `m.youtube.com`, `/shorts/<id>`, `/embed/<id>`, `/live/<id>`, or the 11-character id on its own. Extra parts like `?si=` and `&t=42` are ignored.

## Answers

| Code | When | What to do |
|---|---|---|
| 200 | `{"document_id": 7, "filename": "<title-slug>-<video_id>"}` | Ask about it |
| 400 | Not a YouTube link, no usable English transcript, or too little text | Read `detail`, try another video |
| 422 | The body has no `url` | Send `{"url": "..."}` |
| 503 | YouTube is blocking requests from this IP address | **Stop. Don't retry.** Wait a while |

## Rules

- **One link per call.** The endpoint never pauses and never retries. A `503` means stop: retrying is what gets an IP address blocked for days in worst case scenario. 
- **English only.** Manual English first, then auto-generated, then a transcript YouTube can translate to English. **Note:** we COULD try and incorporate some kind of language selection for transcripts but for now, it should be treated as a "nice-to-have" and not a must.
- **The filename finds the video again:** the title as a slug, then the video id. A title without Latin letters gives just the id. **Note:** Like the `English-only` rule, this is something we can work on later, but for now, it should be treated as a "nice-to-have" and not a must.
- **Every source knows its second.** One `Section` per 60 seconds with `{"second": 182}`. The Ask page shows it as `3:02`, and `https://youtu.be/<id>?t=182` opens the video right there.

## Known issues

- The same video twice gives two documents, since we've got no duplicate check yet.
- From Azure, Youtube **may** block cloud IP addresses. Tested in phase 3.

## Test it without network

```bash
uv run pytest tests/test_ingestion_loader_youtube.py tests/test_api_youtube.py
```

The library and the pipeline are faked, so no video is fetched when running test-suite.
