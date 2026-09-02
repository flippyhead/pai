---
name: add-skill
description: Use when Peter wants to turn something into a reusable skill and get it into his skills repo — "skillify this", "make this a skill", "add a skill", "save this as a skill", "turn this into a skill", "new skill for X" — or wants an existing personal skill changed.
---

# Add a skill to the repo

Repo: `~/Development/pai` (github.com/flippyhead/pai, **public**). Plugin `peter`.
Skills live at `plugins/peter/skills/<slug>/SKILL.md`. That is the only copy: not
`~/.claude/skills/`, not a claude.ai upload.

## Steps

1. **Slug.** Lowercase, hyphens, verb-first where natural (`file-it`, `post-to-google-group`).
   If `plugins/peter/skills/<slug>/` already exists, edit it instead of creating a twin.
2. **Write `SKILL.md`.**
   - Frontmatter: `name: <slug>` and `description:`. The description lists 3+ phrases
     Peter would actually type, in quotes. It says *when*, not *how*.
   - Body: what to do, in order. Under 300 words. Reference material goes in `references/`.
3. **Public-repo check.** No tokens, passwords, private emails or phone numbers,
   and nothing about a named person Peter wouldn't say to their face.
4. **`RESOLVER.md`.** One row per trigger phrase.
5. **Bump the version.** Patch +1 in `plugins/peter/.claude-plugin/plugin.json`.
   Claude Code and Cowork only re-fetch a plugin when this string changes.
6. **Ship.** Only the skill dir, `RESOLVER.md`, and `plugin.json` — if `git status` shows other changes, leave them out.
   ```bash
   cd ~/Development/pai && git add plugins/peter/skills/<slug> RESOLVER.md plugins/peter/.claude-plugin/plugin.json && git commit -m "Add <slug>" && git push && claude plugin marketplace update pai && claude plugin update peter@pai
   ```
   Cowork syncs the repo on its own; **Update** on the marketplace in Customize → Plugins forces it.
7. **Report:** slug, the trigger phrases, and that it is pushed. New skills load in the next session.

Editing: same steps, commit message `Update <slug>: <what changed>`.
