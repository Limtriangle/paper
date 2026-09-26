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
| 23.3, 24.3 | exp | Gate A window | HVI-PLAN §5 (protocol constant, not a measurement; becomes plain text) |
| 0.1 removable | tables | A0−A1 | `s2__rep_ladder_v1.json` analysis.analysis_s2.decision.contrasts.A0-A1.* |
| 0.4 contributes, deciles 1–3 | abs, intro, exp, concl, tables | A0−A2 + mechanism rule | contrasts.A0-A2.*; mechanism_A0_vs_A2.{hue_err,delta_e00}.rule5, stress.monotone |
| 0.1 inconclusive | exp, tables | A2−A3 | contrasts.A2-A3.* |
| 0.2 raw / 0.0 GT-mean, removable | exp, tables | A3−A4 | contrasts.A3-A4.* (GT-mean); raw contrast key TBD |
| (none left) | app_s1_arms | per-arm GT-mean PSNR, re-derived 2026-09-25 from measured L2 26.73 minus plan §7 Δ (was 27.0/27.6 from the §7 27.7 base) | arm_summary.<arm>.psnr_gtmean.mean |
| 23.8 … (derived −3.9; A3 23.2, A4 23.0 so that A3−A4 raw = 0.2 per §7) | app_s1_arms, app_s2_arms | per-arm raw PSNR | arm_summary.<arm>.psnr.mean |
| 26.7, 26.6, 26.3, 26.2, 26.2 (raw 23.3 … 22.6) | app_s2_arms | per-arm GT-mean / raw PSNR, re-derived from measured L2 base minus §7 Δ | arm_summary.<arm>.* |
| 0.3 (SD cells) | app tables | per-arm seed SD | arm_summary.<arm>.<metric>.sd |
| 0.3 | app_s3 (arms A0-A4 only; L0 row now measured) | oracle − final per ladder arm | `s3__selection_bias_v1.json` analysis.analysis_s3.decision.<arm>.oracle_minus_final_mean |
| 26.8, 26.4, 26.3, 26.3 | app_s3 (A0-A4, re-derived from measured L0 oracle max 26.96) | paper-style max per arm (derived) | <arm>.paper_style_max_over_seeds |
| 3.3 | abs, intro, exp, app | GT-mean rescaling gain (26.63 − 23.34 from the summary keys; the difference itself is not a key) | a derived key gtmean_minus_raw.mean, or state both means and drop the difference |
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
| `5` | experiments.tex | `gateA__a0_l0_v1.json: n_jobs.complete` and `gateA__summary_n5_v1.json: summary.gateA_L0.final.raw_psnr.n` | 5 |
| `23.25`, `0.47` | experiments.tex, introduction.tex | `gateA__summary_n5_v1.json: summary.gateA_L0.final.raw_psnr.{mean,sd}` (n=5) | 23.254, 0.470 |
| `26.65`, `0.16` | experiments.tex; `0.16` also abstract, introduction, conclusion (headline seed SD, GT-mean = primary metric) | `summary.gateA_L0.final.gtmean_psnr.{mean,sd}` (n=5) | 26.645, 0.160 |
| `27.73` | experiments.tex | `summary.gateA_L0.gated.gtmean_psnr.mean` | 27.735 |
| `0.85` | experiments.tex | `summary.gateA_L0.k_final.median` (n=5; the S1 file's L0 median now pools n=7 incl. seeds 47-48 and is not used, per the n=5 ruling) | 0.850 |
| `0.2`, `1.13` | experiments.tex | `analysis.analysis_k.decision.constants.{k_init,k_released}` | 0.2, 1.1255 |
| `0.29` | experiments.tex (L2 = A0 under the frozen loss; k moves 0.09 > 0.05, so A1 stays) | `analysis.analysis_k.decision.summary.L2.k_final.median` (n=5) | 0.294 |
| `3.39` | abstract, introduction, experiments, appendix | `summary.gateA_L0.decomposition.gtmean_minus_raw.mean` (n=5) | 3.392 |
| `1.09` | abstract, introduction, experiments | `decomposition.gated_minus_ungated_gtmean.mean` (n=5) | 1.088 |
| `0.07`, `removable` (L0−L1); `-0.16`, `5`, `removable` (L1−L2) | experiments.tex | `s1__loss_ladder_v1.json: analysis.analysis_s1.decision.contrasts.{L0-L1,L1-L2}.{mean,verdict,sign_agreement}` | 0.067, −0.155, 5 |
| s1_contrasts rows L0−L1, L1−L2 (10 cells); app_s1_arms rows L0 (pooled n=8, gateA__summary_v1) and L1, L2 (arm_summary, n=5) | tables | generated by gen-table | see verify-phm --ledger |
| `28.2`, `24.0`, `23.6`, `23.50`, `0.2`, `0.4` | abstract, introduction, experiments | `literature_v1.json: entries.{hvi_paper_lolv1,pal_cidnet_lolv1,issue66_retrain_lolv1,fusionnet_cidnet_lolv1}.value.psnr`, `shafi2026_seed_sd.value.psnr_sd_{low,high}` | 28.201, 23.97, 23.5881, 23.5, 0.2, 0.4 |
| app_s3 rows L0 (42-46), L1, L2 | app_s3.tex | `s3__selection_bias_v1.json: analysis.analysis_s3.decision.<arm>.*` (partial) | 0.06/26.96, 0.11/26.78, 0.07/26.91 |
| `0.58`, `5`, `contributes` (L2−L3) | abstract, introduction, experiments, conclusion | `s1__loss_ladder_v1.json: analysis.analysis_s1.decision.contrasts.L2-L3.{mean,sign_agreement,verdict}` | 0.577, 5 |
| `0.15`, `inconclusive` (L2−L4) | experiments.tex | `s1__loss_ladder_v1.json: contrasts.L2-L4.{mean,verdict}` (final, Gate B) | 0.149 |
| `0.34` | abstract, intro, method, results x2, conclusion (achieved MDE; loss ladder family max, master ruling) | `s1__loss_ladder_v1.json: analysis.analysis_s1.derived.mde_db.family_max` | 0.339 |
| `0.02`, `0.004`, `0.09` | experiments.tex (TOST p beside removable/removable/inconclusive) | `analysis.analysis_s1.derived.tost_p.{L0-L1,L1-L2,L2-L4}` | 0.019, 0.0041, 0.086 |
| `0.25`, `0.90`, `0.17` (L2−L3 Holm CI, SD) | experiments.tex | `contrasts.L2-L3.{ci_holm.0,ci_holm.1,sd}` | 0.253, 0.901, 0.168 |
| `0.58` (mixed model), `0.005`, `0.58` (image-only check) | experiments.tex, appendix.tex | `contrasts.L2-L3.mixed_model.{coef,vc.seed}`, `derived.mixed_supplementary.L2-L3.mixedlm_image_only.coef` | 0.577, 0.0049, 0.577 |
| `0.2` (k init), `0.5`, `50`, `0.01` (loss weights) | method.tex, introduction.tex | `phase0_codebase.json: measured.density_k_init`, `instrument.protocol.weights.{SSIM,edge,perceptual}` | 0.2, 0.5, 50.0, 0.01 |
| `100`, `91`, `0`, `9`, `3` | appendix.tex (LOL-v2-Real dedup; transfer claim dropped) | `lolv2real_v1.json: counts.{n_test,n_dup_train_any,n_dup_eval15,n_kept,n_scenes_kept}` | 100, 91, 0, 9, 3 |
| `30.15`, `29.77`, `29.98`, `28.74`, `30.50`; `5`, `4` | appendix.tex (LOL-v2-Real descriptive, 9 images / 3 scenes, no verdict) | `lolv2real_v1.json: summary.<arm>.gtmean_psnr.{mean,n}` | L1 n=4 (seed-44 read failed twice) |
| `-0.71` | appendix.tex | `decomposition.valsel_minus_final_gtmean.mean` (n=5; seed 46's val-selected checkpoint is 2 dB low) | -0.713 |
| `0.06` | abstract, introduction, experiments (headline selection term, GT-mean) | `decomposition.oracle_minus_final_gtmean.mean` (n=4) | 0.064 |
| `0.41` | abstract, introduction, experiments (raw selection inflation) | `decomposition.oracle_minus_final.mean` (n=5) | 0.408 |
| `23.66` | experiments.tex | `summary.gateA_L0.oracle.max_over_ckpt_mean.raw_psnr.mean` (oracle raw read, inside the window) | 23.662 |
| `23.67` | experiments.tex | `summary.gateA_L0.gated.raw_psnr.mean` (gated raw read, inside the window) | 23.671 |
| `8`, `23.26`, `0.41`, `-0.04` | experiments.tex (pooled reference-arm sentence, master ruling 2026-09-25) | `gateA__summary_v1.json: summary.gateA_L0.final.raw_psnr.{n,mean,sd}`, `window.final_raw_mean_minus_lower` (n=8) | 8, 23.264, 0.406, -0.036 |
| `-0.05` | experiments.tex | `summary.gateA_L0.window.final_raw_mean_minus_lower` | -0.046 |
| `101` | introduction.tex | `summary.gateA_L0.oracle.per_seed.42.n_checkpoints` | 101 |
| `445` | method.tex, experiments.tex | `phase0_val_split_scene.json: n_train` | 445 |
| `27.71` | experiments.tex | `phase0_codebase.json: facts.evaluation_protocol_upstream.readme_lolv1_numbers.w_perc_gtmean.psnr` | 27.7146 |
| app_s3 L0 row (2 cells) | app_s3.tex | `decomposition.oracle_minus_final_gtmean.mean`, `oracle.max_over_seeds.gtmean_psnr` (per-row src override) | 0.06, 26.96 |
| `22.78`, `23.97` | experiments.tex | `final_eval__test.json: entries.gateA_L0_seed{42,44}.metrics.psnr` (min, max over completed seeds) | 22.7751, 23.9697 |
| `26.52`, `26.90` | experiments.tex | `entries.gateA_L0_seed{43,44}.metrics.psnr_gtmean` (min, max) | 26.5215, 26.9044 |
| `27.55`, `28.05` | experiments.tex | `entries.gateA_L0_seed{43,44}_gated.metrics.psnr_gtmean` (min, max) | 27.5513, 28.0453 |
| 20 table cells (seed 46 added) | app_gatea_seeds.tex | `entries.gateA_L0_seed{42..45}{,_gated,_valsel}.metrics.{psnr,psnr_gtmean}` | see `verify-phm.py --ledger` |
