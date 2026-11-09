---
name: pr-ship
description: Use when an existing PR needs to land — auto-loops wait/fix/push until Codex review and CI are clean, then squash-merges and cleans up the branch + worktree. Replaces fix-pr-reviews and fix-pr-in-worktree.
argument-hint: "[pr-number] [--confirm-merge]"
---

# Ship a PR

Take an existing GitHub PR from "Codex is reviewing" all the way to squash-merged + cleaned up. **Single invocation runs an internal loop** — do not wrap with `/loop`. The loop polls Codex review and CI checks, fixes valid feedback, pushes, repeats until clean, then squash-merges and cleans up.

**REQUIRED BACKGROUND:** Follow `superpowers:receiving-code-review` principles when evaluating feedback — verify before implementing, push back on incorrect suggestions with reasoning, no performative agreement.

See `SPEC.md` next to this file for the full design rationale.

## Arguments

Parse `$ARGUMENTS`:
- `<pr-number>` (optional) — PR to ship. If omitted, use the PR for the current branch (`gh pr view --json number,headRefName`). If no PR is associated, stop and ask the user.
- `--confirm-merge` (optional flag) — print a one-line ready-summary and wait for `y/n` before merging. Default is auto-merge.

## High-level flow

```dot
digraph pr_ship {
  rankdir=TB;
  "Resolve PR + working dir" [shape=box];
  "Loop: settle → gather → fix" [shape=box];
  "Clean?" [shape=diamond];
  "Bail?" [shape=diamond];
  "Squash merge" [shape=box];
  "Cleanup" [shape=box];
  "Done" [shape=doublecircle];
  "Bail — hand back" [shape=doublecircle];

  "Resolve PR + working dir" -> "Loop: settle → gather → fix";
  "Loop: settle → gather → fix" -> "Clean?";
  "Clean?" -> "Bail?" [label="no"];
  "Clean?" -> "Squash merge" [label="yes"];
  "Bail?" -> "Loop: settle → gather → fix" [label="no"];
  "Bail?" -> "Bail — hand back" [label="yes"];
  "Squash merge" -> "Cleanup";
  "Cleanup" -> "Done";
}
```

## 1. Resolve PR + working directory

```bash
# 1a. PR number
PR=${ARG_PR:-$(gh pr view --json number --jq .number 2>/dev/null)}
[ -z "$PR" ] && { echo "No PR for current branch. Pass a PR number."; exit 1; }

# 1b. Head branch
HEAD_BRANCH=$(gh pr view "$PR" --json headRefName --jq .headRefName)

# 1c. Pick working dir (in order):

# (i) cwd already on the PR branch?
CURRENT=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ "$CURRENT" = "$HEAD_BRANCH" ]; then
  WORK_DIR=$(pwd)
  CREATED_WORKTREE=false

# (ii) existing worktree on this branch?
elif WT=$(git worktree list --porcelain | awk -v b="refs/heads/$HEAD_BRANCH" '
        /^worktree / { p=$2 }
        $0 == "branch " b { print p; exit }
      '); [ -n "$WT" ]; then
  WORK_DIR="$WT"
  CREATED_WORKTREE=false

# (iii) create one
else
  MAIN_ROOT=$(git rev-parse --path-format=absolute --git-common-dir | xargs dirname)
  git -C "$MAIN_ROOT" fetch origin "$HEAD_BRANCH"
  WORK_DIR="$MAIN_ROOT/.worktrees/$HEAD_BRANCH"
  git -C "$MAIN_ROOT" worktree add -b "$HEAD_BRANCH" "$WORK_DIR" "origin/$HEAD_BRANCH" 2>/dev/null \
    || git -C "$MAIN_ROOT" worktree add "$WORK_DIR" "$HEAD_BRANCH"
  mkdir -p "$WORK_DIR/.claude"
  cp "$MAIN_ROOT/.claude/settings.local.json" "$WORK_DIR/.claude/settings.local.json" 2>/dev/null || true
  cp "$MAIN_ROOT/.claude/settings.json" "$WORK_DIR/.claude/settings.json" 2>/dev/null || true
  CREATED_WORKTREE=true
fi
```

