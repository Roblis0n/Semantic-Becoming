#!/bin/sh
# Rebuild the current corrected paper/main.tex; do NOT regenerate from historical paper_input.md.
set -eu
D=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$D/../../../.."
export TEXMF='{/usr/share/texlive/texmf-dist,/usr/share/texmf}'
export TEXMFVAR="$D/texmf-var" TEXMFCONFIG="$D/texmf-config" XDG_CACHE_HOME="$D/cache"
mkdir -p "$D/render" "$D/cache"
xetex -ini -etex -no-shell-escape -interaction=nonstopmode -halt-on-error -jobname=xelatex -output-directory="$D/render" xelatex.ini > "$D/format_build.txt" 2>&1
for pass in 1 2 3; do
 xetex -fmt="$D/render/xelatex.fmt" -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory="$D/render" paper/main.tex > "$D/latex_pass${pass}.txt" 2>&1
done
