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

```bash
mkdir -p plugins/peter/skills/<slug>
$EDITOR plugins/peter/skills/<slug>/SKILL.md   # frontmatter: name, description
git add -A && git commit -m "Add <slug>" && git push
```

Then, to pick it up:

```bash
claude plugin marketplace update pai   # Claude Code
```

Cowork picks it up on its own.