All subsequent work uses `$WORK_DIR`. Use `git -C "$WORK_DIR"` defensively — Claude Code's Bash tool persists cwd, but `-C` is robust.

**Why cwd-first:** the user often checks the PR branch out in their main checkout to test the running app. Don't override that with a worktree.

## 2. The loop

### 2a. Settle phase

Poll every 30s. Settled when:

1. **All checks terminal** (no `pending`/`in_progress`):
   ```bash
   gh pr checks "$PR" --json state --jq '[.[] | select(.state=="PENDING" or .state=="IN_PROGRESS")] | length'
   # 0 = settled
   ```

2. **Codex has finished reviewing current HEAD SHA.** Codex (ChatGPT Codex Connector, `chatgpt-codex-connector[bot]`) keeps ONE "Codex Review Summary" issue comment per PR and edits it in place. Its body carries a hidden JSON marker `<!-- codex-review-state:v1 {...} -->` with `code_review.commit_sha` and `code_review.status` (`running` while analyzing). Findings, when any, arrive as a separate PR review with inline comments; with no findings Codex posts nothing else and reacts 👍. So never wait on a PR review — wait on the marker:
   ```bash
   HEAD_SHA=$(git -C "$WORK_DIR" rev-parse HEAD)
   gh api "repos/{owner}/{repo}/issues/$PR/comments" --jq '
     [.[] | select(.user.login=="chatgpt-codex-connector[bot]")
          | select(.body | contains("codex-review-state:v1"))
          | (.body | capture("codex-review-state:v1 (?<j>\\{.*?\\}) -->").j | fromjson).code_review
          | select(.commit_sha=="'"$HEAD_SHA"'" and .status!="running")] | length
   '
   # ≥1 = settled
   ```
   Codex reviews fire on: PR opened for review, draft marked ready, or an `@codex review` comment. Drafts are skipped. Automatic review is enabled per repo at https://chatgpt.com/settings/code-review; on a repo without it, nothing fires on its own — use the nudge below on the first iteration.

3. **≥60s since last check completed** — gives bots time to post.

**Status updates while waiting** (every 2–3 min): `Waiting for checks... 3/7 complete | codex: reviewed HEAD ✓ | 4 min elapsed`.

**Fallback nudge:** if 3 min pass after our latest push with no Codex review of HEAD, post `@codex review` as an issue comment to trigger it. Once per push.
```bash
gh api "repos/{owner}/{repo}/issues/$PR/comments" -f body="@codex review"
```

**Timeout:** 15 min per settle phase. On timeout: print `Settle timeout — proceeding with current state`, continue to 2b. Don't bail — there may still be feedback to fix.

### 2b. Gather feedback (5 sources)

```bash
gh api "repos/{owner}/{repo}/pulls/$PR/comments"     # 1. review threads
gh api "repos/{owner}/{repo}/pulls/$PR/reviews"      # 2. reviews
gh api "repos/{owner}/{repo}/issues/$PR/comments"    # 3. issue comments
gh pr checks "$PR" --json name,state,conclusion      # 4. check runs
gh pr view "$PR" --json mergeable,mergeStateStatus   # 5. mergeability
```

For check failures, fetch logs: `gh run view "$RUN_ID" --log-failed`.

**Reading the current Codex analysis:** the marker's `has_any_findings` / `has_unresolved_findings` say whether there is anything to do. The findings themselves are the `chatgpt-codex-connector[bot]` PR review whose `commit_id` == HEAD (summary in `body`, inline items in `pulls/$PR/comments` with that review's `id` as `pull_request_review_id`). Ignore Codex reviews for older SHAs — addressed or superseded.

Use `mcp__github__pull_request_read` if available (cleaner shape).

### 2c. Exit check (when to merge)

ALL must be true:
- No FIX items in this iteration's categorized feedback.
- All checks `success`/`skipped`/`neutral` (no `failure`/`cancelled`/`timed_out`/`action_required`/`startup_failure`/`stale`).
- Codex review exists for current HEAD SHA (same check as 2a).
- `mergeable == "MERGEABLE"` AND `mergeStateStatus ∈ {"CLEAN", "UNSTABLE"}`.

If true → jump to step 3 (merge). Else → 2d.

