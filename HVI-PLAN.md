# HVI-PLAN.md — project spec (the source of truth)

> Status: **DRAFT v0, 2026-09-24.** Written by the scaffold from the study scripts and result
> files that already exist under `/home/work/research`. Lines marked **[CONFIRM]** are the
> author's to confirm or change in `ralph/INBOX.md`; until then agents treat them as the
> pre-committed default. Everything else is derived from what the code actually does.

## 0. The one question

*Which components of the dual-space HVI-CIDNet training recipe measurably improve
low-light enhancement quality on LOL-v1, and which are indistinguishable from seed noise?*

TL;DR (one sentence, guidelines §3.1): Under one frozen protocol, we isolate the effect of
each HVI-space loss term, of model width, and of input prefiltering in HVI-CIDNet, and
report every effect against its seed spread.

**[CONFIRM]** This frames the thesis as a *controlled study*, not a new method. If the
thesis is instead meant to propose a modification (e.g. a prefilter or a DySample
upsampler as the contribution), say so in INBOX.md and the storyline in §6 flips to
"method + ablations".

## 1. Rules of claim (from writing-guidelines §2 and the integrity floor)

- Assertive in framing, never in facts. No SOTA, no "first", no "significant" without a
  number and a spread.
- Every number in the paper is a `\phm{}` bound to a JSON key, or it is deleted.
- A difference smaller than the seed-to-seed sample SD is reported as *no measurable
  difference*, with the spread. Never by sign.
- Checkpoint selection by validation PSNR only. `test15` is read once, by a dedicated
  script, at the very end, and the table that reports it says so.

## 2. What already exists (inventory, 2026-09-24)

| Study | Run | Cells complete | Protocol | Notes |
|---|---|---|---|---|
| width_study | width500_v1 | W18/24/30/36 × seed 42 | `hvi_width_trial.py` (protocol root, sha `32337aa3…`) | 500 epochs, full objective |
| width_study | width_smoke_v1 | 4 × seed 42 | same, 1 epoch | smoke only, not citable |
| loss_ablation | repro_check_v1 | FULL_W18_seed42 (1 epoch) | `hvi_loss_ablation.py` | verifies FULL == width objective bitwise |
| loss_ablation | throughput_v1 | FULL_W36_seed1001 | same | timing only |
| loss_study | dysample50_v1 / dysample_smoke_v1 | A2/A4/B0/B1 × seed 42 | `hvi_dysample_trial.py` | 50 epochs |
| loss_study | kdiag_v1 | baseline / i_ssim / rgb_perceptual | `hvi_k_diagnostic.py` | no validation_summary |
| prefilter_study | prefilter50_v1, prefilter500_v1 | B0/H3/I3/HI3 × seed 42 | `hvi_prefilter_trial.py` | 50 and 500 epochs |
| prefilter_study | ifilter_confirm50_v1 | B0/I3 × seeds 43, 44 | `hvi_ifilter_confirm.py` + `protocol.json` | pre-registered screen → **HOLD** |

Exported by `tooling/export_results.py` into `ralph/results/<study>__<run>.json`.

## 3. Frozen protocol (from the manifests; do not change without a new run name)

LOL-v1, 485 train / 15 eval, split sha `b8eb9baf…`; random 128×128 crops, batch 1; Adam,
lr 1e-4 fixed for 50 epochs then cosine to 1e-7 through epoch 500; FP32, TF32 off, no AMP;
one RTX 2080 Ti per job; loss weights L1 1.0, SSIM 0.5, edge 50, perceptual 0.01, HVI 1.0;
selection = highest validation full-image RGB PSNR; `test15` NEVER READ.

## 4. Studies and claims

Each claim is written first; the experiment exists to support or refute it.

### S1 — Loss-term ablation (leave-one-out)
Claim: the HVI-space perceptual term is the HVI-space component that matters; the other
HVI-space terms are within noise. **[CONFIRM the expected winner]**
Cells: FULL, NO_L1, NO_SSIM, NO_EDGE, NO_PERC, NO_PERC_HVI, RGB_ONLY, HVI_ONLY × W ∈ {18, 36}
× seeds {42, 43, 44}. Script: `hvi_loss_ablation.py` via `hvi_loss_queue.py`.
Cost: ~8 variants × 2 widths × 3 seeds = 48 jobs × 500 epochs. **[CONFIRM budget]** —
default: W18 all variants × 3 seeds first (24 jobs); W36 only FULL / RGB_ONLY / NO_PERC_HVI.
Output: `loss_ablation__<run>.json` + `__analysis.json` (per-variant seed mean/SD, paired delta vs FULL).

