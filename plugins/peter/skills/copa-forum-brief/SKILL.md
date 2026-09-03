---
name: copa-forum-brief
description: Scan the COPA Discourse forum (forum.cirruspilots.org) through Peter's logged-in Chrome session and produce a "forum brief" — a shortlist of threads worth jumping in on, each with a suggested angle and a draft reply in Peter's voice grounded in prior forum threads and COPA content (Commander, Ask COPA U), plus posts worth recognizing with a like or a short attaboy. Use this whenever Peter asks for a forum brief, asks what he should jump in on or reply to, asks where to be visible on the forums, mentions board presence/participation on the forums, or says anything like "find me threads", "what's worth answering on COPA", or "/forum-brief". Requires the Claude-in-Chrome tools and Peter at his desk with Chrome logged in to the forum.
---

# COPA Forum Brief

## Why this skill exists

In August 2026 Erik Gundersen made the case to the board (the "New Sarah Daniels thread" email chain) that COPA's culture problem is partly a board-presence problem: 501 board posts in 12 months, 63% of them from one member, Peter at 7. His definition of good participation is the spec for this skill: *"regularly participating, answering questions, welcoming members, recognizing good contributions, and modeling the tone"* — as **ordinary members, not police**. Mitchel Sellers added that the real metric is visibility and awareness, not post count.

So the goal is not "get Peter's number up." It is to find the small number of places where a reply from Peter is natural, useful, and easy — so that showing up regularly costs him minutes, not an evening of scrolling.

## What a run produces

One brief, delivered as a message in the conversation (not a file), with three sections:

1. **Jump in** — 3–5 threads, each with: linked title, category, age and reply count, one line on why it fits Peter, a one-line angle, the grounding (the prior threads or COPA sources the draft leans on, linked, with date and post count), and a **draft reply in Peter's voice** (see Voice below).
2. **Recognize** — 2–3 recent posts of real substance (maintenance writeups, trip reports, careful accident analysis, members helping members) worth a like, with a one-sentence attaboy draft for any that merit words. A like alone is fine and say so when it is.
3. **Passed on** — one or two lines noting what was deliberately skipped and why ("three hot threads in Off Topic — controversial, not for this brief"). This keeps the selection honest without turning the brief into a monitoring report.

Never post anything. Drafts are for Peter to edit and post himself; the brief should say nothing that implies otherwise.

## How to run it

Access is through Peter's logged-in Chrome session using the Claude-in-Chrome tools — the same method as the 2026 forum research. Mechanics, endpoints, pacing, and the board roster live in `references/discourse-mechanics.md`; read it before the first fetch.

The shape of a run:

1. **Sweep** — pull the last ~7 days of activity: unanswered/under-answered topics, recent new topics, and the week's top posts. (~10–15 JSON requests, paced.)
2. **Filter** — drop anything that fails a hard rule (below), then score the rest for fit.
3. **Deep-read** — fetch the full topic JSON for the top candidates only, and read every post **untruncated**. Never draft from a title and excerpt, and never decide a thread "has a gap" from the first 400 characters of each reply — the gap is usually in the part that got cut off. Re-fetch right before drafting if more than a few minutes have passed; a 2-post thread can be 7 posts by the time the draft is written.
4. **Ground** — before any draft that points somewhere, answers something, or states a fact, find what COPA already has on it (next section).
5. **Draft and deliver** the brief.

## Ground before you draft

A draft that says "search the forum for X" or "there's a thread on that" without having looked is worse than no draft: it sounds like Peter knows something he doesn't, and a member who follows the pointer and finds nothing learns not to trust him. So every draft that points or claims is grounded first, and the brief shows the grounding under the draft.

