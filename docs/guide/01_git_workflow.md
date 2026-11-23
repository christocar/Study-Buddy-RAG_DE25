# Git workflow: Study Buddy
*Johnny. Last updated 2026-11-22. Same flow as in the Data warehouse lab, adapted to this repo.*

Purpose: how the four of us work in the same repo without overwriting each other's code. And without anyone having to sit in the corner of shame.

## TL;DR

Take an issue, sync `main`, create your own branch, commit small pieces and rebase on `origin/main` before the PR. Merge via PR when CI is green and someone else has reviewed. Delete the branch afterwards.
One branch = one issue = one PR. Code never goes directly to `main`.
Unsure of the situation? `git status -sb` and `git log --oneline --graph --all -15` BEFORE you do anything else.

**Jump straight to:**

1. [The sacred rule](#the-sacred-rule)
2. [Where am I?](#where-am-i)
3. [The daily flow](#the-daily-flow)
4. [Commit convention](#commit-convention)
5. [Pair programming and co-authors](#pair-programming-and-co-authors)
6. [When main has moved (rebase)](#when-main-has-moved-rebase)
7. [Pull Request and merge](#pull-request-and-merge)
8. [Clean up after merge](#clean-up-after-merge)
9. [The panic emergency (FAAFO edition)](#the-panic-emergency-faafo-edition)
10. [One-time fix: repo settings](#one-time-fix-repo-settings)

## The sacred rule

**Code NEVER goes directly to `main`.**

`main` is our finished, working product. All code comes in via a **Pull Request (PR)** from its own branch. If someone pushes broken code directly to `main`, the other three pull it down the next morning, and then we have four broken computers instead of one.

**The exception: last minute fix.** A small change in a document or in the README, which doesn't touch anyone's code, may go directly to `main`. Sync first, commit as `docs` and push directly:

```bash
git checkout main
git pull origin main
git add README.md
git commit -m "docs(readme): fix broken link to setup steps"
git push origin main
```

If you are unsure whether it is a last minute fix, then it is not. Take a branch.

## Where am I?

Three concepts that make the rest of the guide understandable:

- **Hash:** every commit gets a unique ID, e.g. `7e1d4b2` (the short version of a 40-character code). If someone writes "commit 7e1d4b2" in Discord, everyone means exactly the same snapshot.
- **HEAD:** the "You are here" arrow on the map. It points to the branch you are standing on, which in turn points to its latest commit.
- **`main` vs `origin/main`:** `main` is your computer's copy. `origin/main` is your computer's *memory image* of GitHub, from the last time you asked. Neither of them updates by itself, and that is why `git fetch` always comes first.

```bash
git fetch origin                        # ask GitHub what has happened, touches none of your files
git status -sb                          # where do I stand? [ahead 2] = 2 unpushed commits, [behind 1] = GitHub has something I lack
git log --oneline --graph --all -15     # the latest 15 commits as a map
git log --oneline origin/main..HEAD     # what do I have that main doesn't?
git log --oneline HEAD..origin/main     # what does main have that I lack?
```

This is what the map looks like on a regular Tuesday:

```
A---B---C---M          origin/main       (Aira merged her PR yesterday)
     \
      D---E            feat/txt-loader   <-- HEAD (you are here)
```

Your branch starts from `B`. Since then `main` has gained `C` and `M`. `git log --oneline HEAD..origin/main` shows exactly `C` and `M`, and that is your signal to [rebase](#when-main-has-moved-rebase).

## The daily flow

**0. Take an issue**

Open the board, take an issue and set yourself as assignee. If it belongs to another track: tell the owner first, so we never build the same thing twice. Remember the issue's number, for example `#12`.

**1. Sync and create your branch**

```bash
git checkout main
git pull origin main
git checkout -b feat/txt-loader
```

The branch name follows the types in the [commit convention](#commit-convention): `feat/`, `fix/`, `docs/` and so on. (`git switch -c` does the same thing as `checkout -b` and is the newer command. We use `checkout` in the guide so that everyone types the same.)

**2. Stage and commit**

```bash
git status                                                  # what have I changed?
git add src/study_buddy/ingestion/loaders/txt.py            # add specific files
git diff --staged                                           # exactly what ends up in the commit
git commit -m "feat(ingestion): add txt and md loader"
```

**NEVER** use `git add .`. It picks up everything in the folder, including `.env` with the API keys if `.gitignore` has a hole. `git diff --staged` is your last chance to see what comes along, after the commit it sits in the history. Commit often and in small pieces: one commit = one thing.

**3. Run the checks before push**

The same three that CI runs on GitHub. If they pass here, they pass there.

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

If `format --check` complains: run `uv run ruff format .`, and ruff formats for you, and commit the change. The commands are also in `docs/quick_commands.md`.

**4. Push**

```bash
git push -u origin feat/txt-loader
```

`-u` connects your local branch to the one on GitHub, once. After that `git push` is enough. If you forget `-u`, git says *"has no upstream branch"* and prints the command you should run itself. Copy it, done. Then: [open a PR](#pull-request-and-merge).

## Commit convention

We follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): `<type>(<scope>): <what the commit does>`. Scope is the part of the repo it concerns: the tracks' folders `ingestion`, `storage`, `qa`, `frontend` and `api`, or `docker`, `ci`, `deps`, `docs` and `repo`.

| Type | Used when |
|---|---|
| `feat` | new functionality: a loader, an endpoint, a page in Streamlit |
| `fix` | something that was broken works now |
| `docs` | README, comments, documentation |
| `refactor` | the code looks different but does the same thing |
| `test` | tests are added or changed |
| `chore` | cleanup and config: `.gitignore`, dependencies |
| `ci` | GitHub Actions and other automation |

```
feat(ingestion): add txt and md loader          # good
fix(storage): pass filename as sql parameter    # good
fixed stuff                                     # which stuff? when? why?
```

English, imperative ("add", not "added"), lowercase, no period at the end, preferably under 72 characters. Why bother? Because we merge (not squash), **every** commit comes along into `main` forever. Then `git log --oneline` becomes either a table of contents of the project, or a diary full of "fix", "fix2" and "now it works".

## Pair programming and co-authors

The person who writes the code commits it. If two of you have sat on a task, add the other as co-author so both show up on GitHub:

```bash
git commit -m "feat(qa): add retrieval over lancedb" --trailer "Co-authored-by: Name <email>"
```

`--trailer` puts the line last in the commit message, where GitHub looks for it. The email must be one that the person has connected to their GitHub account, otherwise they won't show up. We collect our four lines in way of working, so that nobody has to guess.

## When main has moved (rebase)

The Tuesday map above: while you have been working, Aira has merged, and your branch builds on an old picture of `main`. Rebase lifts up your commits and puts them on top of the latest `main`, as if you had started today.

```bash
git fetch origin
git rebase origin/main
```

```
A---B---C---M          origin/main
             \
              D'--E'   feat/txt-loader (same changes, NEW hashes)
```

**Why `D'` and not `D`?** A hash is calculated from, among other things, which commit it builds on. New parent = new hash. Your branch on GitHub still has the old `D` and `E`, so a regular `git push` is refused. Therefore:

```bash
git push --force-with-lease
```

`--force-with-lease` means "overwrite my branch on GitHub, but only if it looks the way I think". If someone else has managed to push there since your last fetch, it aborts. Regular `--force` overwrites blindly, and on the wrong branch someone else's commits are gone.

**The only rule of rebase:** only rebase **your own** branch. Never `main`, never a branch someone else is working in. Rebase rewrites history, and if you rewrite history that someone else is standing on, their git no longer recognizes its own branch. FAAFO.

**When?** Before you open a PR, and when GitHub says the PR has conflicts. (`git merge origin/main` in your branch also works, but adds an extra merge commit every time. Rebase keeps your branch a straight line, and the PR becomes easier to review.)

## Pull Request and merge

1. After push, GitHub shows a yellow box with **"Compare & pull request"**. Click it. (Or **Pull requests > New pull request**, base: `main`, compare: your branch.)
2. **Title** according to the commit convention. **The description** in English with four headings: *Summary*, *Why*, *Changes* and *How to test*. Write `Closes #12` in the description, and the issue closes by itself when the PR is merged.
3. **Wait for green CI.** GitHub runs ruff and pytest on every PR. Red cross: click **Details**, fix on your branch and push. The PR updates by itself.
4. **Someone other than you reviews and merges.** The reviewer checks: does the code do what the title says? Do any secrets or data files sneak in? Can it be run on my computer?
5. Approved and green? **Merge pull request** with the option **"Create a merge commit"**.

**Why merge and not squash?** All your commits come along into `main`, plus a merge commit that shows exactly when the PR landed. The history shows *how* something was built, not just that it got done. The downside: sloppy commit messages also stay forever.

## Clean up after merge

```bash
git checkout main
git pull origin main
git branch -d feat/txt-loader
git fetch --prune
```

`-d` (small d) only deletes a branch whose commits are already in `main`, a safety catch. If git says *"not fully merged"* you have either forgotten `git pull`, or the PR is not merged yet. Check GitHub. Do **not** force it with `-D` (capital D): it deletes regardless, and if something was actually unmerged it is gone.

`--prune` cleans away your computer's memory image of branches that have already been deleted on GitHub. New issue = new branch from a fresh `main`. Never continue on a merged branch.

## The panic emergency (FAAFO edition)

**"I don't know which branch I'm on!"** `git status -sb`, first line.

**"Everything up-to-date", even though I have written new code!** You have forgotten `git add` and `git commit`. The code is on your computer, but git doesn't know about it yet.

**CI is red on my PR.** Click **Details** and see which step failed:

- `ruff check`: run `uv run ruff check . --fix`. What ruff can't fix by itself is in the error.
- `ruff format --check`: run `uv run ruff format .`.
- `uv sync --locked`: `uv.lock` doesn't match `pyproject.toml`. Run `uv lock` and commit both files.
- `pytest`: a test fails. Run `uv run pytest` locally and read the last lines.

Commit the fix and push. CI runs again by itself.

**I started coding on `main` (nothing committed yet).** No danger. Create a branch right away, the changes come along: `git checkout -b fix/oops-wrong-branch`

**I have COMMITTED code on `main` (not pushed).**
Oops, I goofed up. Don't push. Write in Discord, sit in the corner of shame for a while and run the fix with someone reading over your shoulder. **The order is the whole point:**

```bash
git status                          # must be clean, no uncommitted changes
git branch fix/rescued-commits      # 1. rescue your commits onto a new branch
git reset --hard origin/main        # 2. set main back to GitHub's version
git checkout fix/rescued-commits    # 3. keep working there, as usual
```

Step 1 saves the commits. If you swap steps 1 and 2, they no longer hang on any branch, and have to be fished up with `git reflog` (the last item).

**I have PUSHED code to `main`.** Tell us immediately. The fix is `git revert`, which makes a new commit that removes the change. Never `--force` on `main`. We solve it together.

**`! [rejected] ... (non-fast-forward)` when I push my branch.** If you have rebased: completely expected, run `git push --force-with-lease`. If you haven't rebased, GitHub has commits you lack (did you push from another computer?). Run `git pull --rebase` and push again.

**`Not possible to fast-forward` or `divergent branches` when I run `git pull` on `main`.** Your local `main` has commits that are not on GitHub. So you have committed on `main` without pushing. See above, the corner of shame.

**`CONFLICT (content): Merge conflict in ...` in the middle of a rebase.**
Git has stopped and is waiting for you. Open the file and look for the markers:

```
<<<<<<< HEAD
what was already in main
=======
your change
>>>>>>> 7e1d4b2 (feat(ingestion): add txt and md loader)
```

Yes, during a rebase the upper half is `main` and the lower half is your commit. It feels backwards, but git is standing on `main` and laying your commits on top one at a time. Keep what should stay, delete the markers, run `git add <the file>` and then `git rebase --continue`. Git may stop once per commit, so repeat until it's done. The panic button: `git rebase --abort` puts everything back as it was before you started.

**`You are in 'detached HEAD' state`** You have checked out a hash instead of a branch. Look around as you like. Back: `git checkout <your-branch>`. If you have managed to commit something: run `git checkout -b rescue/detached` first, otherwise the commits become homeless.

**I committed `.env` or a key.** Not pushed, and it was the latest commit: `git rm --cached .env`, add it to `.gitignore`, then `git commit --amend`. Pushed: the key is **burned**. Tell the group immediately, so that it is blocked and replaced. Removing the file in a new commit is not enough, it stays in the history.

**Everything is broken and I don't know what I did.** `git reflog` is git's black box. It shows every place HEAD has stood, even commits you have "lost", and they remain for at least 30 days (but only on your computer). Find the line from before it went wrong and run `git checkout -b rescue/reflog <the-hash-from-that-line>`.

## One-time fix: repo settings

Christoffer owns the repo and does this **once**. Then part of the panic emergency disappears before it has time to happen.

- **Settings > General > Pull Requests:** keep *Allow merge commits*, untick *Allow squash merging* and *Allow rebase merging*. Then there is only one button, and nobody can press the wrong one.
- **Same place:** tick *Automatically delete head branches*. The branch on GitHub disappears when the PR is merged.

Each person, **once**, in the repo: `git config pull.ff only`. Then `git pull` refuses rather than quietly creating a merge commit when your local `main` has drifted apart from GitHub. A loud error now beats a quiet mess in a week.

The whole flow as a mermaid diagram (renders on GitHub): [`01_git_workflow.mmd`](01_git_workflow.mmd)

The whole flow as a .png diagram (renders on GitHub): [`01_git_workflow.png`](01_git_workflow.png)
