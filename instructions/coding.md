# When writing code

## Flow
- New work happens in a git worktree on its own branch, never on `main`. Exception: if the current checkout is already on the branch you need (I often test a PR branch in the main checkout), work there.
- Changes land through a pull request. When the work is ready, open the PR without asking and land it with the pr-ship skill. A repo's AGENTS.md may allow docs-only commits straight to `main`.
- Process: superpowers skills for brainstorming, plans, test-first work and debugging; pr-ship for landing. Size the process to the task; a one-line fix doesn't need a plan.
- Make the smallest change that works: reuse what the repo already has, no speculative abstractions, no new dependency for a few lines.

## Done means verified
- Run the repo's verify command (usually `pnpm verify`, or what its AGENTS.md lists) before saying anything is done.
- For UI changes, look at the rendered page (screenshot) before saying it works. For "it's live", load the production page.
- Type-checking misses Next.js build errors; build, or rely on CI, before calling a Next.js change done.

## Don't break my environment
- Never start, stop or restart my dev servers. Never run `next build` for an app whose `next dev` is running (they share `.next`).
- In a new worktree, run the package install and copy `.env.local` from the main checkout before running anything.
- Subagents start in the main checkout, not your worktree. Begin each subagent's work with `cd <worktree> && git branch --show-current`, and check the main checkout afterwards for stray changes.
- Stacked PRs: retarget the child PR before deleting or squash-merging its base.
- Browser work uses Claude in Chrome (it has my sign-ins). Sites signed in as a real user (for example Foster prod as Ashley) are read-only.

## Project instructions
- Each repo's AGENTS.md is its source of truth, and CLAUDE.md contains only `@AGENTS.md`. Keep it short: commands, verify, non-obvious gotchas, review rules.
