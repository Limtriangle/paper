# HVI-PLAN.md — project spec (the source of truth)

> Status: **GATE 0 PASSED 2026-09-24 04:51 UTC** — the author confirmed the topic in `ralph/INBOX.md`
> (line 29). Scope: a bachelor's thesis paper related to HVI-CIDNet (Yan et al., CVPR 2025), ICML format,
> English, 4-page body + appendix. §0–§8 below are binding. Phase 0 history: `ralph/phase0_candidates.md`
> (v10), the author's red-teams `ralph/related/redteam/R1–R6`, and `ralph/DECISIONS.md`.

## 0. The one question

**Under a frozen training protocol with five matched seeds, which steps of HVI-CIDNet's representation design
(learned k → fixed k → no intensity collapse → linear chroma → luma intensity) and of its heuristic dual-space loss
(full → no VGG on HVI → k detached → RGB-only → a principled reweighting) change LOL-v1 enhancement quality by more
than the seed spread — by how much, and where in the intensity range?**

Advisor's framing (INBOX line 29): *confirm under which conditions and by how much HVI-CIDNet's effect reproduces* —
not a refutation, not a new method. The existing loss is heuristically designed; that is the second axis.

TL;DR (one sentence, guidelines §3 step 1): *Two nested single-factor ladders inside one CIDNet — five representation
arms and five loss arms, five matched seeds each, final-checkpoint read-out, pre-registered paired tests — measure
which parts of HVI-CIDNet's design reproduce, by how much, and whether the gain sits in the dark pixels its
mechanism predicts.*

## Phase 0 — how the topic gets chosen

Owner: `master`, with the author. Output: §0, §4, §5, §6, §8 of this file, written
**before** any experiment runs (the upstream method: generate the plan first, with a paper
story for every outcome, then run).

1. **Ground truth first.** `experiment` reads the upstream code and reports, as a file
   (`ralph/results/phase0_codebase.json`), what HVI-CIDNet actually does: the HVI transform,
   the two-branch architecture, the loss terms and weights, the training protocol in the
   repo's configs, the datasets its README uses, the released checkpoints, and what one
   training run costs on one RTX 2080 Ti (measured with a 1-epoch smoke run). `writing`
   reads the HVI-CIDNet paper and its closest related work and writes
   `ralph/phase0_related.md`: what the paper claims, what it ablates, what it leaves open.
2. **Candidate questions.** `master` writes 4–6 candidates in `ralph/phase0_candidates.md`.
   Each candidate has: the one-sentence question; why it is open (cite the gap from step 1);
   the claim we would make if it works; the claim we would make if it fails (a negative
   result must still be a thesis); the minimal experiment that decides it; its GPU cost in
   2080 Ti-hours against the ~4-GPU budget; and the risk that the answer is trivial.
   Candidate families worth considering (not a list to copy): color-space design
   (what the HVI transform buys over HSV/LAB/YCbCr under an identical network), the
   dual-space objective (which terms matter, with seed spread), robustness (noise, JPEG,
   real-world unpaired data, other datasets), efficiency (width/depth/latency trade-off on
   consumer GPUs), failure modes of the polar chroma mapping near black, or a targeted
   modification with a pre-registered success criterion.
3. **Recommendation.** `master` ranks them by (decidability with our compute) × (size of the
   open gap) × (survives a negative result), writes the ranking and the recommended pick
   into `ralph/INBOX.md` under `## Open questions`, and logs it in DECISIONS.md.
4. **Gate 0 — the author's call.** The author edits INBOX.md: `[human] topic confirmed: <#>`
   (or names a different one). Master then fills §0–§8 below, `writing` writes the full
   4-page draft with `\ph{}` values, `experiment` writes the study scripts. Only then does
   Gate A open.

While Phase 0 is open, `experiment` may only do **instrument work**: make the upstream repo
train and evaluate end to end (1-epoch smoke run, one GPU), fix the run-directory convention
so `tooling/export_results.py` ingests it, and measure cost. `writing` keeps the skeleton
compiling and prepares the related-work appendix and the verified bibliography.

## 1. Rules of claim (from writing-guidelines §2 and the integrity floor)

- Assertive in framing, never in facts. No SOTA, no "first", no "significant" without a
  number and a spread.
- Every number in the paper is a `\phm{}` bound to a JSON key, or it is deleted.
- A difference smaller than the seed-to-seed sample SD is reported as *no measurable
  difference*, with the spread. Never by sign. Three seeds before any mean is cited.
- Checkpoint selection by validation only. The test split is read once, by one script, at
  the end, and the table that reports it says so.