### S2 — Width
Claim: PSNR grows with width with diminishing returns; 30→36 is within noise.
Cells: W18/24/30/36 × seeds {42, 43, 44}. Seed 42 done. Script: `hvi_width_trial.py`.
Output: `width_study__width500_v1.json` + analysis (per-width mean/SD, params).

### S3 — Input prefilter
Claim (pre-registered, already tested): I3 improves LPIPS/SSIM at equal PSNR. Result so
far: seed 43 passes all criteria, seed 44 fails all → **HOLD**. Default: report as
non-replicating; no expansion. Optional: one more seed (45) at 500 epochs for B0/I3 only
**[CONFIRM]**.

### S4 — Final test evaluation (last)
One script, run once per configuration that appears in the paper's main table, reads
`test15`, writes `final_eval__test15.json`. Never before Gate C.

## 5. Gates (master calls them from files, not from chat)

| Gate | Needs | PASS default | FAIL default |
|---|---|---|---|
| **A — instrument** | export of all existing runs; hash check of every manifest vs `hvi_width_trial.py`; FULL_W18 repro equals width500 W18 within 1e-6 on validation PSNR | launch S1/S2 seeds 43–44 | fix the instrument; nothing else runs |
| **B — width & seeds** | S2 with 3 seeds; S1 W18 FULL/RGB_ONLY/NO_PERC_HVI with 3 seeds | storyline §6 as written | Pivot P1 or P2 |
| **C — ablation complete** | S1 W18 all variants × 3 seeds | freeze the method table; run S4 | report the completed subset; freeze |
| **D — final** | S4 done; `verify-phm.py` 0 unbacked; `writing-audit.sh --final` PASS | submit-ready | delete unbacked claims; submit-ready |

## 6. Storyline (writing agent's spine)

1. Background: learned enhancers dominate LOL-v1; HVI-CIDNet changes the color space of
   both computation and supervision.
2. Problem: the recipe bundles eight loss terms, a width, and a raw input; its paper does
   not isolate them, and single-seed ablations overstate small gaps.
3. Approach: one frozen, hash-pinned protocol; every comparison with seed spread; every
   number file-bound.
4. Results: (S1) which HVI-space term matters; (S2) width curve; (S3) prefilter does not
   replicate.
5. Conclusion: what to keep from the recipe, what is noise.

Intro follows the 7-move arc (style guide §12). Lead figure: PSNR/LPIPS vs width with
per-seed points (`writing/figures/fig1_width.pdf`). Figure 2: loss-ablation deltas vs FULL
with seed SD bars (`fig2_ablation.pdf`). Tables: width (`tab:width`), prefilter
(`tab:prefilter`), full ablation in appendix. Page budget: style guide §2.

## 7. Provisional values (for `\ph{}` only; replaced as JSON lands)

- Width 18→36: +0.6 dB PSNR, −0.03 LPIPS, ~4× params. 30→36: +0.1 dB.
- NO_PERC_HVI vs FULL at W18: −0.3 dB PSNR, +0.02 LPIPS. RGB_ONLY vs FULL: −0.4 dB.
- Seed SD at W18: 0.2 dB PSNR.
These are guesses. They are never confidence intervals. They die at the milestone audit.

## 8. Pivots (pre-committed; master logs which one fired)

- **P1 — no HVI-space term matters** (all within SD): the paper becomes "the HVI-space
  supervision is redundant given RGB supervision under this protocol"; headline is the
  RGB_ONLY vs FULL delta with its SD. Positive-framing: simpler recipe, same quality.
- **P2 — everything matters** (removing any term hurts beyond SD): the paper becomes "the
  dual-space objective is jointly necessary"; headline is the smallest single-term drop.
- **P3 — width is flat** (18≈36): headline flips to "a 4× smaller HVI-CIDNet matches the
  original"; the width table leads.
- **P4 — instrument fails at Gate A**: nothing is cited until fixed; the paper's appendix
  documents the failure and the fix.
- **P5 — GPU budget runs out before Gate C**: report the completed subset with its exact
  cell count; never fill a missing cell.

## 9. Open questions for the author (also mirrored in `ralph/INBOX.md`)

1. [CONFIRM] Controlled-study framing (§0) vs. proposing a modification.
2. [CONFIRM] GPU budget for S1 (48 full jobs ≈ several days on 4 GPUs at 500 epochs).
3. [CONFIRM] Whether S3 gets a third seed.
4. Author name / affiliation for the camera-ready build (anonymous now).
5. Thesis deadline date, so master can set the calendar for Gates B–D.
