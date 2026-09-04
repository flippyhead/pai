# pai

Source of truth for Peter's personal skills. One marketplace, one plugin.

```
.claude-plugin/marketplace.json   marketplace "pai"
plugins/peter/
  .claude-plugin/plugin.json      plugin "peter"
  skills/<slug>/SKILL.md          one dir per skill
RESOLVER.md                       trigger phrase -> skill
```

## Install (Claude Code)

```bash
claude plugin marketplace add flippyhead/pai
claude plugin install peter@pai
```

Private repo — clone auth comes from `gh auth login` via the git credential
helper. Run `gh auth setup-git` once if background marketplace refreshes fail.

## Cowork

**Customize → Plugins → Personal plugins "+" → Add marketplace →** `flippyhead/pai`,
leave "Sync automatically" on, install **peter**. Cowork's backend fetches the
repo anonymously, which is why the repo is public: a private repo fails with
"GitHub API rate limit exceeded" (anthropics/claude-code#28125), and private
sync is Team/Enterprise only.

Don't also enable the same skills as claude.ai account skills — the names collide.

## Add a skill

Say "skillify this" / "add a skill that …" — the `add-skill` skill does the rest.
By hand: new dir under `plugins/peter/skills/<slug>/SKILL.md`, a row in
`RESOLVER.md`, **bump `version` in BOTH `plugins/peter/.claude-plugin/plugin.json`
and the `peter` entry of `.claude-plugin/marketplace.json`** (Claude Code reads
the first, the Cowork backend reads the second; miss either and that surface
never re-fetches), then:

```bash
git add -A && git commit -m "Add <slug>" && git push && claude plugin marketplace update pai && claude plugin update peter@pai
```

Cowork picks it up on its own.
