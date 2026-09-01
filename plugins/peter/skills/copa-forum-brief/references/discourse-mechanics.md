# Discourse mechanics for the forum brief

Forum: `https://forum.cirruspilots.org` — Discourse, members-only. All reads go through Peter's logged-in Chrome session; there is no stored credential.

## Chrome pattern (proven in the Aug 2026 forum research)

1. `tabs_context_mcp` first. Reuse an existing forum tab only if Peter says to; otherwise `tabs_create_mcp` a new tab on the forum.
2. Fetch JSON with `javascript_tool` in that tab: `await (await fetch('/search.json?q=...')).json()` — same-origin fetch rides the session cookie. Return only the fields you need (map/filter in the page before returning), not whole payloads.
3. **Pace requests ~1.3s apart.** Cap a run at ~25 requests. Discourse rate-limits, and this is the production forum.
4. If a fetch returns HTML or a 403, the session has expired — tell Peter to log in, don't retry in a loop.
5. Browser `window` state is lost on navigation. If accumulating results across many fetches, accumulate in the agent, not in the page.

## Endpoints

- `/site.json` — once per run: category id→name map (ids shift as categories are reorganized; known anchors: Off Topic 17, General Aviation 18, COPA Organization 8).
- `/search.json?q=status:noreplies after:YYYY-MM-DD order:latest` — unanswered topics. Also useful: `in:title` qualifiers, `#category` slugs, `min_posts`.
- `/latest.json?page=N` — recent activity; each topic has `posts_count` (1 = unanswered), `created_at`, `last_posted_at`, `category_id`, `posters[]` (with user ids and descriptions like "Original Poster").
- `/top.json?period=weekly` — for the Recognize section: `like_count`, `op_like_count`.
- `/t/<topic_id>.json` — deep read. `post_stream.posts[]` carries `username`, `name`, `trust_level`, `cooked` (HTML body), `like_count`. First post = the OP. More posts via `/t/<id>/posts.json?post_ids[]=...` batched.
- `/u/<username>.json` — account `created_at` and `trust_level` for new-member detection (account < ~60 days or TL0–1 with few posts ⇒ treat as new).

## Controversy screen (cheap heuristics before deep-reading)

Skip a topic when any of: category is Off Topic **and** reply velocity is high (>20 posts in 48h); title contains moderation/complaint/politics markers (ban, moderation, censorship, flag, "finest hour", political figures/party names); topic JSON shows `has_accepted_answer`-style resolution already; or the deep read surfaces flag/deleted-post gaps and people quoting each other to object. When in doubt, it's a "Passed on" line, not a candidate.

## Board roster (Aug 2026 — for the saturation check)

Dave St. Clair, Jim Grace, Rob Fulton, TJ Shembekar, John Covino, Kelly Nimmo-Guenther, Peter Brown, Doug Beary, Bill King, Mark van Niftrik. Erik Gundersen (President, forum username `erikgun`) posts constantly and does not count against saturation — he's the baseline, not the ceiling. Match by display `name` in post JSON, not just username; verify usernames on first encounter and note them in AI Brain so future runs stop guessing.

Peter's own forum username: verify on first run via `/session/current.json` (returns the logged-in user) and record it in AI Brain.

## Related durable assets

- `copa-member-feedback.db` (COPA '26 folder) — 2020–2026 thread corpus with triage scores; useful for "has this question come up before" context in a draft reply.
- AI Brain — current priorities, aircraft, and any usernames/ids recorded by earlier runs. Check it at the start of every run.
