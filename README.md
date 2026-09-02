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

Cowork cannot read this repo while it is private: personal marketplaces are
fetched server-side by claude.ai with no GitHub credential (fails with
"GitHub API rate limit exceeded" / open bug anthropics/claude-code#28125).
Private-repo sync exists only for Team/Enterprise org marketplaces.

So Cowork gets the whole plugin as one zip upload:

```bash
(cd plugins && zip -r /tmp/peter-plugin.zip peter -x '*.DS_Store')
```

Then **Customize → Plugins → upload option → pick the zip**. Re-upload after
changes. Don't also enable the same skills as claude.ai account skills — the
names collide.

If the repo ever goes public, replace the upload with
**Customize → Plugins → Add marketplace → `flippyhead/pai`**.

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

and re-upload the zip in Cowork.
