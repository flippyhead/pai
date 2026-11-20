#!/usr/bin/env bash
# Keep gstack out of everyday sessions: its skills live only in the planning
# workspace (~/Development/planning). Safe to re-run; run it after /gstack-upgrade,
# which regenerates the global skill folders.
set -euo pipefail

GSTACK=~/.claude/skills/gstack                 # the install itself stays put (skills call its bin/ by path)
WS=~/Development/planning
ARCHIVE=~/.claude/skills-archive/$(date +%Y-%m-%d)
PLANNING="office-hours spec autoplan plan-ceo-review plan-eng-review plan-design-review plan-devex-review design-consultation design-shotgun diagram make-pdf gstack-upgrade"

mkdir -p "$WS/.claude/skills" "$ARCHIVE/claude" "$ARCHIVE/agents"
[ -d "$WS/.git" ] || git -C "$WS" init -q          # gstack skills expect a git repo

# Global ~/.claude/skills: every folder whose SKILL.md links into gstack is a generated shell.
for d in ~/.claude/skills/*/; do
  d=${d%/}; name=$(basename "$d")
  [ "$name" = gstack ] && continue
  [[ "$(readlink "$d/SKILL.md" 2>/dev/null)" == "$GSTACK"* ]] || continue
  if [[ " $PLANNING " == *" $name "* ]]; then
    rm -rf "$WS/.claude/skills/$name"; mv "$d" "$WS/.claude/skills/$name"; echo "planning: $name"
  else
    rm -rf "$ARCHIVE/claude/$name"; mv "$d" "$ARCHIVE/claude/$name"; echo "archived: $name"
  fi
done

# Codex: the ~/.agents/skills gstack copy points at a bin path that doesn't exist; archive it.
for name in gstack _gstack-command; do
  [ -e ~/.agents/skills/$name ] && { rm -rf "$ARCHIVE/agents/$name"; mv ~/.agents/skills/$name "$ARCHIVE/agents/$name"; echo "archived codex: $name"; }
done
find ~/.agents/skills -mindepth 1 -maxdepth 1 -type d -empty -delete

# Codex reads <repo>/.agents/skills but doesn't follow symlinks, so give it real copies.
rm -rf "$WS/.agents/skills"; mkdir -p "$WS/.agents/skills"
cp -RL "$WS/.claude/skills/." "$WS/.agents/skills/"
grep -qx '.agents/' "$WS/.gitignore" 2>/dev/null || echo '.agents/' >> "$WS/.gitignore"
echo "done. planning skills: $(ls "$WS/.claude/skills" | wc -l | tr -d ' ')"
