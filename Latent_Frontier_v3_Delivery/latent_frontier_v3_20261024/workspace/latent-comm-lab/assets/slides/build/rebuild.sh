#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
: "${CODEX_PRIMARY_RUNTIME_NODE:?Use the existing authorized primary runtime}"
: "${CODEX_PRIMARY_RUNTIME_NODE_MODULES:?Use the existing authorized primary runtime}"
linked=0
if [ ! -e "$here/node_modules" ]; then ln -s "$CODEX_PRIMARY_RUNTIME_NODE_MODULES" "$here/node_modules"; linked=1; fi
cleanup(){ if [ "$linked" -eq 1 ]; then unlink "$here/node_modules"; fi; }
trap cleanup EXIT
python "$here/../../figures/build_media_sources.py"
"$CODEX_PRIMARY_RUNTIME_NODE" "$here/export_decks.mjs" all
