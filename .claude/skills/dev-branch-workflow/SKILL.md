---
name: dev-branch-workflow
description: The branching and test-gate workflow for this ticketing-ai repo — every feature starts on a fresh branch cut from `dev` and only `dev`, the full suite (pytest + jest + Playwright) must be green before it merges into `dev`, and green again on `dev` after the merge. Use this skill whenever work on this repo starts, resumes, or finishes: when asked to implement a feature, fix a bug, start a phase, create a branch, commit, merge, integrate, or release — and also when about to edit files while sitting on `dev`, `master`, or a branch that was cut from the wrong base. Check the base before writing code, not after.
---

# Dev Branch Workflow

## The rule

Every unit of work lives on its own branch cut from `dev`. Never from `master`, never
from another feature branch, never from wherever HEAD happens to be sitting.

`dev` is the integration branch: it is the only branch whose green test suite means
"these features work *together*". That guarantee is what the workflow protects, and it
is why the suite runs twice — once on the feature branch (does this feature work?) and
once on `dev` after the merge (does it still work next to everything else?).

```
master  ──●─────────────────────────────●──   releases only, tagged
           ╲                           ╱
dev     ────●────────●────────●────────●───   integration; receives merge commits only
             ╲      ╱ ╲      ╱
              ●──●─╯   ●──●─╯                 feature branches, cut from dev
              ↑        ↑
              gate 1: green before merge
                       gate 2: green again on dev after merge
```

## Starting a unit of work

Do this before writing a single line. A branch cut from the wrong base is cheap to fix
in the first minute and expensive to fix after ten commits.

```powershell
git status                      # must be clean; stash or commit first
git switch dev
git pull --ff-only              # or skip if dev has no upstream yet
git switch -c feature/<slug>
git merge-base --is-ancestor dev HEAD   # exits 0 ⇒ correctly based on dev
```

Branch naming follows what's already in this repo's history — `feature/`, `fix/`,
`test/`, `docs/` plus a kebab-case slug (`feature/department-auth`). Run
`git log --oneline --all | head -20` if unsure which prefix fits.

**If `dev` doesn't exist**, stop and say so rather than silently falling back to
`master`: `git branch dev master` creates it, but whether `master`'s tip is the right
base is the user's call.

## While working

Commit after every individual task, not at the end of a batch — each commit should be a
point the suite could be run from. Use conventional-commit subjects (`feat(auth):`,
`test:`, `docs:`) to match existing history.

The fast suites are cheap enough to run per commit; save the full gate for merge time:

```powershell
backend\.venv\Scripts\python.exe -m pytest tests/ -q      # run from backend\
cd frontend; npm test                                      # jest
```

At the end of a phase, write `docs/summaries/phase-N.md` before the merge, so the
summary lands in `dev` with the code it describes.

## Gate 1 — full suite green before merging

All three suites, no exceptions, from a clean tree on the feature branch.

```powershell
# 1. backend — pytest
cd backend; .venv\Scripts\python.exe -m pytest tests/ -v --cov=app

# 2. frontend — jest
cd frontend; npm test

# 3. e2e — Playwright (needs both servers up, see below)
cd e2e; npx playwright test
```

### Bringing up the servers for e2e

`e2e/playwright.config.ts` has no `webServer` block, so Playwright assumes the stack is
already running. Start both in the background, confirm they answer, then run the suite:

```powershell
cd backend; .venv\Scripts\uvicorn.exe app.main:app --port 8000     # background
cd frontend; npm run dev                                            # background, :3000
```

Two things make this suite fail for reasons that have nothing to do with the change:

- `globalSetup.ts` wipes `tickets` and `duplicate_email_log` via the `sqlite3` CLI. If
  `sqlite3` isn't on PATH it prints a warning and carries on against a dirty DB, and the
  failures look like real bugs. Check that warning before debugging anything else.
- The suite is deliberately serial (`workers: 1`) because tests share backend state.
  Don't "speed it up" with parallel workers.

If a suite is red, the merge doesn't happen. Fix it on the feature branch — that's the
whole point of the gate.

## Merging into dev

Bring `dev` into the feature branch *first*, re-run the suite, and only then merge. This
way conflicts and integration breakage get resolved on the feature branch, where a
mistake costs nothing, instead of on `dev`, where it blocks everyone.

```powershell
git switch dev; git pull --ff-only
git switch feature/<slug>
git merge dev                    # resolve conflicts here
# re-run gate 1 if that merge brought in anything
git switch dev
git merge --no-ff feature/<slug>
```

`--no-ff` on purpose: the merge commit keeps the feature legible as one unit in history
and makes it revertable in one move if gate 2 fails. `dev` should contain merge commits
and nothing else — no direct commits.

## Gate 2 — full suite green again on dev

Run all three suites again, now on `dev`. This is not redundant: gate 1 proved the
feature worked against the `dev` you started from, and the merge commit is code that no
suite has ever seen. Semantic conflicts — two features that each pass alone and clash
together — only show up here.

If gate 2 is red, prefer reverting over debugging on a broken integration branch:

```powershell
git revert -m 1 <merge-sha>     # dev is green again immediately
git switch feature/<slug>        # fix, re-run gate 1, merge again
```

Fix forward directly on `dev` only when the break is obvious and one-line.

Once gate 2 is green, delete the merged branch (`git branch -d feature/<slug>`) so stale
branches don't become tempting bases later.

## Releasing — dev to master

`master` only ever receives `dev`, and only with the full suite green on `dev` first:

```powershell
git switch master
git merge --no-ff dev
git tag -a v<x.y.z> -m "<summary>"
```

Pushing and tagging are outward-facing — confirm with the user before either.

## When the base is wrong

A branch accidentally cut from `master` (or from another feature) can be replanted
without losing commits:

```powershell
git rebase --onto dev master feature/<slug>    # replace `master` with the actual old base
git merge-base --is-ancestor dev HEAD          # verify
```

If the branch is already pushed and shared, say so before rewriting it — a rebase of
shared history needs the user's agreement.

## Quick reference

| Moment | Action |
|---|---|
| Before any code | clean tree → `switch dev` → `pull` → `switch -c feature/<slug>` |
| After each task | commit (conventional subject) |
| End of phase | write `docs/summaries/phase-N.md` |
| Before merge | pytest + jest + Playwright all green on the branch |
| Merge | `merge dev` into branch → `merge --no-ff` branch into `dev` |
| After merge | all three suites green on `dev`; revert the merge if not |
| Release | `dev` green → `merge --no-ff` into `master` → tag |
