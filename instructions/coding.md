# When writing code

## Flow
- New work happens in a git worktree on its own branch, never on `main`. Exception: if the current checkout is already on the branch you need (I often test a PR branch in the main checkout), work there.
- Changes land through a pull request. When the work is ready, open the PR without asking and land it with the pr-ship skill. A repo's AGENTS.md may allow docs-only commits straight to `main`.
- Process: superpowers skills for brainstorming, plans, test-first work and debugging; pr-ship for landing. Size the process to the task; a one-line fix doesn't need a plan.
- Make the smallest change that works: reuse what the repo already has, no speculative abstractions, no new dependency for a few lines.
- Before writing setup steps for a tool or service, check what's already configured (env files, commits, deployments) and cover only what's missing.
- Estimate agent work in session-days, from counts in the code (files, call sites, tests). List review and production-risk time separately.

## Git and PRs
- `git fetch` before reasoning from `main`; if the local checkout is behind, read origin's version.
- Commit work in progress (a WIP commit is fine) before stashing, switching branches or starting agents in worktrees.
- Never rename the branch of an open PR (it closes the PR).
- When handling review feedback, read both inline review threads and PR-level comments.
- A review subagent that goes idle without a verdict has failed. Ask once for its conclusions, then start a fresh reviewer; after two failures, review it yourself and say so.
- After a merge, remove only the worktrees you created.

## Done means verified
- Run the repo's verify command (usually `pnpm verify`, or what its AGENTS.md lists) before saying anything is done.
- For UI changes, look at the rendered page (screenshot) before saying it works. For "it's live", load the production page.
- "Update production" means the user-visible result is live: the deploy plus any data, index, file or env-var step behind it. List what differs between dev and prod and close each gap, or name the blocker.
- Type-checking misses Next.js build errors; build, or rely on CI, before calling a Next.js change done.

## Don't break my environment
- Never start, stop or restart my dev servers. Never run `next build` for an app whose `next dev` is running (they share `.next`).
- In a new worktree, run the package install and copy `.env.local` from the main checkout before running anything.
- Subagents start in the main checkout, not your worktree. Begin each subagent's work with `cd <worktree> && git branch --show-current`, and check the main checkout afterwards for stray changes.
- Stacked PRs: retarget the child PR before deleting or squash-merging its base.
- Scripts that run longer than a couple of minutes run in your own session in the foreground, not in a subagent (which backgrounds them and loses the result).
- Large documents and media (PDFs, manuals, video) go in object storage, never in git or Git LFS.
- Set Vercel env values with `printf`, never `echo` (echo stores a trailing newline).
- Browser work uses Claude in Chrome (it has my sign-ins). Sites signed in as a real user (for example Foster prod as Ashley) are read-only.

## Project instructions
- Each repo's AGENTS.md is its source of truth, and CLAUDE.md contains only `@AGENTS.md`. Keep it short: commands, verify, non-obvious gotchas, review rules.
