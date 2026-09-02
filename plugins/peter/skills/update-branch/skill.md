---
name: update-branch
description: Update current branch with latest main using rebase (default) or merge (--merge). Works with PR branches or any feature branch.
argument-hint: [--merge] [--base=main]
---

# Update Branch with Main

Bring the current branch up to date with the base branch (default: `main`) using rebase (default) or merge.

## Arguments

- `$ARGUMENTS` - Optional arguments:
  - `--merge` - Use merge instead of rebase (default is rebase)
  - `--base=<branch>` - The base branch to update from (default: `main`)

## Workflow

### 0. Parse Arguments

Parse `$ARGUMENTS` to extract:
- **Strategy**: If `--merge` is present, use merge. Otherwise, use rebase.
- **Base branch**: Extract from `--base=` flag, or default to `main`.

### 1. Gather Context

```bash
# Check current branch
git branch --show-current

# Check for uncommitted changes
git status --porcelain

# Check if there's an associated PR
gh pr view --json number,title,headRefName,baseRefName 2>/dev/null || echo "No PR"

# See how far behind base we are
git fetch origin
git rev-list --count HEAD..origin/<base-branch>
```

### 2. Stash Uncommitted Changes (if any)

If there are uncommitted changes:

```bash
git stash push -m "update-branch: auto-stash before rebase/merge"
```

Track that we stashed so we can pop later.

### 3. Fetch Latest Base Branch

```bash
git fetch origin <base-branch>
```

### 4. Update Branch

**Rebase (default):**

```bash
git rebase origin/<base-branch>
```

**Merge (`--merge`):**

```bash
git merge origin/<base-branch> --no-edit
```

### 5. Handle Conflicts

If the rebase or merge produces conflicts:

1. List conflicting files:
```bash
git diff --name-only --diff-filter=U
```

2. For each conflicting file, follow the same resolution strategy as the `resolve-conflicts` skill:
   - Read the conflicted file to understand both sides
   - Check git log for context on both changes
   - Apply intelligent resolution (keep both, pick one, or manual merge)
   - Mark resolved:
```bash
git add <resolved-file>
```

3. Continue the operation:

**For rebase:**
```bash
git rebase --continue
```
If there are additional conflicts in subsequent commits, repeat the resolution process.

**For merge:**
```bash
git commit --no-edit
```

### 6. Verify

After successful update, run project verification:

```bash
# Check for remaining conflict markers
git diff --check

# Run project checks (check CLAUDE.md for specifics)
pnpm check-types
pnpm test
```

If verification fails:
- Identify and fix the issue
- Amend the merge commit or continue fixing during rebase
- Re-run verification

### 7. Restore Stashed Changes

If we stashed changes in step 2:

```bash
git stash pop
```

If the pop has conflicts, resolve them.

### 8. Push (with confirmation)

Ask the user before pushing. The push command depends on the strategy:

**After rebase:**
```bash
# Rebase rewrites history, so force-push is needed
git push --force-with-lease origin <current-branch>
```

**After merge:**
```bash
git push origin <current-branch>
```

**Important:** Always use `--force-with-lease` (not `--force`) after rebase to prevent overwriting others' work.

### 9. Report Summary

Provide a summary:

- **Strategy used**: Rebase or Merge
- **Base branch**: Which branch was merged/rebased from
- **Commits incorporated**: How many new commits from base
- **Conflicts resolved**: List of files and resolution strategy (if any)
- **Verification status**: Type check and test results
- **Push status**: Whether changes were pushed
- **PR link**: If associated with a PR, link to it

## Important Notes

- Default to rebase for cleaner history; use `--merge` when the branch is shared or has many commits
- Always use `--force-with-lease` instead of `--force` after rebase
- If rebase produces too many conflicts (>10 commits with conflicts), suggest switching to merge instead
- Never force-push to main/master
- Check with user before pushing, especially after rebase (which rewrites history)
- If the branch has no associated remote, skip the push step
