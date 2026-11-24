# Way of working: Study Buddy
*Johnny. Last updated 2026-11-22. Draft for the group meeting Monday 23 November. Applies when all four have approved it at the bottom.*

Purpose: how the four of us work together, from issue to merge, and what we promise each other. The spec requires a short document that everyone agrees on. This is it. The commands are in git workflow, the uv guide and the repo structure, here are only the rules.

## TL;DR

No code without an issue. An issue becomes a branch and a PR. Someone else reviews and merges, when CI is green. Speak up early when something is lagging, not the day before. Code you haven't written yourself gets a comment with the source, and you must be able to explain it.

**Jump straight to:**

1. [From issue to merge](#from-issue-to-merge)
2. [The tracks and the meetings](#the-tracks-and-the-meetings)
3. [Rules for the code](#rules-for-the-code)
4. [Contributions and co-authors](#contributions-and-co-authors)
5. [Presentation and reflection](#presentation-and-reflection)
6. [To decide at the meeting](#to-decide-at-the-meeting)
7. [Approved](#approved)

## From issue to merge

```text
issue ──► branch ──► commits ──► PR ──► green CI + review ──► merge ──► issue closes
Todo      In progress            In review                              Done
```

- **Every task is an issue on the board before anyone starts coding**, with labels for phase and track.
- **Set yourself as assignee and move the card** when you start. Then everyone sees who is doing what, and nobody builds the same thing twice.
- **One branch = one issue = one PR.** The PR text is written in English and ends with `Closes #N`, so the issue closes on merge.
- **Someone other than you reviews and merges.** The reviewer reads the code, not just that CI is green. If you don't understand a change, ask in the PR.
- **Code never goes directly to `main`.** The exception is a small fix in a document or in the README, which doesn't touch anyone's code.

## The tracks and the meetings

**Owning a track**, after Indira's idea: the owner keeps track of the track's tasks and asks for help early when it is lagging. Everyone may take a task from another track, but sign up on the issue and tell the owner first.

**Questions and decisions are written in the Discord channel, not in DMs.** Then everyone can read up, and nobody needs to be part of everything.

**When each phase ends** we check in, at most 30 minutes:

1. What has been merged? We go through the merged PRs together, so that everyone knows what the code looks like.
2. What is lagging, and who needs help?
3. Retro: what worked, and what do we change for the next phase?

## Rules for the code

- **The source rule from the spec.** Code we have taken from someone else, from the web or from our own earlier projects gets a comment with the source right next to it. You must understand how the code works and be able to explain it.

  ```python
  # Source: <url>. Adapted: kept only the retry logic
  ```

- **Secrets live in `.env`, never in the repo.** A new name is added to `.env.example` in the same PR as the code that reads it.
- **Values are passed to SQL as parameters** (`%s` in psycopg), never with f-strings. Otherwise a file name like `O'Brien.pdf` is enough to make the query break, and the same gap is the way in for SQL injection.
- **Don't write it twice.** If the function already exists in another track, like the embedding function, import it instead of writing your own. The spec assesses DRY for VG.
- **Streamlit only speaks HTTP with the API** and imports nothing from the other tracks.
- **Run the same three checks as CI before you push:** `uv run ruff check .`, `uv run ruff format .` and `uv run pytest`.
- **A new package is its own commit** with both `pyproject.toml` and `uv.lock`.

## Contributions and co-authors

For G everyone must have relevant commits and PRs. Each of us therefore opens their own PRs in their track, even when we help each other.

**If we pair program** the person who wrote the code commits, and the other is added as co-author:

```bash
git commit -m "feat(qa): add retrieval over lancedb" --trailer "Co-authored-by: Name <email>"
```

Our four lines. GitHub connects all four to the right account, checked on the commits in PR 2:

```text
Co-authored-by: Aira Franco <adelosofranco@gmail.com>
Co-authored-by: Christoffer Carlsson <christoffer.carlsson88@gmail.com>
Co-authored-by: Johnny Hyytiäinen <Johnny.Hyytiainen@gmail.com>
Co-authored-by: Putu Indira Mahadiva Arysaputri <indiramahadiva1@gmail.com>
```

## Presentation and reflection

- **Everyone presents.** It is a G requirement. 10-15 minutes with a demo and a short walkthrough of the code.
- **The individual reflection** is half a page to one page about your contribution and about the group. Your PR list is your log: search `is:pr author:<your-github-name>` under Pull requests.
- **The submission:** the link to the public repo, the reflection, the presentation, and KC invited to the repo.

## To decide at the meeting

Everything in the document is approved at the meeting. These are the points where we need to choose.

- [x] **The columns on the board.** Proposal: Todo, In progress, In review and Done, as in the picture above.
- [x] **How quickly do we review?** Proposal: within a day on weekdays. If you don't have time, say so in Discord and someone else takes it.
- [x] **The language in the repo.** Proposal: English in code, comments, commits, PRs and `docs/`. The repo is public and is submitted.
- [x] **The demo.** Proposal: each track owner shows their own track, so everyone presents naturally.
- [x] **KC in the repo.** Proposal: Christoffer, who owns the repo, invites KC in phase 0.

## Approved

Tick your name when you have read and approved. If something changes after the meeting, everyone ticks again.

- [x] Aira
- [x] Christoffer
- [x] Indira
- [x] Johnny
