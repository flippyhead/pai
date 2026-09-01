# ai-system

Source of truth for Peter's personal skills. One marketplace, one plugin.

```
.claude-plugin/marketplace.json   marketplace "ai-system"
plugins/peter/
  .claude-plugin/plugin.json      plugin "peter"
  skills/<slug>/SKILL.md          one dir per skill
RESOLVER.md                       trigger phrase -> skill
```

## Install (Claude Code)

```bash
claude plugin marketplace add flippyhead/ai-system
claude plugin install peter@ai-system
```

Private repo — clone auth comes from `gh auth login` via the git credential
helper. Run `gh auth setup-git` once if background marketplace refreshes fail.

## Cowork

Cowork does **not** read this repo, or `~/.claude/skills/`, or user settings.
It loads only the skills enabled for the claude.ai account. So Cowork is fed by
hand: edit here, then upload the changed skill via **Customize** in the Desktop
sidebar (or claude.ai skills settings).

Verify an upload round-tripped:

```bash
CLAUDE_CODE_SYNC_SKILLS=1 claude -p "ok"
diff -r ~/.claude/skills/synced/*/<slug> plugins/peter/skills/<slug>
```

## Add a skill

```bash
mkdir -p plugins/peter/skills/<slug>
$EDITOR plugins/peter/skills/<slug>/SKILL.md   # frontmatter: name, description
git add -A && git commit -m "Add <slug>" && git push
```

Then, to pick it up:

```bash
claude plugin marketplace update ai-system   # Claude Code
```

and upload it via Customize if it needs to work in Cowork too.
