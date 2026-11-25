# The shapes: `models.py`
*Johnny. Last updated 2026-11-25. Describes `src/study_buddy/models.py`.*

Purpose: what every track hands to the next, what each field means, and the few rules that keep the tracks in step. Read this before you build against the shapes, and when you review a change to them.

## TL;DR

**Five shapes, one file.** `Section`, `Document`, `Chunk`, `Source` and `Answer` in `src/study_buddy/models.py`. Every backend track imports from there, and the file imports only Pydantic. Every shape rejects fields it does not know, so a typo stops with an error instead of vanishing.

**Three rules to remember:** the loader lowercases the file extension before it builds a `Document`. `chunk_index` and `chunk_id` are two different numbers. And a change to a field is a change for every track, so it goes in its own PR that everyone reviews.

**Jump straight to:**

1. [The flow](#the-flow)
2. [The five shapes](#the-five-shapes)
3. [Two numbers: chunk_index and chunk_id](#two-numbers-chunk_index-and-chunk_id)
4. [Rules for each track](#rules-for-each-track)
5. [What the models do not check](#what-the-models-do-not-check)
6. [How to use them](#how-to-use-them)
7. [The tests](#the-tests)
8. [Reviewing a change to the shapes](#reviewing-a-change-to-the-shapes)
9. [Not in phase 1](#not-in-phase-1)

## The flow

```
file bytes --loader--> Document --chunker--> list[Chunk] --pipeline--> Postgres --same id--> LanceDB
                       (sections)            (chunk_index)              (gives chunks.id)

question --POST /ask--> Answer(answer, sources: list[Source]) --JSON--> Streamlit sources dropdown
```

Pydantic checks a shape when it is created. A wrong value stops with a `ValidationError` in the code that made the mistake, instead of showing up two tracks later as an empty field in the dropdown.

**Unknown fields are stopped too.** Every shape has `model_config = ConfigDict(extra="forbid")`, so a misspelled field such as `source_locaton` raises a `ValidationError` instead of being dropped and leaving the place empty.

## The five shapes

| Shape | What it is | Made by | Read by |
|---|---|---|---|
| `Section` | One page, one stretch of a video, or the whole .txt | loader | chunker |
| `Document` | What a loader hands over | loader | chunker |
| `Chunk` | One piece of text after chunking, not saved yet | chunker | pipeline, Storage |
| `Source` | One row in the sources dropdown | Retrieval | `/ask`, frontend |
| `Answer` | What `POST /ask` returns | `/ask` | frontend |

Field by field. The column is where the value ends up in `sql/schema.sql`.

| Shape | Field | Type | Meaning | Column |
|---|---|---|---|---|
| `Section` | `text` | `str` | The text of the page, the stretch or the whole file | becomes `chunks.content` after chunking |
| | `source_location` | `dict \| None`, default `None` | Where in the source: `{"page": 3}`, `{"second": 125}` or `None` | `chunks.source_location` (JSONB) |
| `Document` | `filename` | `str` | The uploaded file's name | `documents.filename` |
| | `source_type` | `Literal["txt", "md", "pdf", "youtube"]` | The kind of file, lowercase | `documents.source_type` |
| | `sections` | `list[Section]` | The text in sections, in order | — |
| `Chunk` | `chunk_index` | `int` | The place in its document, from 0 | `chunks.chunk_index` |
| | `content` | `str` | The text of the chunk | `chunks.content` |
| | `source_location` | `dict \| None`, default `None` | Copied from the section the chunk came from | `chunks.source_location` |
| `Source` | `chunk_id` | `int` | The chunk's row in Postgres, the same id as its vector in LanceDB | `chunks.id` |
| | `filename` | `str` | The file the chunk came from | `documents.filename` |
| | `source_location` | `dict \| None`, default `None` | Where in that file | `chunks.source_location` |
| | `content` | `str` | The text of the chunk, shown under the answer | `chunks.content` |
| `Answer` | `answer` | `str` | The agent's answer | — |
| | `sources` | `list[Source]` | The chunks the answer rests on. Can be empty | — |

## Two numbers: chunk_index and chunk_id

| | `chunk_index` | `chunk_id` |
|---|---|---|
| What | The chunk's place in its document | The chunk's row, `chunks.id` in Postgres |
| Starts | at 0, again in every document | at 1, and runs across all documents |
| Set by | the chunker | Postgres, when the row is saved |
| Lives in | `Chunk` | `Source` |

A `Chunk` has only the index, because it is not saved yet. A `Source` has only the id, because it comes out of the database. LanceDB stores each vector under `chunk_id`.

**Mixing them up crashes nothing.** The search returns a valid id, just for the wrong chunk, and the dropdown shows the chunk next door. That is why `Chunk` refuses a `chunk_id`, and why the pipeline's test uses a fake Postgres whose ids do not start at 0.

## Rules for each track

- **Loader:** lowercase the extension before you build the `Document`. `"TXT"` and `"Md"` are stopped just like `"docx"`. For .txt and .md, leave `source_location` out; it becomes `None`.
- **Chunker:** copy `source_location` from the section into every chunk made from it. Number the chunks from 0 in every document. Never add an id.
- **Storage:** save the chunks first and hand back the new ids in `chunk_index` order. The vectors go into LanceDB under those ids.
- **Retrieval & Generation:** build each `Source` from the row in Postgres, so `chunk_id` is `chunks.id`. An answer that says the material does not cover the question has `sources=[]`.
- **Frontend:** the place is under `source_location`. Show `"Page 3"` for `{"page": 3}`, a time for `{"second": 125}`, and only the file name when it is empty.
- **Everyone:** use the keys `"page"` and `"second"` exactly. Nothing checks them, so a loader writing `"minute"` and a dropdown reading `"second"` gives an empty place without an error.

## What the models do not check

They check the shape, not the meaning.

- **The keys inside `source_location`.** Any dict gets through. `{"pgae": 3}` is valid.
- **Empty values.** `text=""`, `sections=[]` and `sources=[]` are valid. An empty file is not stopped by the shapes; the chunker or the pipeline decides what to do with it.
- **Whether an id points at the right row.** `chunk_id=7` is a valid integer, whatever row 7 holds.
- **Safe conversion still happens.** In an `int` field, `"3"` becomes `3` and `2.0` becomes `2`, but `1.5` is stopped. Nothing is converted into a `str`: `content=5` is stopped.

## How to use them

```python
from study_buddy.models import Answer, Chunk, Document, Section, Source

# Loader: one section for a whole .txt, no place
doc = Document(
    filename="notes.txt",
    source_type="txt",
    sections=[Section(text="The whole file...")],
)

# Chunker: one Chunk per piece, numbered from 0 in every document
chunks = [
    Chunk(chunk_index=i, content=piece, source_location=section.source_location)
    for i, piece in enumerate(pieces)
]

# Retrieval: one Source per row from Postgres
source = Source(
    chunk_id=row_id,
    filename=filename,
    source_location=location,
    content=content,
)
answer = Answer(answer="It retrieves first.", sources=[source])
```

What the frontend gets from `POST /ask`, as JSON:

```json
{
  "answer": "It retrieves first.",
  "sources": [
    {
      "chunk_id": 42,
      "filename": "lecture.pdf",
      "source_location": {"page": 3},
      "content": "RAG retrieves before it generates."
    }
  ]
}
```

## The tests

`tests/test_pydantic_models.py`. They test what we decided, not what Pydantic already promises: that `int` stops `"abc"` is Pydantic's job, which values we let in is ours.

| Test | What it guards |
|---|---|
| `test_document_accepts_the_source_types` | All four planned types get through |
| `test_document_rejects_unknown_and_uppercase_source_types` | `"docx"`, `"pDF"`, `"TXT"` and `"Md"` are stopped |
| `test_source_location_is_none_when_left_out` | A .txt section needs no place |
| `test_answer_without_sources_is_valid` | "Not in the material" is a valid answer |
| `test_answer_survives_the_trip_through_json` | Nothing is lost between FastAPI and Streamlit |
| `test_chunk_has_no_id_before_it_is_saved` | A `chunk_id` cannot sneak into a `Chunk` |
| `test_misspelled_field_in_source_is_rejected` | A typo in `Source` stops with an error instead of emptying the place in the dropdown |

## Reviewing a change to the shapes

- Does every field that is saved have the same name as its column in `sql/schema.sql`?
- Is every value in `Literal[...]` lowercase, and does the loader produce exactly those strings?
- Does every optional field have a default (`= None`)? Without one, it is required.
- Does a new shape have `model_config = ConfigDict(extra="forbid")`, like the other five?
- Does `Chunk` still have `chunk_index` and no `chunk_id`, and `Source` the opposite?
- Does every track that creates or reads the changed shape still work? Run `uv run pytest`.
- Is the change in its own PR, and has someone from each affected track seen it?

## Not in phase 1

- `file_hash`, `status`, `error_message` and `char_count` from `schema.sql`. All four can be empty, so they stay out until a track needs them.
- A rule that a PDF section must have a page. A `Section` does not know which file it came from, so that check belongs in the PDF loader's tests.