### 2d. Categorize feedback

Per `superpowers:receiving-code-review`:

1. Read referenced code in `$WORK_DIR`. Don't trust the reviewer.
2. Check if already fixed in subsequent commits.
3. Evaluate technically for THIS codebase (CLAUDE.md conventions).
4. Categorize each item:
   - **FIX** — valid issue, will address.
   - **SKIP-ALREADY-FIXED** — addressed in a later commit.
   - **SKIP-DESIGN-DECISION** — intentional choice; reply with reasoning.
   - **SKIP-INCORRECT** — reviewer is technically wrong; reply with reasoning.
   - **SKIP-SUBJECTIVE** — style preference without clear benefit; reply briefly.

**SKIP-\* items are replied-to but DO NOT block the merge gate.** Priority for FIX: Security > Bugs > CLAUDE.md violations > Code quality > Style.

**Track each item by a stable fingerprint** (used by 2g bail check):
- Review-thread comment: `(file, line, comment_id)`.
- Codex review-body finding: `(file, line, normalized first ~60 chars of finding text)`.
- Check failure: `(check_name, first non-empty error line)`.

### 2e. Resolve merge conflicts (if any)

If `mergeable == "CONFLICTING"` or `mergeStateStatus == "DIRTY"`, conflicts come BEFORE other fixes:

```bash
git -C "$WORK_DIR" fetch origin
BASE=$(gh pr view "$PR" --json baseRefName --jq .baseRefName)
git -C "$WORK_DIR" merge "origin/$BASE"
```

If conflicts: read each conflicted file, understand both sides, keep intent of both where possible. If base removed code → keep the removal (likely intentional). If both sides materially changed the same lines and intent isn't obvious → **bail** (2g condition 3). After resolution, run verification gates, commit, push, loop back to 2a.

### 2f. Fix valid issues + verify + push

For each FIX item:
1. Read the file(s) first. Don't edit blind.
2. Make minimal, focused edits — don't expand scope.

Then run CLAUDE.md verification gates from `$WORK_DIR`. For foster-clarity:
```bash
pnpm check-types && pnpm lint && pnpm test && pnpm format:check
# Plus pnpm build if apps/web was touched
```

If any gate fails → fix isn't done. Iterate until gates pass.

```bash
git -C "$WORK_DIR" add <specific files>
git -C "$WORK_DIR" commit -m "fix: address PR review comments

<one-line per fixed item>

Co-Authored-By: Claude <noreply@anthropic.com>"
git -C "$WORK_DIR" push origin "$HEAD_BRANCH"
```

### 2g'. Resolve threads / reply

#### Review threads (resolvable, inline)

For FIX items, resolve via GraphQL:
```bash
# Fetch thread node IDs
gh api graphql -f query='
  query($owner:String!,$repo:String!,$pr:Int!) {
    repository(owner:$owner,name:$repo) { pullRequest(number:$pr) {
      reviewThreads(first:100) { nodes { id isResolved
        comments(first:1) { nodes { databaseId body path line } } } } } }
  }' -f owner=<owner> -f repo=<repo> -F pr=$PR

# Resolve
gh api graphql -f query='
  mutation($id:ID!) { resolveReviewThread(input:{threadId:$id}) { thread { isResolved } } }
' -f id="$THREAD_NODE_ID"
```

For SKIP items, reply explaining why:
```bash
gh api "repos/{owner}/{repo}/pulls/$PR/comments/$COMMENT_ID/replies" \
  -f body="Not addressed — <reason: e.g., intentional design choice because X>."
```

#### Issue comments (not resolvable)

Reply once with fixed + skipped summary:
```bash
gh api "repos/{owner}/{repo}/issues/$PR/comments" -f body="$(cat <<'EOF'
Addressed the review feedback:

**Fixed:**
- <item>: <what was done>

**Not fixed (with reasoning):**
- <item>: <reason>
EOF
)"
```

Always reply, even if everything was skipped. Don't reply if the comment had no actionable feedback.

#### Review bodies

If body had actionable feedback, reply as issue comment summarizing. Skip if it was just APPROVE / "lgtm".

### 2g. Bail conditions

Check before looping back to 2a:

