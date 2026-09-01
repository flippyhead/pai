---
name: file-it
description: File documents, photos, PDFs, and other files into the correct place in Peter's ~/Documents organization scheme. Use this skill whenever a file needs a home — when Peter says "file this", "put this where it belongs", "organize this", "where should this go", when a file is found in the wrong place (Downloads, Desktop, Archive/review, email attachments, loose at ~/Documents root), or after any task that produces or discovers a file worth keeping. Also use when Peter asks to clean up or triage a folder of unsorted files. Covers moving, renaming cryptic filenames, and flagging sensitive content.
---

# File It — filing into ~/Documents

Peter's ~/Documents has a deliberate organization scheme. This skill files any file into the right place in that scheme: pick the destination, give the file a sensible name, move it, and report what happened.

## Operating mode

**Auto-file and report.** Don't ask for permission on each file — classify it, move it, then tell Peter exactly what moved where (old path → new path) so he can veto after the fact. Moves are easily reversible; a wall of confirmation prompts is not what he wants.

Two exceptions to acting without asking:
- If a file's identity is genuinely unclear even after inspecting it (open images, skim PDFs — don't guess from the filename alone), move it to `Archive/review/` and say so, rather than inventing a category.
- Never **delete** anything. Files that look like junk go to `Archive/to-delete/`.

## Workflow

1. **Check the brain for scheme updates.** Search AI Brain for "Documents organization scheme" (type: reference). Peter evolves the scheme over time; the brain entry wins if it conflicts with this skill's reference file. If AI Brain is unavailable, proceed with the bundled reference.
2. **Inspect the file.** Read images and PDFs to see what they actually are. A filename like `18588976_...o.jpg` tells you nothing; the pixels tell you it's a headshot. For batches, inspect anything whose name is ambiguous.
3. **Classify** using the decision tree in `references/organization-scheme.md`. Read that file before filing anything — it has the full folder map and the edge cases.
4. **Rename if the name is cryptic.** Facebook/social exports, `IMG_xxxx`, download hashes, `Untitled 14` → descriptive kebab-case: `peter-headshot.jpg`, `n224jk-annual-inspection-2025.pdf`. Keep names that are already meaningful (don't churn `617_Cedar_Move_In_Checklist.pdf`). Preserve the extension; include a year when the document is time-bound.
5. **Move it.** Create intermediate folders if a sensible new subfolder is warranted (e.g., a new property number under `Properties/`). Don't overwrite: if the destination name exists, compare — identical content means leave the original and move the newcomer to `Archive/to-delete/`; different content means suffix `-2`.
6. **Flag sensitive content.** If a file contains SSNs, account credentials, recovery codes, passport/license scans, or signatures, file it under `Personal/identity/` or `Personal/security/` as appropriate and explicitly call it out in the report so Peter can decide whether it should live on disk at all.
7. **Report.** One line per file: `old → new` plus a note for anything renamed, flagged, or sent to review. If filing taught you something durable (a new property number, a new project name, a scheme change Peter approved), save it to AI Brain as a brief reference note.

## What goes where (summary)

Full map with edge cases: `references/organization-scheme.md`. The short version:

- **Properties/** — anything tied to a property, in its street-number subfolder (5808, 617, 740, J-4, ...)
- **Aviation/** — aircraft N224JK, hangar, flight plans, training material, aviation insurance
- **Finance/** — taxes (by year), investments, insurance cards, payment/benefit docs, expense trackers
- **Personal/** — identity & security (sensitive), legal & estate, medical, writing, events, car, friends
- **Projects/** — non-code business ventures (Pathable, Brown Town Spa, SJPA, CSI, UrbanX, Fetching, ...)
- **Foster/** — Foster Realty Co
- **Archive/** — old travel, screenshots, recordings, misc, `review/` (unidentified), `to-delete/` (staged)
- **Claude/** — managed by Claude; never file into or reorganize it
- **Code** → `~/Development/`, never ~/Documents

When a file plausibly fits two places, prefer the more specific, active home over Archive, and the subject folder over the format (an invoice for the plane goes to `Aviation/N224JK/`, not `Finance/`).
