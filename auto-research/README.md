# auto-research/ — experiment agent's territory

The existing studies live in `/home/work/research` (`hvi_*.py`, `outputs/`, `code/HVI-CIDNet`,
`env/hvi`) and stay there; `legacy` is a symlink to that directory (gitignored).

Put here:
- `analysis/` — scripts that turn `ralph/results/<run>.json` into `<run>__analysis.json`
  (seed means/SD, paired deltas). Each writes a `sources` block with input sha256s.
- `plots/` — scripts that read `ralph/results/*.json` (never raw CSVs) and write
  `writing/figures/*.pdf`.
- `final_eval_test15.py` — the ONLY script allowed to read `test15`; run once per
  configuration after Gate C; writes `ralph/results/final_eval__test15.json`.
- New protocols — a new script with a new hash and a new run name; never edit
  `hvi_width_trial.py`.
