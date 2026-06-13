#!/usr/bin/env bash
# =====================================================================
#  XING ICCIA 2026 - Full Build Pipeline (Bash)
#  Usage: bash compile.sh [-sim]
# =====================================================================

set -euo pipefail

echo "=== XING ICCIA 2026 Build Pipeline ==="

# ---- Phase 1: Run Simulator ----
if [[ "${1:-}" == "-sim" ]]; then
    echo "[1/4] Running stochastic simulator..."
    python xing_simulator.py 100 20 50
    echo "       Done."
else
    echo "[1/4] SKIP: Use '-sim' flag to re-run simulator"
fi

# ---- Phase 2: Check LaTeX ----
echo "[2/4] Checking LaTeX installation..."
if ! command -v pdflatex &>/dev/null; then
    echo "       ERROR: pdflatex not found."
    echo "       Install: sudo apt install texlive-latex-base texlive-bibtex-extra texlive-science"
    echo "       Or: brew install --cask mactex"
    exit 1
fi
echo "       pdflatex found: $(which pdflatex)"

# ---- Phase 3: Get IEEEtran if needed ----
if [ ! -f "IEEEtran.cls" ]; then
    echo "[3/4] Downloading IEEEtran.cls..."
    wget -q https://mirrors.ctan.org/macros/latex/contrib/IEEEtran/IEEEtran.cls 2>/dev/null || \
    curl -sL https://mirrors.ctan.org/macros/latex/contrib/IEEEtran/IEEEtran.cls -o IEEEtran.cls
    echo "       Done."
else
    echo "[3/4] IEEEtran.cls found"
fi

# ---- Phase 4: Compile ----
echo "[4/4] Compiling LaTeX (3 passes + bibtex)..."
for f in main; do
    echo "       pdflatex $f (1)"
    pdflatex -interaction=nonstopmode "$f.tex" >/dev/null 2>&1 || true
    echo "       bibtex $f"
    bibtex "$f" >/dev/null 2>&1 || true
    echo "       pdflatex $f (2)"
    pdflatex -interaction=nonstopmode "$f.tex" >/dev/null 2>&1 || true
    echo "       pdflatex $f (3)"
    pdflatex -interaction=nonstopmode "$f.tex" >/dev/null 2>&1 || true
done

if [ -f "main.pdf" ]; then
    size=$(du -h main.pdf | cut -f1)
    echo "       SUCCESS: main.pdf ($size)"
else
    echo "       ERROR: main.pdf not generated."
    exit 1
fi

echo ""
echo "=== BUILD COMPLETE ==="
echo "  PDF:  main.pdf"
echo "  LOG:  main.log"
echo "  CSV:  xing_experiment_results.csv"