- **Forum search is the default.** 2–4 `/search.json` queries per candidate (the poster's phrasing, a quoted form, one with `order:likes`), then read the 1–3 threads that actually match — first post plus the top-liked replies, untruncated. Come out with: the specific prior thread to name (title in quotes so the member can find it), what the forum's consensus actually was, and whether the current thread's replies already covered it. Empty search means the draft doesn't point; it answers from what Peter actually knows, or gives the angle only.
- **Commander for technical claims.** Part numbers, procedures, what the AMM or an SB says: put the question to Commander (mechanics in the reference file) and use its cited answer, not a recollection. One or two questions per run.
- **Other COPA sources when they fit:** Ask COPA U for training/CPPP questions and which SME has answered similar ones; `copa-member-feedback.db` for "how often has this come up"; AI Brain for facts about COPA the organization — never assert one from memory when the brain can be checked.
- **What grounding changes.** Name the thread, not the search. Carry the specific finding, not the topic. If the existing replies already covered the ground, the draft shrinks to a welcome plus one pointer — or the candidate drops to Recognize (like the reply that did the work). Don't point a new member at a thread that turned into a fight; read far enough to know.

## What makes a good candidate

**Wheelhouse.** Peter's natural ground: software, web, and AI tech (including the forum platform itself, membership systems, and anything COPA-digital); event technology (he founded Pathable); avionics and cockpit tech; COPA organization questions where a plain factual answer helps; Goal 2 / "One COPA" and Migration-adjacent topics; Pacific Northwest / San Juans flying and destinations. Check AI Brain for current aircraft and any active COPA priorities before scoring — the wheelhouse drifts and the brain is the source of truth.

**Openness.** The best candidates are questions with zero or few replies after several hours, or threads where the existing replies missed something Peter actually knows. A thread that is already well answered is not a candidate — piling on is noise, not presence.

**New members.** A first topic from a new or near-silent member is a strong candidate even outside the wheelhouse, because a welcome plus a pointer is exactly the "ordinary member" behavior Erik described. Check the poster's account age or trust level. The pointer still has to be grounded — a welcome that points at a thread nobody looked up is the failure mode this skill exists to avoid.

**Thank-yous addressed to the board or COPA.** A member thanking "the Board" or "COPA" for something, with likes and no reply, is a strong candidate: a plain thank-you back plus a real question ("what would you want more of?") is easy, warm, and useful signal.

**Board saturation.** If another board member is already active in the thread, score it down — the point is breadth of presence, not two board members in one place. Roster and known usernames are in the reference file.

## Hard rules — skip entirely, don't score

- **Controversial and political threads.** Heated threads, moderation complaints, callout threads, anything political. Erik's data showed a new member's impression of COPA formed almost entirely by seven controversial topics; Peter deciding to enter one of those is a deliberate choice he makes himself, never something this skill nudges him into. If one is genuinely burning, name it in "Passed on" and stop there.
- **Threads Peter already posted in** (unless someone directly asked him something — then flag it as a reply owed, at the top of the brief, before everything else). A sincere unanswered follow-up in a thread he's in, not aimed at him, may appear as a clearly labelled optional item, never as owed.
- **Anything touching the AI moderation pilot** — Peter runs it; his posts there are governance, not presence.
- **Condolence and accident-fatality threads.** Never draft into grief.

## Voice

Peter's forum voice is his email Register B leaning casual: warm, contractions, hedged corrections ("I think…", "seems like…"), real questions that hand the other person something, and concrete specifics over generalities. Numbers with provenance when he's answering a technical question. 50–150 words — forum posts are shorter than his emails. Signs nothing; forum posts don't get signatures.

Never: "As a board member…" posturing (ordinary member is the whole point — the exception is a direct question about COPA the organization, answered plainly and factually), "I appreciate", "Thanks for raising", restating the poster's question back at them, exclamation-point pileups, or anything that reads like a press release. Never put a fact in Peter's mouth that the run didn't verify — if the draft needs one (who does the work, whether it's paid, what a program covers) and the brain and forum don't say, leave it out or flag it in chat for him to fill in. One draft that sounds canned does more damage than five skipped threads; when a draft won't come out natural, give the angle only and say so.

## Cadence note

If Peter starts asking for this most days, offer once to look into a scheduled version (needs a Discourse API key instead of Chrome). Don't re-offer if he declines.