1. **Same feedback survived two rounds.** Compare iteration N's fingerprint set to N+1's. If any item we attempted to fix in N reappears in N+1 → bail.
2. **CI check failed AND we can repro locally.** For each red check, try to reproduce in `$WORK_DIR`. If local reproduction also fails after our fix → bail. (Vercel-only failures we can't repro → also bail; needs human to check env.)
3. **Merge conflict needs human judgment.** If both sides of a conflict materially changed the same lines and intent isn't obvious → bail.

**Bail action:**
1. Stop the loop. Do NOT merge.
2. Post status comment on PR:
   ```
   /pr-ship paused — needs human review:
   • <bail reason>
   • <what was attempted>
   • <what's left unresolved>
   ```
3. Print same summary to terminal + PR URL.
4. If `CREATED_WORKTREE=true`, leave the worktree in place.
5. Exit non-zero.

### Otherwise — loop back to 2a

If no bail and there's still feedback or CI is red, return to 2a. The next settle phase waits for the new push to be reviewed.

## 3. Squash merge

Reached only when 2c's exit check passed.

### Default mode

```bash
gh pr merge "$PR" --squash --delete-branch
```

`--delete-branch` deletes the **remote** branch. Local + worktree cleanup is step 4.

### `--confirm-merge` mode

Print one-line summary and prompt:
```
PR #$PR is clean.
• codex ✓ on $HEAD_SHA
• <N> checks green
• <M> comments resolved (<F> fixed, <S> skipped with reasoning)
• Last commit: <abbrev SHA> "<msg>"

Squash-merge now? [y/N]
```

Wait for `y` (case-insensitive). Anything else → exit without merging, leave PR + worktree as-is.

If `y` → run the same `gh pr merge --squash --delete-branch`.

### Verify merge

```bash
gh pr view "$PR" --json state,mergedAt --jq '.state + " " + (.mergedAt // "never")'
# Expected: "MERGED <timestamp>"
```

If not merged (e.g., race condition where a check went red between exit check and merge) → report error, bail, don't continue to cleanup.

## 4. Cleanup

```bash
# 4a. Find main checkout root (always first entry in worktree list)
MAIN_ROOT=$(git -C "$WORK_DIR" worktree list --porcelain | awk '/^worktree / { print $2; exit }')

# 4b. Switch to default branch in main checkout
DEFAULT=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
git -C "$MAIN_ROOT" checkout "$DEFAULT"
git -C "$MAIN_ROOT" pull origin "$DEFAULT"

# 4c. Delete the worktree FIRST (if we created it), then the branch.
# Order matters: branch -D fails if the branch is checked out anywhere.
if [ "$CREATED_WORKTREE" = "true" ]; then
  git -C "$MAIN_ROOT" worktree remove "$WORK_DIR" --force
fi
git -C "$MAIN_ROOT" branch -D "$HEAD_BRANCH"

# 4d. Prune stale remote refs
git -C "$MAIN_ROOT" fetch --prune
```

If `WORK_DIR == MAIN_ROOT` (user was on the PR branch in main checkout), no worktree to remove — the `checkout DEFAULT` step already moved them off the doomed branch.

## 5. Final report

```
✓ PR #N squash-merged: <pr URL>
✓ Branch <HEAD_BRANCH> deleted (local + remote)
[✓ Worktree removed: <path>]   ← only if CREATED_WORKTREE
✓ Now on <DEFAULT> @ <new sha>

Summary:
  <N> rounds of fixes
  <F> issues fixed, <S> skipped with reasoning
  <C> checks green
  Total time: <duration>
```

## Important notes

- All file reads/edits during the loop must use paths within `$WORK_DIR`.
- Run verification gates from `$WORK_DIR`, not the main checkout.
- Don't run `pnpm dev` / `pnpm deploy:dev` from a worktree if the main checkout's dev server is running — they'll collide on ports / shared backends.
- When pushing back on a suggestion, reply with technical reasoning, not just "skipped".
- The loop is INTERNAL to one invocation. Do NOT use `/loop` to wrap this skill — `/loop` is for skills that do single passes.
- If the user is already inside a worktree on the PR branch when invoking, that worktree is preserved after merge (only the branch is deleted). They might want to keep working there.
