---
name: pr-watch
description: 'Use for ongoing cross-project PR discovery and automatic reviews: "watch my PRs", "keep checking my pull requests", "auto-review my PRs until I say stop", "stop watching PRs", or "PR watch status".'
---

# PR Watch

Find and review open PRs across active projects, then check every five minutes until the user stops the watch. Invoking this workflow authorizes COMMENT reviews on the scoped PRs. Honor a private-review request.

1. **Start or resume.** Read [watch.md](references/watch.md). Reuse this chat's existing scope, state and automation. Otherwise discover current projects and GitHub remotes, including active mirrors and private repositories. Exclude unrelated accessible and legacy repositories. Store scope privately in the workspace, never in this public skill.
2. **Check now.** Prefer the GitHub connector where it covers the repository and operation; use authenticated `gh` for omissions or granular data. Compare heads, actual bases, discussions, review threads and CI with saved state. `scripts/poll.py` provides a read-only CLI fallback. Check CI even when code is unchanged.
3. **Delegate changed work.** Use bounded internal subagents for independent PR reviews. Give each its current head, actual base, prior findings and repository instructions. Workers return evidence; the parent consolidates and publishes. Follow [review.md](references/review.md), applying `pr-review` and `engineering:code-review` when installed.
4. **Persist.** Save completed checks without marking unreviewed heads reviewed. Reuse or create one native thread heartbeat at five-minute intervals. Confirm scheduling succeeded. Stay quiet on unchanged or non-actionable state; notify only about actionable findings, verified fixes, meaningful CI/merge/closure changes, failure or required action. Link reviews.
5. **Stop or status.** “Stop watching PRs” deactivates the matching heartbeat and cancels pending publications. Verify it stopped. “PR watch status” reads scope, last check, pending work and scheduler state without starting another watch.

Preserve checkouts. This skill authorizes reviews, not source changes, merges, thread resolution, deployments or production operations.