## 2. Run-directory convention (what `export_results.py` expects)

```
/home/work/research/outputs/<study>/<run>/manifest.json        protocol + script sha256 + upstream commit + split sha256
/home/work/research/outputs/<study>/<run>/<job>/config.json     variant, seed, width, weights, gpu, torch, "test": "NEVER READ"
/home/work/research/outputs/<study>/<run>/<job>/status.json     {"state": "running"|"complete"|"failed"}
/home/work/research/outputs/<study>/<run>/<job>/metrics.csv     per-epoch: epoch, loss, val_psnr, ...
/home/work/research/outputs/<study>/<run>/<job>/validation_summary.csv   rows checkpoint=best|last, metric columns
```
Jobs never overwrite or resume in place (`mkdir(exist_ok=False)`). A protocol change is a
new script hash and a new run name.

## 3. Frozen protocol

Inherited from the upstream code (not the paper text: the code trains 1000 epochs at 256² crops; the paper says
1500 / 400²), measured in `ralph/results/phase0_codebase.json`, pinned by script sha256 in every run manifest.

| Item | Value | Source / note |
|---|---|---|
| Data | LOL-v1 our485 → **445 train / 40 val** (scene-disjoint split `scene_v1`, sha256 b0dde627…, DINOv2 + pHash clusters; val clusters contain no eval15 image) | `auto-research/split_scene_v1.json`; the 24 train images sharing a scene with eval15 **stay** (default, INBOX line 11) — stated caveat: 14/15 eval15 images have a train near-duplicate |
| Test | eval15, read **once per arm** at the end by `final_eval_test.py` (final checkpoint); a post-hoc `--oracle` pass over saved checkpoints, labelled `oracle`, never used for selection | integrity floor rule 4 |
| Schedule | 1000 epochs, batch 8, crop 256, random H/V flips, Adam lr 1e-4, 3-epoch warmup (epoch 1 at lr 0, as upstream), cosine to 1e-7; gradient clipping as upstream (a no-op, kept identical) | train.py, options.py |
| Precision / mode | FP32, no AMP, TF32 off; default (non-deterministic) CUDA mode; same-seed run-to-run floor 0.042 dB is reported | DECISIONS 2026-09-23 18:40 / phase0_codebase reproducibility |
| Validation | every 5 epochs on the 40 val pairs, ungated; checkpoints saved every 10 epochs | needed for val-selected secondary and the oracle |
| Seeds | **5 matched seeds {42, 43, 44, 45, 46}** per arm; seed fixes data order, crops, flips, init of shape-identical layers | R2 §3 |
| Read-outs | **primary = final epoch-1000 checkpoint**; secondary = best-val-PSNR checkpoint; oracle = test PSNR of every 10th checkpoint, post hoc | R2 §4b |
| Metrics | **primary = GT-mean PSNR with ONE scalar luminance gain** (never per-channel); secondary = raw PSNR, SSIM (one fixed implementation, stated), LPIPS (alex), ΔE00 (raw and after scalar gain), log-exposure error; decomposition raw MSE ≈ gain error + GT-mean residual | R2 §4c; `auto-research/c1_metrics.py` |
| Mandatory analysis | per-GT-intensity-decile RGB MSE, ΔE00, chroma-weighted circular hue error per arm and seed with seed-level CIs; darkness stress test (× 0.5, × 0.25 + frozen Poisson–Gaussian noise) | `analysis_c1.py` rules 1–7, self-tested |
| Test-time knobs | gated off, α_s = α_i = 1, γ = 1 in every arm | R2 §4e |
| Loss-side transform | k0 = **1.1255** (released converged value), constant and detached, in every arm whose HVI-space loss uses a detached k | DECISIONS 2026-09-24 02:15 default |
| Cross-dataset (secondary) | LOL-v2-Real test, deduplicated against LOL-v1 train by hash/embedding, all final checkpoints, no retraining; download + checksum logged | R6 §7 |
| Hardware | 1 job per RTX 2080 Ti (peak 9.8 GiB), ≈ 7.7 GPU-h per run with val every 5 epochs | phase0_codebase cost |

Runs already on disk may be reused as seed 42 of an arm **only if** their manifest script hash equals the frozen
one: `outputs/baseline/rankcheck_v2/{A0,A2}_seed42` (frozen loss L2, from scratch).

## 4. Studies and claims

