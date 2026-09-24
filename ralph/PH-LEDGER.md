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
| 23.8 / 27.7 | exp, intro | A0-L0 raw / GT-mean PSNR, mean of 5 | `gateA__a0_l0_v1.json` arm_summary.L0.psnr(.mean), psnr_gtmean(.mean) |
| 23.3, 24.3 | exp | Gate A window | HVI-PLAN §5 (protocol constant, not a measurement; becomes plain text) |
| 0.3 | abs, intro, exp, concl | σ_seed (val and test GT-mean PSNR) | `gateA__a0_l0_v1.json` arm_summary.L0.psnr_gtmean.sd; later per-arm |
| 0.5 | abs, intro, exp, concl | achieved paired MDE | analysis decision_rules.mde (to be added by experiment) or derived 1.66·SD(Δ) |
| 0.1 removable | exp, tables | L0−L1 | `s1__loss_ladder_v1.json` analysis.analysis_s1.decision.contrasts.L0-L1.{mean,sd,ci_holm,verdict} |
| 0.0 inconclusive; k 0.2→1.1 | exp, tables | L1−L2; k trajectory | contrasts.L1-L2.*; k trajectory key (experiment logs k per epoch; key TBD) |
| 0.6 contributes | abs, intro, exp, concl, tables | L2−L3 | contrasts.L2-L3.* |
| 0.0 removable | exp, tables | L2−L4 | contrasts.L2-L4.* |
| 0.1 removable | tables | A0−A1 | `s2__rep_ladder_v1.json` analysis.analysis_s2.decision.contrasts.A0-A1.* |
| 0.4 contributes, deciles 1–3 | abs, intro, exp, concl, tables | A0−A2 + mechanism rule | contrasts.A0-A2.*; mechanism_A0_vs_A2.{hue_err,delta_e00}.rule5, stress.monotone |
| 0.1 inconclusive | exp, tables | A2−A3 | contrasts.A2-A3.* |
| 0.2 raw / 0.0 GT-mean, removable | exp, tables | A3−A4 | contrasts.A3-A4.* (GT-mean); raw contrast key TBD |
| 27.7, 27.6, 27.6, 27.0, 27.6 | app_s1_arms | per-arm GT-mean PSNR (derived: 27.7 − Δ) | arm_summary.<arm>.psnr_gtmean.mean |
| 23.8 … (derived −3.9) | app_s1_arms, app_s2_arms | per-arm raw PSNR | arm_summary.<arm>.psnr.mean |
| 27.6, 27.5, 27.2, 27.1, 27.1 | app_s2_arms | per-arm GT-mean PSNR (derived) | arm_summary.<arm>.psnr_gtmean.mean |
| 0.3 (SD cells) | app tables | per-arm seed SD | arm_summary.<arm>.<metric>.sd |
| 0.3 | exp, app_s3 | oracle − final | `s3__selection_bias_v1.json` analysis.analysis_s3.decision.<arm>.oracle_minus_final_mean |
| 0.6 | exp | paper-style max − mean final | derived from paper_style_max_over_seeds − arm mean |
| 28.0, 27.9, 27.5, 27.4, 27.4 | app_s3 | paper-style max per arm (derived) | <arm>.paper_style_max_over_seeds |
| 3.9 | abs, intro, exp, app | GT-mean rescaling gain | arm_summary.L0.psnr_gtmean.mean − psnr.mean |
| 0.04 | app | same-seed run-to-run floor | `baseline__determinism_{a,b}.json` (exists; bind at next pass) |
| (no number) | exp, transfer paragraph | cross-dataset sign agreement and uniform level drop; a claim without a §7 value: quantify from the LOL-v2-Real JSON (sign counts per contrast, mean drop) or delete the paragraph at the milestone | cross-dataset export (R6 §7), keys TBD |
| 80 %, 0.3 dB | app S4 | brightness-shift loss explained by pre-gain; knob gain | S4 analysis JSON (not yet defined) |

Rule: at the first milestone every row either becomes a `\phm{}` row below or its sentence is
deleted. Literature rows (first three) become citations with the number attributed, or go.

## `\phm{}` — measured (from `verify-phm.py --ledger`)

*(none yet)*
