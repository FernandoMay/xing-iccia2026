# =====================================================================
#  XING ICCIA 2026 - Full Build Pipeline (PowerShell)
# =====================================================================

Write-Host "=== XING ICCIA 2026 Build Pipeline ===" -ForegroundColor Cyan

# ---- Phase 1: Run Simulator (optional) ----
$runSim = $args[0] -eq '-sim'
if ($runSim) {
    Write-Host "[1/4] Running stochastic simulator..." -ForegroundColor Yellow
    python xing_simulator.py 100 20 50
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Simulator failed" -ForegroundColor Red; exit 1 }
    Write-Host "       Done." -ForegroundColor Green
} else {
    Write-Host "[1/4] SKIP: Use '-sim' flag to re-run simulator" -ForegroundColor DarkYellow
}

# ---- Phase 2: Check LaTeX availability ----
Write-Host "[2/4] Checking LaTeX installation..." -ForegroundColor Yellow
$hasLatex = Get-Command pdflatex -ErrorAction SilentlyContinue
if (-not $hasLatex) {
    Write-Host "       WARNING: pdflatex not found. Install MiKTeX or TeX Live:" -ForegroundColor Red
    Write-Host "       Windows: https://miktex.org/download" -ForegroundColor Red
    Write-Host "       Linux:   sudo apt install texlive-latex-base texlive-bibtex-extra" -ForegroundColor Red
    Write-Host "       macOS:   brew install --cask mactex" -ForegroundColor Red
    Write-Host "       Then run this script again." -ForegroundColor Red
    exit 1
}
Write-Host "       pdflatex found: $(Get-Command pdflatex).Source" -ForegroundColor Green

# ---- Phase 3: Download IEEEtran if needed ----
if (-not (Test-Path "IEEEtran.cls")) {
    Write-Host "[3/4] IEEEtran.cls not found. Downloading..." -ForegroundColor Yellow
    $url = "https://raw.githubusercontent.com/rasbt/texknows/master/IEEEtran.cls"
    # Try CTAN as backup
    $ctanUrl = "https://mirrors.ctan.org/macros/latex/contrib/IEEEtran/IEEEtran.cls"
    try {
        Invoke-WebRequest -Uri $url -OutFile "IEEEtran.cls" -UseBasicParsing
    } catch {
        try {
            Invoke-WebRequest -Uri $ctanUrl -OutFile "IEEEtran.cls" -UseBasicParsing
        } catch {
            Write-Host "       Could not download IEEEtran.cls - check your LaTeX distribution has it" -ForegroundColor Yellow
        }
    }
    if (Test-Path "IEEEtran.cls") { Write-Host "       Downloaded IEEEtran.cls" -ForegroundColor Green }
} else {
    Write-Host "[3/4] IEEEtran.cls already present" -ForegroundColor Green
}

# ---- Phase 4: Compile LaTeX ----
Write-Host "[4/4] Compiling LaTeX (3 passes + bibtex)..." -ForegroundColor Yellow
$files = @("main")

foreach ($f in $files) {
    Write-Host "       pdflatex $f (1)" -ForegroundColor DarkGray
    pdflatex -interaction=nonstopmode "$f.tex" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1) {
        Write-Host "       WARNING: pdflatex pass 1 had issues (check $f.log)" -ForegroundColor Yellow
    }

    Write-Host "       bibtex $f" -ForegroundColor DarkGray
    bibtex "$f" 2>&1 | Out-Null

    Write-Host "       pdflatex $f (2)" -ForegroundColor DarkGray
    pdflatex -interaction=nonstopmode "$f.tex" 2>&1 | Out-Null

    Write-Host "       pdflatex $f (3)" -ForegroundColor DarkGray
    pdflatex -interaction=nonstopmode "$f.tex" 2>&1 | Out-Null
}

if (Test-Path "main.pdf") {
    $size = (Get-Item "main.pdf").Length / 1KB
    Write-Host "       SUCCESS: main.pdf generated ($([math]::Round($size, 0)) KB)" -ForegroundColor Green
} else {
    Write-Host "       ERROR: main.pdf not generated. Check .log files for errors." -ForegroundColor Red
    exit 1
}

# ---- Summary ----
Write-Host "`n=== BUILD COMPLETE ===" -ForegroundColor Cyan
Write-Host "  PDF:  main.pdf" -ForegroundColor Green
Write-Host "  LOG:  main.log (check for warnings)" -ForegroundColor DarkGray
Write-Host "  CSV:  xing_experiment_results.csv" -ForegroundColor DarkGray
Write-Host "  FIGS: figures/*.pdf" -ForegroundColor DarkGray
