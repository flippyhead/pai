# `/pr-ship` skill — design

## Problem

Three skills today cover the tail end of a PR's life:

- `fix-pr-reviews` — single-pass: wait for checks/bots, fix feedback, push. Stays on the current branch.
- `fix-pr-in-worktree` — same, but creates a fresh worktree first.
- `post-merge-cleanup` — switch back to main, delete merged branch, remove worktree.

The friction:

1. **Looping is external.** You wrap `fix-pr-reviews` in `/loop 10m` and stop the loop yourself once the PR is clean.
2. **The merge step is manual.** After the loop reports "clean," you go to GitHub and click "Squash and merge."
3. **Two skills for the same job.** Whether to invoke `fix-pr-reviews` or `fix-pr-in-worktree` depends on whether you're already in a worktree — that's a decision the skill should make, not you.
4. **Cleanup is a separate step.** Even after merge, branch + worktree cleanup is its own command.

The user wants one skill that takes a PR from "qodo is reviewing" all the way to "merged, on main, branch + worktree gone."

## Solution

A single skill, `/pr-ship`, that auto-loops through review-fix-push until the PR is clean, then squash-merges and cleans up. Worktree-aware: uses cwd if it's already on the PR branch, otherwise reuses or creates a worktree.

### Invocation

```
/pr-ship [pr-number] [--confirm-merge]
```

- `pr-number` — optional. Defaults to the PR for the current branch via `gh pr view --json number`.
- `--confirm-merge` — optional. Prints a one-line ready-summary and waits for `y/n` before merging. Default is auto-merge.

### What it replaces

- `fix-pr-reviews` — disabled (renamed to `.disabled`).
- `fix-pr-in-worktree` — disabled.
- `post-merge-cleanup` — kept as standalone, since users sometimes work through PRs without `/pr-ship`.

## Flow

### 1. Resolve PR + working directory

1. If `pr-number` arg present, use it. Else `gh pr view --json number,headRefName`.
2. Fetch PR head branch.
3. Pick working directory (in order):
   - If cwd's branch == PR head branch → **use cwd**. Covers worktree-on-branch AND main-checkout-on-branch (user often checks PR branch out in main to test the running app — don't override that).
   - Else if a worktree on that branch exists → cd there.
   - Else → create a worktree at `.worktrees/<branch>/`, copy `.claude/settings*.json`, cd there.
4. Track `CREATED_WORKTREE` for the cleanup step.

### 2. Loop body

```
┌─ 2a. Settle: wait for checks + qodo on current HEAD SHA
├─ 2b. Gather feedback (5 sources)
├─ 2c. Exit check: clean → merge
├─ 2d. Categorize feedback
├─ 2e. Resolve merge conflicts (bail if non-trivial)
├─ 2f. Fix FIX items, verify locally, push
├─ 2g'. Resolve threads / reply to comments
├─ 2g. Bail check: same feedback twice? local CI repro fail?
└─ Loop back to 2a
```

#### 2a. Settle phase

Poll every 30s, max 15 min per phase. "Settled" requires:

1. All check runs in a terminal state (no `pending`/`in_progress`).
2. Qodo's persistent review reflects current HEAD SHA. Two acceptable signals — combined as OR, never AND:
   - **Canonical (always works):** persistent comment whose body starts with `<h3>Code Review by Qodo</h3>` has `updated_at > head commit's committer.date`. Qodo always edits this comment in place after re-analyzing — present on every iteration.
   - **Optional fast-path:** issue comment whose body starts with `**[Persistent review]` and contains the full HEAD SHA. Posted inconsistently — appears on some pushes but not others. When present, accept early; when absent, fall back to the canonical signal. **Never block on this alone.**
3. ≥60s since the last check completed.

**Fallback nudge:** if 3 min pass after our push with no qodo activity on the new SHA, post `/review` as an issue comment. Once per push.

**Timeout:** 15 min per settle phase → proceed with whatever exists, note timeout. No global wall-clock cap.

#### 2b. Gather feedback (5 sources)

| Source | API | Used for |
|---|---|---|
| Review threads | `gh api repos/{o}/{r}/pulls/{pr}/comments` | Inline comments — resolvable via GraphQL |
| Reviews | `gh api repos/{o}/{r}/pulls/{pr}/reviews` | APPROVE / REQUEST_CHANGES verdicts + body |
| Issue comments | `gh api repos/{o}/{r}/issues/{pr}/comments` | Bot reviews (qodo) — not resolvable, must reply |
| Check runs | `gh pr checks {pr} --json name,state,conclusion` | CI/build/lint/deploy failures |
| Merge state | `gh pr view {pr} --json mergeable,mergeStateStatus` | Detect conflicts |

#### 2c. Exit check

