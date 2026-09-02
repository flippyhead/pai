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

Cowork reads this repo directly as a personal plugin marketplace. One-time:
**Customize → Plugins → Personal plugins "+" → Add marketplace →** `flippyhead/ai-system`,
then install `peter`. Cowork clones on the host with system git, so private-repo
auth comes from the same credential helper `gh auth` set up. Click **Update** on
the marketplace to pull new commits.

Do not also enable the same skills as claude.ai account skills — the names
collide. The plugin is the only copy.

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

and **Customize → Plugins → ai-system → Update** in Cowork.
