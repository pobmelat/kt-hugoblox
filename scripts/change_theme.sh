#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT/hugo.yaml"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage: change_theme.sh [default|classic]

Without an argument, prompts for the header theme. The selected theme is written
to hugo.yaml and make build is run automatically.
EOF
  exit 0
fi

choose_theme() {
  if [[ $# -gt 0 ]]; then
    printf '%s\n' "$1"
    return
  fi
  printf 'Select header theme:\n1) default (current header)\n2) classic (one-row header)\n> ' >&2
  read -r selection
  case "$selection" in
    1|default) printf 'default\n' ;;
    2|classic) printf 'classic\n' ;;
    *) echo "Choose 1/default or 2/classic." >&2; exit 1 ;;
  esac
}

theme="$(choose_theme "$@")"
case "$theme" in
  default|classic) ;;
  *) echo "Unknown theme '$theme'. Use default or classic." >&2; exit 1 ;;
esac

python3 - "$CONFIG" "$theme" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
theme = sys.argv[2]
text = path.read_text(encoding="utf-8")
pattern = r'(?m)^  header_style:\s*".*"$'
replacement = f'  header_style: "{theme}"'
if re.search(pattern, text):
    text = re.sub(pattern, replacement, text, count=1)
else:
    text = text.replace("params:\n", f"params:\n{replacement}\n", 1)
path.write_text(text, encoding="utf-8")
PY

echo "Selected '$theme' header theme."
(cd "$ROOT" && make build)