Exit to merge step when **all** are true:
- No FIX items in latest gather.
- All checks green (no `failure`/`cancelled`/`timed_out`/etc.).
- Qodo's persistent comment reflects current HEAD SHA.
- `mergeable == MERGEABLE` AND `mergeStateStatus` ∈ `{CLEAN, UNSTABLE}`.

#### 2d. Categorize

Per `superpowers:receiving-code-review`:

- **FIX** — valid issue, will address.
- **SKIP-ALREADY-FIXED** — addressed in subsequent commits.
- **SKIP-DESIGN-DECISION** — intentional choice; reply with reasoning.
- **SKIP-INCORRECT** — reviewer is technically wrong; reply with reasoning.
- **SKIP-SUBJECTIVE** — style preference without clear benefit; reply briefly.

SKIP-* items are replied-to but do not block the merge gate. Priority for FIX: Security > Bugs > CLAUDE.md convention violations > Code quality > Style.

#### 2e–2f. Fix + verify + push

- Resolve merge conflicts first (if any).
- Read files first; minimal focused edits.
- Run CLAUDE.md "Verification before marking work complete" gates.
- Commit + push.

#### 2g'. Resolve threads / reply

- Review threads (resolvable): for FIX, resolve via GraphQL `resolveReviewThread`. For SKIP, reply with reasoning.
- Issue comments (not resolvable): reply once summarizing fixed + skipped. Always reply.
- Review bodies: reply if body had actionable feedback; skip pure APPROVE.

#### 2g. Bail conditions

Three:
1. **Same feedback flagged twice in a row.** Track each item by stable fingerprint. If iteration N+1 reflags what we fixed in N → bail.
2. **CI failure that also fails locally** after our fix (or Vercel-only failures we can't repro) → bail.
3. **Merge conflict needs human judgment** (both sides materially changed same lines, intent unclear) → bail.

Bail = stop loop, post status comment on PR, print summary, do **not** merge, leave worktree if we created it, exit non-zero.

### 3. Merge

- **Default:** `gh pr merge <pr> --squash --delete-branch`.
- **`--confirm-merge`:** print one-line summary and wait for `y/n` before merging.
- Verify merge succeeded (`gh pr view <pr> --json state` → `MERGED`).

### 4. Cleanup (after successful merge)

1. Find main checkout root from `git worktree list --porcelain` (first entry).
2. `cd <main-checkout-root>`.
3. `git checkout main && git pull origin main`.
4. `git branch -D <headRefName>` — force, because squash creates new SHA.
5. `git fetch --prune`.
6. **Only if `CREATED_WORKTREE=true`:** `git worktree remove <path> --force`. If user was already in a worktree, leave it alone.

### 5. Final report

```
✓ PR #N squash-merged: <pr-url>
✓ Branch <headRefName> deleted (local + remote)
[✓ Worktree removed: <path>]   ← only if we created it
✓ Now on main @ <new-sha>

Summary: <N> rounds, <F> fixed, <S> skipped, total time <duration>
```

## Detection signals (this project)

- **Bot login:** `qodo-code-review[bot]`. Different from open-source `pr-agent`'s `qodo-merge-pro[bot]` — verified empirically on PRs #37–39 in `flippyhead/foster-clarity`.
- **Persistent review comment:** body starts with `<h3>Code Review by Qodo</h3>`. Updated in place on every push.
- **Per-push pointer markers (inconsistent):** body starts `**[Persistent review]` and contains the full head SHA. Posted on some pushes but not others — do not rely on its presence.
- **No check run.** Qodo doesn't post a GitHub check.

**Design constraint driving the settle algorithm:** qodo does NOT post a fresh analysis comment per push. On each push it edits the existing Code Review comment in place — same `id`, advancing `updated_at`, body replaced with the new findings. It may *additionally* post a short "Persistent review updated to latest commit `<SHA>`" pointer comment, but empirically this is inconsistent (observed missing on PR #148 iteration 2 in `consumer-bot/consumer.bot`, where qodo edited Code Review to `🐞 Bugs (0)` but never posted a pointer).

This rules out two naive approaches:

1. "Poll comments, take the newest, look for findings." The newest comment by `created_at` is either an unrelated PR comment or the pointer (no findings); the comment with the findings is older.
2. "Block until the pointer names current HEAD SHA." The pointer doesn't always appear — the loop hangs even though qodo has fully caught up.

The correct canonical signal is the in-place `updated_at` advance on the `<h3>Code Review by Qodo</h3>` comment past the HEAD commit's authored time. The pointer can be used as an OR fast-path, but never required.

## What's deliberately not in v1

- No commit-message customization (uses PR title).
- No `--dry-run` (`--confirm-merge` covers it).
- No interactive feedback re-categorization.
- No multi-PR mode.
- No deploy verification (use `/land-and-deploy` separately).
