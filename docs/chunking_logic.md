# Chunking: `chunker.py`
*Johnny. Last updated 2026-11-25. Describes `src/study_buddy/ingestion/chunker.py`.*

Purpose: why we cut every uploaded file into small pieces, how the chunker does it, and what the rest of the pipeline can count on. Read this before you build on the chunks, or when you want to change the numbers.

## TL;DR

**The chunker cuts a `Document` into a `list[Chunk]`.** Each piece is at most 1000 characters, and two pieces in a row share 200 characters. It cuts one section (one page) at a time, so a chunk never mixes two pages.

**Why at all:** the embedding model only reads the start of a long text, one vector for a whole file is too blurry to find anything, and the agent should get the paragraph that answers the question, not the whole PDF.

**Three numbers, one file:** `CHUNK_SIZE`, `CHUNK_OVERLAP` and `MIN_SECTION_CHARS` in `src/study_buddy/embedding/constants.py`. They are a starting point. We measure and adjust them later.

**Jump straight to:**

1. [Why we chunk](#why-we-chunk)
2. [Where the chunker sits](#where-the-chunker-sits)
3. [How the window works](#how-the-window-works)
4. [What you can count on](#what-you-can-count-on)
5. [Why characters and not tokens](#why-characters-and-not-tokens)
6. [Changing the numbers](#changing-the-numbers)
7. [What it does not do yet](#what-it-does-not-do-yet)
8. [Words](#words)

## Why we chunk

A student uploads 40 pages of lecture slides and asks *"what does overlap mean?"*. The answer is one paragraph on page 12. Our job is to find that paragraph.

1. **The model has a limit.** Grunden's `bge-m3` reads at most 8192 tokens per text. A longer text is cut **without an error**, so the vector would only describe the start of the file.
2. **Small pieces give sharp vectors.** One vector for a whole file is an average of every topic in it, and lands close to no question. A piece that is about one thing lands close to questions about that thing.
3. **The agent gets only what matters.** A few pieces in the prompt instead of the whole file: cheaper, less noise, and the sources dropdown can say *page 12* instead of *somewhere in the PDF*.

## Where the chunker sits

```text
POST /upload  (file name + bytes)
   |
loader      load_text_file()  -> Document     one Section per page, or one for a .txt
   |
chunker     chunk_document()  -> list[Chunk]  chunk_index 0, 1, 2 ...
   |
Postgres    save_document()   -> chunk ids    41, 42, 43 ...
   |
LanceDB     one vector per chunk, saved under the same id
```

`ingest_file()` in `ingestion/pipeline.py` (#34) will call these in order.

## How the window works

Think of a window that slides over the text. It is `CHUNK_SIZE` characters wide, and it moves `CHUNK_SIZE - CHUNK_OVERLAP` characters each step. With small numbers, size 4 and overlap 1, the window moves 3:

```text
text:     1234567890
chunk 0   1234
chunk 1      4567
chunk 2         7890
```

The last chunk ends exactly where the text ends. When the window reaches the end, it stops: there is never an extra chunk that only repeats what the one before already had.

With our real numbers, size 1000 and overlap 200, the window moves 800. A page with 2500 characters gives three chunks: characters 0–1000, 800–1800 and 1600–2500.

**Why overlap?** The window cuts wherever it is, often in the middle of a sentence. With 200 characters of overlap, any passage of up to 200 characters that falls on a border is whole in at least one chunk. The price is about 25 % more chunks, and some text stored twice.

## What you can count on

| Rule | What it means for you |
|---|---|
| No chunk is longer than `CHUNK_SIZE` | Every chunk fits far under the model's limit |
| A chunk never spans two sections | Every chunk keeps its section's `source_location`, so the page in the dropdown is right |
| `chunk_index` counts 0, 1, 2 ... across the whole document | No restart per page and no gaps. It is not the id in Postgres, see `docs/shapes_of_basemodels.md` |
| A section shorter than `MIN_SECTION_CHARS` gives no chunk | A page with only images, a lone page number or an empty page is skipped. Spaces and new lines are not counted |
| A document with no text gives an empty list | `save_document` refuses an empty list, and the pipeline will turn it into a clear message |
| A bad setting stops at once | If the overlap is not below the size, `split_text` raises `ValueError` instead of running forever or giving nothing |

## Why characters and not tokens

The model's limit is in tokens, but the project has no way to count tokens for `bge-m3`. We don't need one: a token is usually about four characters, and even if every character became a token, 1000 would still be far under 8192.

## Changing the numbers

All three live in `src/study_buddy/embedding/constants.py`:

| Constant | Value | Meaning |
|---|---|---|
| `CHUNK_SIZE` | 1000 | Most characters in one chunk |
| `CHUNK_OVERLAP` | 200 | Characters two chunks in a row share, 20 % of the size |
| `MIN_SECTION_CHARS` | 20 | Shorter sections give no chunk |

`test_constants_are_safe` checks in CI that the overlap is below the size and that the size is under the model's limit. Files that are already saved keep their old chunks until they are uploaded again.

There is no right answer for these numbers. The way to find better ones is to measure: a set of test questions with known answers, a check of how often the right chunk comes back, and one number changed at a time. This is something we will have to evaluate in later stages with questions to measure both our `Retrieval` and our `Generation` in our `eval harness`

## What it does not do yet

- **It cuts in the middle of words and sentences.** The overlap softens this, but a chunk that starts mid-sentence gives a weaker vector. A later step can cut at paragraphs (`\n\n`) first, and use the window only on paragraphs that are too long. The loader already turns Windows new lines into `\n` for this.
- **It does not split .md files by heading.** A .md file is one section for now.
- **`char_count` is not saved.** The column exists in `sql/schema.sql`. It comes up when we write the phase 2 issues.

## Words

| Word | Meaning |
|---|---|
| Section | One page, one stretch of a video, or the whole .txt. Made by the loader |
| Chunk | One piece of a section, at most `CHUNK_SIZE` characters |
| Overlap | The characters two chunks in a row share |
| Token | The unit the model reads. About four characters of normal text |
| Vector | 1024 numbers that stand for what a chunk means. Saved in LanceDB |