Common to all arms: same two-branch CIDNet, identical parameter count (1,975,569; asserted per arm), residual in the
working space, frozen protocol §3. Claims are written first; the ladders exist to support or refute them.
Vocabulary (author's rule): a step **"contributes"** when the paired-by-seed test (rule S-3 below) rejects; a step is
**"removable"** when TOST ± 0.3 dB rejects; otherwise **"inconclusive"**. The words "better loss", "SOTA", "significant"
without a number, and "less than the seed spread" as a claim are banned.

### S1 — Loss ladder on the A0 representation (HVI, learned k), 5 arms × 5 seeds = 25 runs
| Arm | Loss | Step isolated (vs neighbour) |
|---|---|---|
| L0 | FULL upstream: L_rgb (L1 + 0.5 SSIM + 50 edge + 0.01 VGG) + 1.0·L_hvi (same four terms), k coupled through HVIT(gt) | reference = the released recipe; **Gate A arm** |
| L1 | L0 − VGG on HVI | the perceptual term on non-RGB tensors (range_norm oddity) |
| L2 | L1 with k **detached** in the loss transform (k0 = 1.1255) | loss-side k coupling (the chroma-collapse shortcut) — **L2 is the frozen loss of S2** |
| L3 | RGB-only (λ_hvi = 0) | the whole HVI-space supervision (replicates the paper's ablation, seeded) |
| L4 | L2 with the HVI chroma terms weighted by C_k(I_gt) (dark pixels down-weighted in proportion to their collapse) | one principled alternative (author's default; uncertainty weighting rejected by R6 as magnitude normalisation) |

Contrasts (nested, Holm across 4): L0−L1, L1−L2, L2−L3, L2−L4. Claims: **C-S1a** "VGG on HVI contributes / is
removable"; **C-S1b** "coupling k into the loss changes k's trajectory (logged every epoch) and quality by Δ";
**C-S1c** "HVI-space supervision contributes Δ over RGB-only"; **C-S1d** "the C_k-weighted chroma loss is
equivalent / contributes". Gradient-share attribution per term, stratified by pixel luminance, is logged in L0 (R6 C3).

### S2 — Representation ladder under the frozen loss L2, 4 arms × 5 seeds = 20 runs (+ A0-L2 shared with S1)
| Arm | Representation (I-branch / HV-branch) | Step isolated |
|---|---|---|
| A0 | HVI, learned k | reference (= S1's L2 arm) |
| A1 | HVI, k frozen at the median converged k of the five A0-L2 runs | learned vs fixed k (**dropped only if A0's k moves < 0.05**; released k moved 0.2 → 1.13, so expected to stay) |
| A2 | HVI with k = 0 (Cartesian HSV: I = max, S·cos h, S·sin h) | **the C_k intensity collapse — primary mechanism contrast A0−A2** |
| A3 | I = max / linear opponent chroma (Cb, Cr) | saturation-polar vs linear chroma |
| A4 | YCbCr (I = Y / Cb, Cr) | intensity definition max vs luma (expect mainly an exposure effect) |

Contrasts (Holm across 4): A0−A1, A0−A2, A2−A3, A3−A4. Claims: **C-S2a** "learned k contributes / is removable";
**C-S2b** "C_k contributes Δ and its gain is located in the bottom three intensity deciles and grows with darkness"
(mechanism rule S-5); **C-S2c** "polar chroma vs linear chroma: Δ"; **C-S2d** "max vs luma intensity: Δ, mostly
exposure (decomposition)". Adapters and preflights: `auto-research/c1_arms.py`, `phase0_arms_preflight.json`.

### S3 — Seed variance and selection bias (zero extra runs)
σ_seed per arm from the five seeds (val and test); selection bias = (oracle − final) and (oracle − val-selected) per
arm as mean ± SD, and max-over-seeds of the oracle as the "paper-style" number. **C-S3** "the published LOL-v1
spread (23.5–24.0 raw third-party vs 28.2 GT-mean paper) decomposes into GT-mean rescaling (x dB), test-set
selection (y dB) and seed noise (z dB)". Never used to rank arms.

### S4 — Bonus chapter, zero training (only after S1/S2 are launched)
T3 oracle decomposition of the brightness-shift failure (R4 revised design): per-image GT-oracle over {pre-gain only}
vs {all knobs k, α_s, α_i, γ} on val GT-blends α ∈ {0.1, 0.2, 0.35, 0.5} and gains {× 0.5, × 2, × 4}; baselines =
identity and closed-form mean-match pre-gain; scene as the replication unit. **C-S4** "X % of the brightness-shift loss
is one scalar of exposure miscalibration; HVI's knobs add ≤ Y dB / ≤ Z ΔE". Not a method.

### Pre-registered decision rules (R2, adopted verbatim in substance)
S-1 primary metric/read-out: GT-mean PSNR (scalar gain), final checkpoint, per run. S-2 contrasts as listed, paired by
seed (n = 5), Holm within each ladder. S-3 **difference** only if (a) paired 95 % t-CI (df = 4) excludes 0 after Holm,
(b) |mean Δ| ≥ 0.3 dB and > 2·SD(Δ_s), (c) sign agrees in ≥ 4/5 seeds, (d) the mixed model PSNR ~ arm + (1|image) +
(1|seed) agrees in direction; per-image Wilcoxon descriptive only. S-4 **equivalence** only if TOST ± 0.3 dB rejects at
α = 0.05; else "inconclusive". S-5 mechanism (A0 vs A2): bottom-3-decile hue/ΔE00 difference CI excludes 0 while the
top-5-decile difference includes 0 or is ≥ 3× smaller; darkness stress test monotone. S-6 pipeline gate = Gate A.
S-7 selection bias reported as in S3. S-8 frozen before launch with hashes: loss weights, k0, split, knobs, metric and
analysis code. S-9 pivots in §8. Brightness artefact (R6 K4): if > 70 % of a raw-PSNR gain disappears under GT-mean,
it is called brightness bias, not improvement.

### Budget
45 runs × ≈ 7.7 GPU-h ≈ 350 GPU-h ≈ 3.6 days on 4 GPUs (Gate A's 5 runs first; the running seed-42 pair counts if
its hash matches). Cut order if time runs out: A4 → L4 → A3/A4 down to 3 seeds → A1.

## 5. Gates

| Gate | Needs | PASS default | FAIL default |
|---|---|---|---|
| **0 — topic** | PASSED 2026-09-24 (INBOX line 29) | — | — |
| **A — instrument + reproduction** | A0 under L0, 5 seeds, from scratch; `final_eval_test.py` final read of each (this is that arm's one test read); export + `verify-phm.py` green; protocol hash pinned | mean raw eval15 PSNR ∈ [23.3, 24.3] dB **and** σ_seed ≤ 0.5 dB → launch S1/S2 in waves of 4. If 0.4 < σ_seed ≤ 0.5: add seeds 47–49 to A0, A2, A3 (R2) | raw PSNR outside the window → K0: stop, debug once (one cycle, no new arms); if still outside, S1/S2 run anyway under the frozen protocol and the paper's first result is the measured reproduction gap with its causes (GT-mean, selection, seed) — the storyline's "problem" move (P-A). σ_seed > 0.6 dB even with 8 seeds → P-σ (§8) |
| **B — loss ladder** | S1's 25 runs exported (or the cut set), analysis JSON from the frozen script | verdict per contrast in the vocabulary of §4; if L2 differs from L0 by a "difference", the paper states the cost of the frozen loss used in S2 (P-L) | a cell that fails/OOMs twice → drop it, note in RESULTS.md, report the contrast with n = 4 |
| **C — representation ladder** | S2's 20 runs exported; A1 kept/dropped by the k-movement rule | verdict per contrast; mechanism rule S-5 evaluated on saved outputs | an arm that does not train (e.g. A2 instability) is reported as a result with its curve, never silently dropped (P-A2) |
| **D — final** | final-eval JSON for every arm; S3 numbers; `verify-phm.py` 0 unbacked; `writing-audit.sh --final` PASS; generated tables match JSON | submit-ready | delete unbacked claims; submit-ready |

## 6. Storyline (five moves; the intro follows the style guide's 7-move arc; lead figure = a results figure: the two ladders as paired-by-seed Δ plots with CIs, plus the per-decile mechanism panel)

1. **Background.** HVI-CIDNet enhances low-light images in a polar colour space whose intensity-dependent collapse
   C_k is claimed to remove colour noise near black; it reports state-of-the-art numbers on LOL-v1 and a colour-space
   ablation. *Limitation:* those numbers are single runs, selected on the test split, and the dual-space loss is
   heuristic (four terms, weights 1 / 0.5 / 50 / 0.01, duplicated in two spaces).
2. **Problem / motivation.** The published LOL-v1 numbers span 23.5–28.2 dB depending on GT-mean rescaling and
   selection; third-party reproductions disagree; nobody reports seeds; the paper's own colour-space ablations flip
   sign between datasets (R1). Under which conditions, and by how much, does the effect reproduce?
3. **Approach (the "killer" idea).** Two nested single-factor ladders inside one frozen CIDNet — representation and
   loss — with five matched seeds, a scene-disjoint validation split, final-checkpoint read-out, one test read per arm,
   and decision rules fixed before launch; the mechanism claim is tested where it predicts (dark deciles).
4. **Experiments (claim first).** S1: which loss terms contribute (\ph values from §7). S2: which representation steps
   contribute, and whether the C_k gain is in the dark deciles. S3: how the published spread decomposes into
   rescaling, selection and seed noise. S4 (appendix): the brightness-shift failure is mostly one scalar.
5. **Conclusion.** One sentence per ladder in the vocabulary "contributes / removable / inconclusive", with the
   measured seed SD and MDE stated, and the practical recipe that follows (what to keep, what to drop).

## 7. Provisional values (for `\ph{}` only — every one is replaced by a `\phm{}` bound to a JSON key or deleted)

Written as if final (guidelines §1). Sources: README/paper numbers and R2's predictions; none is measured by us.

| Quantity | Provisional | Basis |
|---|---|---|
| A0-L0 raw PSNR / GT-mean PSNR (eval15, final ckpt, mean of 5) | 23.8 / 27.7 dB | README w_perc |
| σ_seed (val GT-mean PSNR) | 0.3 dB | R2 assumption; run-to-run floor 0.04 |
| Achieved paired MDE | 0.5 dB | 1.66·σ_Δ |
| L0−L1 (VGG on HVI) | +0.1 dB (removable) | README wo_perc GT-mean 28.14 vs 27.71 suggests ≤ 0 |
| L1−L2 (k coupling) | 0.0 dB (inconclusive); k drifts 0.2 → 1.1 | released k |
| L2−L3 (HVI supervision) | +0.6 dB (contributes) | paper 24.11 vs 23.32 on v2-real |
| L2−L4 (C_k-weighted chroma) | 0.0 dB (equivalent) | no prior |
| A0−A1 (learned vs fixed k) | 0.1 dB (removable) | R2 |
| A0−A2 (C_k) | +0.4 dB, concentrated in deciles 1–3 | R2: −0.2 to −0.6 |
| A2−A3 (polar vs linear chroma) | 0.1 dB (inconclusive) | R2: ± 0.3 |
| A3−A4 (max vs luma) | 0.2 dB raw, 0.0 GT-mean | R2 |
| Selection bias (oracle − final) | 0.3 dB | R2 |
| GT-mean rescaling gain | 3.9 dB | README 27.71 − 23.81 |
| Brightness-shift loss explained by one scalar gain (S4) | 80 % | R4 |

## 8. Pivots (pre-committed; master logs which one fired)

Every contrast has three pre-written outcomes — **difference**, **equivalent**, **inconclusive** — and each is a
sentence in the paper, never a reason to rerun. Specific pivots:

- **P-A (Gate A window fails after one debug cycle).** The thesis leads with the measured reproduction gap and its
  decomposition (S3); S1/S2 proceed unchanged under the frozen protocol; every absolute number is labelled "under our
  protocol". Log: `GATE A: FAIL → P-A`.
- **P-σ (σ_seed > 0.6 dB even with 8 seeds).** No superiority claim survives; the thesis becomes the study with "no
  detectable difference; MDE = x dB" for every contrast, plus S3 and the mechanism analysis, plus the k sweep from the
  A0 k-trajectories (C3 lite, zero runs). Log: `PIVOT-σ`.
- **P-A1 (k moves < 0.05 in A0-L2).** A1 := A0; 5 runs saved and given to seeds 47–49 of A2/A3.
- **P-A2 (A2 does not train / diverges at k = 0).** Report the curves as the result "no intensity collapse is not
  trainable under this protocol"; A2−A3 contrast becomes A0−A3 (stated).
- **P-L (L2 differs from L0 by a "difference" > 0.5 dB).** S2 still runs under L2 (frozen before launch); the paper
  adds one paragraph quantifying what the frozen loss costs and notes the S2 conclusions are conditional on it.
- **P-mech (A0−A2 is a difference but the decile rule S-5 fails).** Claim "C_k contributes globally; its gain is not
  localised where the mechanism predicts"; the dose–response curve is reported as-is.
- **P-budget (time runs out).** Cut order A4 → L4 → A3/A4 to 3 seeds → A1; the paper reports the cut arms as
  "not run" with the reason; no partial arm is reported with fewer than 3 seeds.
- **P-S4 (T3 oracle shows the knobs add > 1 dB beyond gain-only).** Report it as an observation in the appendix with
  a caution that the oracle uses GT; no method claim.
- **P-neg (every contrast equivalent or inconclusive).** That *is* the thesis: "HVI-CIDNet's design steps are within
  ± 0.3 dB of each other at n = 5 under a frozen protocol; the published spread is rescaling + selection + seed noise".
