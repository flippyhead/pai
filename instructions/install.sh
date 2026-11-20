#!/usr/bin/env bash
# Builds each tool's global instructions from the parts in this folder.
# Edit the .md parts, then run: bash instructions/install.sh
set -euo pipefail
cd "$(dirname "$0")"

build() { # build <output-file> <part>...
  local out=$1; shift
  mkdir -p "$(dirname "$out")"
  { echo "<!-- GENERATED from ~/Development/pai/instructions ($*). Do not edit here: edit the parts and run install.sh. -->"
    for part in "$@"; do echo; cat "$part.md"; done; } > "$out"
  echo "wrote $out ($(wc -l < "$out" | tr -d ' ') lines)"
}

build ~/.claude/CLAUDE.md   global coding   # Claude Code: T3, CLI, desktop Code tab
build ~/.codex/AGENTS.md    global coding   # Codex: T3, CLI
build ~/.gemini/GEMINI.md   global coding   # Antigravity / Gemini in T3
build dist/cowork.md        global assistant  # Cowork + claude.ai: paste into Settings > Profile > personal preferences
pbcopy < dist/cowork.md && echo "copied dist/cowork.md to clipboard for claude.ai personal preferences"
