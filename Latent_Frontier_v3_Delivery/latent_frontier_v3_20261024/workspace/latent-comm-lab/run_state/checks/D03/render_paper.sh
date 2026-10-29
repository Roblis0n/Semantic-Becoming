#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
pandoc run_state/checks/D03/paper_input.md --from=markdown --to=latex --standalone --shift-heading-level-by=-1 --toc --toc-depth=1 --metadata title='Semantic Becoming 可改写认知的跨模型计算' --metadata subtitle='前沿机制提案 / 无模型实测' --metadata date='2026年10月24日' -V documentclass=article -V fontsize=10pt -V geometry:margin=22mm -V mainfont='Noto Serif CJK SC' -V sansfont='Noto Sans CJK SC' -V monofont='Noto Sans Mono CJK SC' --include-in-header=run_state/checks/D03/header.tex --lua-filter=run_state/checks/D03/format_tex.lua --output=paper/main.tex
export TEXMF='{/usr/share/texlive/texmf-dist,/usr/share/texmf}'
export TEXMFVAR="$PWD/run_state/checks/D03/texmf-var"
export TEXMFCONFIG="$PWD/run_state/checks/D03/texmf-config"
export XDG_CACHE_HOME="$PWD/run_state/checks/D03/cache"
if [ ! -f run_state/checks/D03/render/xelatex.fmt ]; then
 xetex -ini -etex -no-shell-escape -interaction=nonstopmode -halt-on-error -jobname=xelatex -output-directory=run_state/checks/D03/render xelatex.ini > run_state/checks/D03/format_build.txt 2>&1
fi
for pass in 5 6; do
 xetex -fmt="$PWD/run_state/checks/D03/render/xelatex.fmt" -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory=run_state/checks/D03/render paper/main.tex > "run_state/checks/D03/latex_pass${pass}.txt" 2>&1
done
