# auto-research/ — experiment agent's territory

All study scripts live here. They import the upstream model from
`/home/work/research/code/HVI-CIDNet` (never edited in place, commit pinned in `hvilib.COMMIT`)
and write runs under `/home/work/research/outputs/<study>/<run>/<job>/` in the layout given in
`HVI-PLAN.md` §2, so that `tooling/export_results.py --run <study>/<run>` can ingest them.

Layout:
- `hvilib.py` — the shared instrument: repo pin, LOLv1 split (435 train / 50 val from our485,
  eval15 = test, guarded in `open_rgb`), the upstream protocol dict, faithful copies of the
  upstream loss (train.py:60-64), LR schedule (upstream scheduler classes), augmentation and
  metrics (measure.py), colour diagnostics, job bookkeeping. Every study imports it and pins
  its sha256 in the manifest.
- `hvi_baseline.py` — the baseline study / instrument check: `--preflight` (CPU synthetic,
  bitwise checks), `--launch --run R --gpu N [--smoke]` (spawns one detached worker on one
  GPU), `--status`. `--smoke` trains the first 2 epochs of the 1000-epoch schedule (epoch 1
  is lr=0 under the upstream warmup) on the full train/val sets: real cost numbers.
  Flags: `--arm` (default U = upstream model + loss), `--k0`, `--val-every` (default 5),
  `--snapshot-every` (default 10), `--split` (default scene_v1), `--eval-gated` (off: identity
  test-time knobs), `--strict`.
- `c1_arms.py` — C1 ladder: `ArmNet` (CIDNet body transcribed between encode/decode; arms
  A0, A2, A3, A4, L1, R, U), `FrozenLoss` (L_rgb + L_hvi at constant detached k0, no VGG on
  the HVI side), `--preflight` (CPU, one fwd/bwd per arm, parameter-count assertion) ->
  `ralph/results/phase0_arms_preflight.json`. `hvi_baseline.py --arm X` trains an arm.
- `scene_split.py` / `split_scene_v1.json` — scene-disjoint validation split (DINOv2 + pHash
  clusters, 40 val / 445 train); the only script besides final_eval_test.py permitted to touch
  eval15 (listing + GT embedding for clustering, recorded in its JSON).
- `phase0_codebase.py` — writes `ralph/results/phase0_codebase.json` (upstream facts with
  file:line pointers, parameter/MAC counts, latency, the smoke run's cost block).
- `final_eval_test.py` — the ONLY script allowed to read the test split (eval15); run once per
  reported configuration after the plan's final gate; refuses a second read of the same label;
  writes `ralph/results/final_eval__test.json`. `--preflight` runs on validation images only.
- `analysis/` — scripts that turn `ralph/results/<run>.json` into `<run>__analysis.json`
  (seed means/SD, paired deltas). Each writes a `sources` block with input sha256s.
- `plots/` — scripts that read `ralph/results/*.json` (never raw CSVs) and write
  `writing/figures/*.pdf`.

Conventions: one training job per GPU with explicit `CUDA_VISIBLE_DEVICES`; jobs never
resume or overwrite (`mkdir(exist_ok=False)`); `status.json` state is `running | complete |
failed` with a `phase` field; every `config.json` carries `"test15": "NEVER READ"`.
Run `export_results.py` only with `--run`: a bare call would re-export the discarded
pre-reset studies still present under `outputs/`.
