# auto-research/ — experiment agent's territory

All study scripts live here. They import the upstream model from
`/home/work/research/code/HVI-CIDNet` (never edited in place) and write runs under
`/home/work/research/outputs/<study>/<run>/<job>/` in the layout given in `HVI-PLAN.md` §2,
so that `tooling/export_results.py` can ingest them.

Layout:
- `<study>.py` — one script per study; `--preflight` (CPU, synthetic), `--smoke` (1 epoch),
  `--init-run`, `--worker`. Every run pins the script sha256 and the upstream commit.
- `analysis/` — scripts that turn `ralph/results/<run>.json` into `<run>__analysis.json`
  (seed means/SD, paired deltas). Each writes a `sources` block with input sha256s.
- `plots/` — scripts that read `ralph/results/*.json` (never raw CSVs) and write
  `writing/figures/*.pdf`.
- `final_eval_test.py` — the ONLY script allowed to read the test split; run once per
  reported configuration after the plan's Gate C; writes `ralph/results/final_eval__test.json`.
