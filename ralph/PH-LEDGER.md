# PH-LEDGER — every provisional value in the paper, and what it waits on

**Owner:** `writing`. Regenerate the measured half with `python3 tooling/verify-phm.py --ledger`.
List the invented half with `grep -rnoE '\\ph\{[^}]*\}' writing/section writing/tables`.

| Macro | Meaning | Rule at the milestone audit |
|---|---|---|
| `\ph{}` | **INVENTED.** No measurement exists. | Land the real number (→ `\phm{}` + spec entry) or **delete the sentence**. |
| `\phm{}` | **MEASURED.** `ralph/phm-spec.json` binds it to a JSON key. | Verified by key; **unwrap** at the end (`tooling/unwrap-phm.sh`). Never delete. |

## `\ph{}` — invented, waiting on

All values from HVI-PLAN.md §7 (Gate 0, 2026-09-24). "Derived" = arithmetic on §7 values.
Files: `abs` = abstract, `intro`, `exp` = experiments, `concl`, `app` = appendix, tables in
`writing/tables/spec.json` (rendered as `\ph{}` by gen-table while the key is absent).

| Value | Where | Meaning | Waits on (JSON key, source) |
|---|---|---|---|
| 23.5, 28.2 | abs, intro, exp | published LOL-v1 spread (README raw / paper GT-mean) | literature numbers; cite `phase0_related.md` §2.3 sources or delete at milestone |
| 24.0 | intro | third-party raw reproductions upper bound | literature (PAL, issue #66); cite or delete |
| 0.2, 0.4 | intro | seed SD reported for comparable restoration models | `shafi2026iphoneblur` numbers; cite or delete |
| 23.3, 24.3 | exp | Gate A window | HVI-PLAN §5 (protocol constant, not a measurement; becomes plain text) |
| 0.3 | abs, intro, concl | σ_seed (val and test GT-mean PSNR), plan §7 | aggregate sd key (see row above) |
| 27.71 | exp | README w_perc GT-mean number for the released checkpoint (literature) | cite `yan2025hvi` README or delete |
| 0.5 | abs, intro, exp, concl | achieved paired MDE | analysis decision_rules.mde (to be added by experiment) or derived 1.66·SD(Δ) |
| 0.1 removable | exp, tables | L0−L1 | `s1__loss_ladder_v1.json` analysis.analysis_s1.decision.contrasts.L0-L1.{mean,sd,ci_holm,verdict} |
| 0.0 inconclusive | exp, tables | L1−L2 | contrasts.L1-L2.* |
| 1.1 | exp (S2 paragraph) | k end value in the A0-L2 runs (plan §7; the L0 runs give median 0.85, now \phm) | S2 summary k_final.median for A0 under L2 |
| 0.6 contributes | abs, intro, exp, concl, tables | L2−L3 | contrasts.L2-L3.* |
| 0.0 removable | exp, tables | L2−L4 | contrasts.L2-L4.* |
| 0.1 removable | tables | A0−A1 | `s2__rep_ladder_v1.json` analysis.analysis_s2.decision.contrasts.A0-A1.* |
| 0.4 contributes, deciles 1–3 | abs, intro, exp, concl, tables | A0−A2 + mechanism rule | contrasts.A0-A2.*; mechanism_A0_vs_A2.{hue_err,delta_e00}.rule5, stress.monotone |
| 0.1 inconclusive | exp, tables | A2−A3 | contrasts.A2-A3.* |
| 0.2 raw / 0.0 GT-mean, removable | exp, tables | A3−A4 | contrasts.A3-A4.* (GT-mean); raw contrast key TBD |
| 27.7, 27.6, 27.6, 27.0, 27.6 | app_s1_arms | per-arm GT-mean PSNR (derived: 27.7 − Δ) | arm_summary.<arm>.psnr_gtmean.mean |
| 23.8 … (derived −3.9; A3 23.2, A4 23.0 so that A3−A4 raw = 0.2 per §7) | app_s1_arms, app_s2_arms | per-arm raw PSNR | arm_summary.<arm>.psnr.mean |
| 27.6, 27.5, 27.2, 27.1, 27.1 | app_s2_arms | per-arm GT-mean PSNR (derived) | arm_summary.<arm>.psnr_gtmean.mean |
| 0.3 (SD cells) | app tables | per-arm seed SD | arm_summary.<arm>.<metric>.sd |
| 0.3 | exp, app_s3 | oracle − final | `s3__selection_bias_v1.json` analysis.analysis_s3.decision.<arm>.oracle_minus_final_mean |
| 28.0, 27.9, 27.5, 27.4, 27.4 | app_s3 | paper-style max per arm (derived) | <arm>.paper_style_max_over_seeds |
| 3.3 | abs, intro, exp, app | GT-mean rescaling gain (26.63 − 23.34 from the summary keys; the difference itself is not a key) | a derived key gtmean_minus_raw.mean, or state both means and drop the difference |
| 4 of 5; 22.0 | exp, transfer paragraph | contrasts keeping sign on LOL-v2-Real (dedup); A0-L0 GT-mean PSNR there | §7 row (R6 §7 placeholder); cross-dataset export, keys TBD |
| 80 %, 0.3 dB | app S4 | brightness-shift loss explained by pre-gain; HVI knobs add ≤ 0.3 dB beyond gain-only (§7 rows) | S4 analysis JSON (not yet defined) |

Rule: at the first milestone every row either becomes a `\phm{}` row below or its sentence is
deleted. Literature rows (first three) become citations with the number attributed, or go.

## Removed at master's audit of f0cd1fc (2026-09-24)
- round-trip error "below 4e-7" (method): JSON says 6.43e-7 per arm; scientific notation cannot be bound by verify-phm, sentence deleted (the preflight file is named instead).
- paper-style max − mean final "0.6" (exp): not in §7; replaced by a pointer to the S3 table.
- "a dozen follow-ups" (intro): count removed.
- "six cross-attention blocks" (method): it is twelve (six per branch); plain text, no number macro.

## `\phm{}` — measured (from `verify-phm.py --ledger`)

| written | file | key | actual |
|---|---|---|---|
| `0.04` | appendix.tex | `phase0_codebase.json: reproducibility.epoch2_val_psnr_spread_db` | 0.0424 |
| `1975569` | method.tex | `phase0_arms_preflight.json: ladder_parameter_count` | 1975569 |
| `4` | experiments.tex | `gateA__a0_l0_v1.json: n_jobs.complete` and `gateA__summary_v1.json: summary.gateA_L0.final.raw_psnr.n` | 4 (becomes 5 when seed 46 lands; re-bind then) |
| `23.34`, `0.49` | experiments.tex, introduction.tex | `gateA__summary_v1.json: summary.gateA_L0.final.raw_psnr.{mean,sd}` | 23.344, 0.490 |
| `26.63`, `0.18` | experiments.tex | `summary.gateA_L0.final.gtmean_psnr.{mean,sd}` | 26.634, 0.183 |
| `27.73` | experiments.tex | `summary.gateA_L0.gated.gtmean_psnr.mean` | 27.735 |
| `0.85` | experiments.tex | `summary.gateA_L0.k_final.median` | 0.847 |
| `22.78`, `23.97` | experiments.tex | `final_eval__test.json: entries.gateA_L0_seed{42,44}.metrics.psnr` (min, max over completed seeds) | 22.7751, 23.9697 |
| `26.52`, `26.90` | experiments.tex | `entries.gateA_L0_seed{43,44}.metrics.psnr_gtmean` (min, max) | 26.5215, 26.9044 |
| `27.55`, `28.05` | experiments.tex | `entries.gateA_L0_seed{43,44}_gated.metrics.psnr_gtmean` (min, max) | 27.5513, 28.0453 |
| 16 table cells | app_gatea_seeds.tex | `entries.gateA_L0_seed{42..45}{,_gated,_valsel}.metrics.{psnr,psnr_gtmean}` | see `verify-phm.py --ledger` |
