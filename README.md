# XING: Agentic Cognitive Infrastructure

**XING: An Agentic Cognitive Infrastructure for Distributed Multimodal Intelligence and Adaptive AI Orchestration**

IEEE Conference Paper — ICCIA 2026

## Package Structure

```
xing_iccia2026_package/
├── main.tex                 # Main LaTeX manuscript (IEEE format)
├── main.pdf                 # Compiled manuscript
├── references.bib           # BibTeX bibliography
├── IEEEtran.cls             # IEEE conference class file (download required)
├── xing_simulator.py        # Complete stochastic simulation framework
├── replication_note.txt     # Step-by-step replication instructions
├── README.md                # This file
│
├── figures/                 # Generated figures directory
│   ├── fig1_architecture.pdf       # Global runtime architecture
│   ├── fig2_self_healing.pdf       # Self-healing DAG lifecycle
│   ├── fig3_memory_fabric.pdf      # Semantic memory fabric
│   ├── fig5a_rai_comparison.pdf    # RAI experimental results
│   ├── fig5b_gre_analysis.pdf      # GRE self-healing analysis
│   ├── fig5c_cost_crl_analysis.pdf # Cost & CRL analysis
│   ├── results_summary.tex         # LaTeX summary table
│   └── architecture_data.json      # Diagram descriptors
│
└── xing_experiment_results.csv     # Raw experimental data
```

## Quick Start

### 1. Run the simulator

```bash
pip install numpy networkx pandas matplotlib scipy
python xing_simulator.py
```

### 2. Compile the LaTeX paper (Windows)

```powershell
.\compile.ps1
```

Or manually:
```bash
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

### 3. Generate architecture figures (optional)

```bash
python generate_figures.py
```

## Core Contributions

1. **Formalized Distributed Cognitive Runtime** — Decouples application logic from model execution
2. **Constrained Adaptive Routing** — Multi-objective optimization under infrastructure limits
3. **Semantic Memory Fabric** — Persistent graph memory with probabilistic context decay
4. **Self-Healing DAG Execution** — Topological recovery from runtime failures
5. **Reproducible Simulation** — Stochastic framework with IEEE-quality visualization

## Experimental Results (100 trials, 20 tasks/DAG)

| Metric | XING | Static Baseline | Role Baseline |
|--------|------|----------------|--------------|
| RAI (relaxed) | 7.50 | 0.22 | 0.44 |
| RAI (constrained) | 7.28 | 0.10 | 0.26 |
| RAI delta | -2.9% | -56.2% | -41.6% |
| GRE | 0.67 | N/A (crashes) | N/A (crashes) |
| CRL | 0.05 | N/A | N/A |

Key findings:
- **RAI**: XING maintains near-constant efficiency under infrastructure constraints (-2.9%), while static baselines collapse (-56.2%)
- **GRE**: Self-healing DAG engine achieves 67% topological recovery rate under cascading failures
- **CRL**: Semantic Memory Fabric maintains low context degradation (0.05) across long-horizon tasks
- **Cost**: XING's edge-cloud balancing reduces costs by ~40x compared to cloud-only execution

## License

Academic research — reproducible science for ICCIA 2026.
