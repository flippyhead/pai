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

## Grounding endpoints

- **Forum search** — `/search.json?q=<terms>`; Discourse search is keyword, not semantic, so run 2–4 phrasings per question (the poster's exact words, a `"quoted phrase"`, one with `order:likes`, one with `order:latest`). Results carry `topics[]` with `id`, `title`, `posts_count`, `created_at`. Then `/t/<id>.json` for the match; the first post plus the top-liked replies is enough, but read them **untruncated** — strip `cooked` to text and return the whole thing, not a 300-char slice. Same 1.3 s pacing; grounding fetches count against the ~25-request cap, so budget them (sweep ~12, deep-read ~6, grounding ~6).
- **Commander** — `https://commander.copa.fyi`, logged in through the same Chrome profile (as p@ptb.io; verified 3 Sep 2026). It is a chat UI, not JSON: navigate there, click **Start New Conversation**, type the question, wait for the answer to finish streaming, then `get_page_text`. It searches Cirrus TechPubs, COPA articles, and live member-gated Discourse search, and cites sources — use the cited answer. Slow; one or two questions per run. Ask "what are people saying on the forums about X" to make the forum the primary source.
- **Ask COPA U** — `https://answers.copa.fyi` (experts list at `/experts`). For training/CPPP questions and to see which SME has answered similar ones.
- **`copa-member-feedback.db`** — see below; for "has this come up before" counts, not for drafting text.

## Controversy screen (cheap heuristics before deep-reading)

Skip a topic when any of: category is Off Topic **and** reply velocity is high (>20 posts in 48h); title contains moderation/complaint/politics markers (ban, moderation, censorship, flag, "finest hour", political figures/party names); topic JSON shows `has_accepted_answer`-style resolution already; or the deep read surfaces flag/deleted-post gaps and people quoting each other to object. When in doubt, it's a "Passed on" line, not a candidate.

## Board roster (Aug 2026 — for the saturation check)

Dave St. Clair, Jim Grace, Rob Fulton, TJ Shembekar, John Covino, Kelly Nimmo-Guenther, Peter Brown, Doug Beary, Bill King, Mark van Niftrik. Erik Gundersen (President, forum username `erikgun`) posts constantly and does not count against saturation — he's the baseline, not the ceiling. Match by display `name` in post JSON, not just username; verify usernames on first encounter and note them in AI Brain so future runs stop guessing.

**Verified 3 Sep 2026 (first run):** Peter = `flippyhead` (user id 17785). Dave St. Clair = `dstclair`. Rob Fulton = `robfult`. Erik = `ErikGun`. Not board but frequent: `mwaddell` (Mark Waddell, posts the accident-report threads), `tlewis` (Tim Lewis), `Mark_Wolfgang`. Other board usernames still unverified — match by display `name` and add here when seen.

Category 57 "AI Moderation Test (staff)" is Peter's own pilot fixture category: exclude it from every sweep.

## Related durable assets

- `copa-member-feedback.db` (COPA '26 folder) — 2020–2026 thread corpus with triage scores; useful for "has this question come up before" context in a draft reply.
- AI Brain — current priorities, aircraft, and any usernames/ids recorded by earlier runs. Check it at the start of every run.
