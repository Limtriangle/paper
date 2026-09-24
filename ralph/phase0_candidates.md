# phase0_candidates.md — thesis candidates (master)

Status: **v6 = the author's requested "v5 method candidates"** (2026-09-24 03:10 UTC). Part I below is new: five
method candidates M1–M5 under the author's new Gate 0 criteria (INBOX line 18). Part II is the earlier C-series
(v5, survey-reconciled); **C1, the R2 nested ladder, is now the ablation chapter of whichever method wins**, and C3–C6
are kept for the record. Evidence keys are in `ralph/related/survey.bib` unless noted; file pointers use
D = related/D_hvi_followups.md, E = related/E_evaluation.md, CJ = results/phase0_codebase.json, R2 = redteam/R2.

---

# Part I — Method candidates (new Gate 0 criteria)

## The fast-iteration loop every M-candidate uses (built by experiment; being validated on one pair now)
- **Init:** released LOL-v1 `w_perc.pth` (sha256 logged in `ralph/results/phase0_weights.json`).
- **Iteration run:** 50 epochs from those weights, short warmup then cosine re-annealed to the new end, lr recorded;
  scene-disjoint val (40 pairs, split `scene_v1`) every epoch; **≈ 25 min on one 2080 Ti, 4 variants per wave**
  (≈ 10 waves/day ≈ 40 variants/day). eval15 never read. Selection = the candidate's **locus metric on val** plus
  val GT-mean PSNR (scalar gain) as the guard that the global number did not regress.
- **Validity guard:** the loop is trusted only if the A0-vs-A2 ranking after 50 fine-tune epochs agrees in sign and
  rough size with the 1000-epoch from-scratch pair (`phase0_finetune_rankcheck.json`, due ≈ 8 h after dispatch).
  If it disagrees, iteration runs move to 150-epoch fine-tunes (≈ 75 min) and the check is repeated.
- **Final table only:** best component + upstream baseline (+ the strongest published baseline we can retrain)
  × **3 seeds from scratch**, 1000 epochs (≈ 7.7 GPU-h each); test read once by `final_eval_test.py`; the C1 ladder
  is run as the ablation chapter (in fine-tune mode by default, ≈ 2 GPU-h for 5 arms; from scratch only if the author
  asks). Analysis by the frozen `analysis_c1.py` rules (paired-by-seed, Holm, TOST ± 0.3 dB, decile mechanism rule).

## M1 — Dark-chroma confidence: fix colour at dark, low-saturation pixels
**Locus + evidence.** Exact black gives an arbitrary 45° hue (`atan2(V+ε, H+ε)`, CJ hvi_transform) and the inverse
divides by C_k; the paper itself downgraded HVI from "one-to-one" to "surjective" (phase0_related §4.2.12); BC-IHV
(`ai2026bcihv`) shows the colour space sets the gradient dynamic range (log-IHV 1001× vs learned Box-Cox 12×) and
HVI-CIDNet+ (`yan2025hvicidnetplus`) had to add a region-refinement block for extreme darkness; MILL
(`pilligua2025mill`) measures ΔE76 rising 10.6 → 25 under intensity blends. Our own instrument already exports
per-intensity-decile ΔE00 and chroma-weighted hue error, and R2 rule 5 predicts A0−A2 differences sit in the bottom 3
deciles. **Metric:** ΔE00 and |Δh|·S_gt in the bottom 3 GT-intensity deciles on val; darkness stress test (× 0.5,
× 0.25 + Poisson–Gaussian) as dose–response; global GT-mean PSNR as guard.
**Component.** *Chroma-confidence gating in the HV branch*: the predicted HV residual is blended, per pixel, between the
network output and a locally-smoothed chroma prior with weight g = σ(a·C_k(I) + b) (two learned scalars, or a 1×1 conv
on [C_k, S]), so chroma is trusted where intensity supports it and regularised where it does not; plus a
**hue-consistency loss on dark pixels** (circular hue error weighted by S_gt, restricted to I_gt below the 30th
percentile) and the loss-side k **frozen and detached** (R2 §1b) so the model cannot shrink the chroma loss by moving k.
Adds < 1 k parameters; loads the released weights unchanged.
**Fast loop.** Wave 1: gate on/off × hue-loss on/off (4 runs, 25 min). Wave 2: gate parametrisation (scalar / 1×1 /
C_k-only) and the dark-pixel threshold (p20/p30/p40). Wave 3: k frozen vs learned under the new loss. ≈ 3 waves ≈ 1.5 h
of wall-clock per round.
**Baselines to beat.** Upstream w_perc (fine-tuned 50 epochs with no component — the fair control), upstream
`--gamma` augmentation (U[0.6, 1.2], CJ), BC-IHV's learnable intensity law (`ai2026bcihv`; LOL-v2-Real controlled
22.54 → 24.21 dB, no LOL-v1 number in files), RHVI-FDD's illumination refinement (`yang2026rhvifdd`; 23.92 → 24.82 on
LOL-v2-Real), HVI-CIDNet+ region refinement (`yan2025hvicidnetplus`; +0.77 dB GT-mean LOL-v1), PAL loss (`li2026pal`;
23.97 → 24.13 LOL-v1), GT-mean loss (`liao2025gtmean`). Re-implementable in the loop: gamma aug, PAL, GT-mean loss,
a Box-Cox intensity law; the others are reported from their papers with the dataset/GT-mean status stated.
**Novelty risk (one line).** Medium: BC-IHV and RHVI-FDD alter the *intensity* law; nobody gates *chroma* by
intensity confidence inside CIDNet, but a reviewer may call the gate "a learned C_k" — the decile-localised evidence
and the dose–response curve are what make it a finding rather than a tweak.

## M2 — Exposure-equivariant intensity branch: robustness to brightness-shifted inputs
**Locus + evidence.** MILL (`pilligua2025mill`, D): CIDNet's luminance PSNR falls 26.38 → 17.72 dB at a 20 % blend
toward GT and to 14.12 at 50 %, trailing Retinexformer at every intensity level; `du2026atp` reports "significant
luminance deviations"; NTIRE 2026 zero-shot CIDNet scores 13.85 dB, below plain gamma correction at 14.91
(`ciubotariu2026ntire`, D/E). Upstream's only answer is random-gamma input augmentation (off by default).
**Metric:** PSNR / ΔE at MILL-style blend levels {0, 20, 50 %} and at input gains {× 0.5, × 2} on val
(chroma-preserving jitter of I only), and the log-exposure error log(mean_out/mean_gt); global GT-mean PSNR as guard.
**Component.** *Exposure-conditioned I-branch*: a FiLM modulation of the I-branch (per-level scale/shift from a
2-layer MLP on [log mean I, log p10 I, log p90 I] of the input, ≈ 2 k params) plus an **intensity-equivariance
consistency loss** in HVI space: for a random gain s, ‖f(s·I, HV) − T_s(f(I, HV))‖ where T_s is the expected shift in
log-I (chroma untouched, which HVI makes possible and RGB does not). Training-time jitter is applied to I only, so this
is *not* the upstream gamma augmentation (which moves chroma too) and *not* InterLight's sensor-level augmentation.
**Fast loop.** Wave 1: FiLM on/off × consistency on/off. Wave 2: jitter range and statistics fed to FiLM. Wave 3:
compare against upstream `--gamma` and PAL under identical fine-tuning.
**Baselines to beat.** Upstream w_perc + `--gamma` aug (CJ), PAL (`li2026pal`), GT-mean loss (`liao2025gtmean`),
InterLight's illumination prompts + augmentation (`wang2026interlight`, gain not in files), MILL's own training
(`pilligua2025mill`), Retinexformer at each MILL level (reported).
**Novelty risk (one line).** Medium–high: InterLight (2026) already combines augmentation with illumination prompts on
HVI; ours must stand on HVI-specific chroma-preserving equivariance and on the MILL-protocol numbers, otherwise it
reads as "augmentation helps".

## M3 — HVI-aware supervision: replace the meaningless VGG-on-HVI term and fix the range shift
**Locus + evidence.** The perceptual loss uses `range_norm=True` (x → (x+1)/2 before ImageNet normalisation,
vgg_arch.py:228-231, CJ): RGB is fed as [0.5, 1] (brightened, contrast halved) and (H, V, I) tensors get ImageNet
VGG features with no perceptual meaning (R2 §1d); the paper never mentions it. README: wo_perc 23.50 / 28.14 (GT-mean)
vs w_perc 23.81 / 27.71 — the perceptual term *lowers* the GT-mean number. The only non-RGB composite-loss precedent is
U-Shape Transformer (`peng2023ushape`, RGB + Lab/LCH). **Metric:** LPIPS and ΔE00 on val (global and in low-saturation
pixels), plus GT-mean PSNR; the locus is *perceptual/colour fidelity*, not PSNR.
**Component.** *Loss-only*: VGG kept on correctly-ranged RGB only; on the HVI side a **C_k-weighted chroma-structure
loss** (SSIM on the (H, V) plane weighted by C_k(I_gt), so dark pixels do not dominate) and an explicit hue term.
Zero new parameters; every iteration is a 25-min fine-tune from w_perc, which is exactly what a loss change needs.
**Fast loop.** Wave 1: {upstream loss, range fixed, VGG off HVI, both}. Wave 2: chroma-structure weight and the hue
term. Wave 3: interaction with `--gamma` aug.
**Baselines to beat.** w_perc and wo_perc released weights (fine-tuned identically), PAL, GT-mean loss, U-Shape's
Lab/LCH loss (`peng2023ushape`), VCR's colour-distribution alignment (`cheng2026vcr`; 24.11 → 24.76 on LOL-v2-Real).
**Novelty risk (one line).** Medium: a loss recombination plus the documentation of an undocumented range shift;
strong as a diagnostic chapter, weak as a headline unless the low-saturation ΔE00 gain is clear.

## M4 — Repaired and symmetric LCA fusion
**Locus + evidence.** HV_LCA has no FFN residual while I_LCA has both; I_LCA5's output is overwritten (CIDNet.py:105,
109) so 70,960 parameters never receive a gradient; encoder stage 3 consumes pre-LCA2 features (:94-95) so LCA2 reaches
the decoder only via skips (CJ, phase0_related §1.2). No follow-up fixes these; TCA-Net (`wu2026tcanet`), HAIMNet
(`wang2026haimnet`) and WIRNet's gated LCA (`ciubotariu2026ntire`) replace the fusion instead. **Metric:** edge PSNR
(already exported) and PSNR in high-gradient regions on val; global GT-mean PSNR.
**Component.** Repair the three wiring defects, then a **gated bidirectional LCA** (one learned gate per block deciding
how much cross-branch information enters). Loads released weights for every unchanged tensor; the resurrected block
starts from its (never-trained) initialisation.
**Fast loop.** Wave 1: {upstream, +residual, +I_LCA5 live, +LCA2 feed}. Wave 2: gate on/off.
**Baselines to beat.** Upstream; TCA-Net, HAIMNet, WIRNet (reported only; numbers not in files); the C1 ladder for the
representation side.
**Novelty risk (one line).** High: bug fixes are not a method, and gated LCA already appeared at NTIRE 2026 — only the
measured size of the wiring defects (a reproducibility finding) is safely new.

## M5 — Illumination-normalised inference for zero-shot / cross-dataset use
**Locus + evidence.** NTIRE 2026: zero-shot CIDNet 13.85 dB, below gamma correction 14.91 (`ciubotariu2026ntire`);
Efficient-LLIE HVI entries ranked 5th/12th/17th (`yan2026ntireellie`); MILL brittleness as in M2. **Metric:**
deduplicated LOL-v2-Real PSNR/ΔE00 and NTIRE-style min-max PSNR if the challenge data can be downloaded; unpaired
NIQE/MUSIQ as secondary. Requires new data on disk (checksums logged).
**Component.** *Exposure normalisation in HVI*: divide I by a robust exposure estimate before the network, predict in
normalised space, re-apply; **test-time self-ensembling over exposure scales** with a chroma-consistency criterion
(only HVI allows changing I without touching chroma). Trained with the M2 jitter.
**Fast loop.** As M2, plus a zero-run TTA sweep on saved fine-tunes.
**Baselines to beat.** Gamma correction (14.91 dB), upstream `--gamma`, InterLight, FusionNet (`shi2025fusionnet`,
NTIRE 2025 winner), MB-LPFR/Wave-P (NTIRE 2026 entries, ranks only).
**Novelty risk (one line).** High on data availability and medium on idea (TTA over exposure is common); the locus is
the most convincing to an outside reader but the least controllable in a two-week thesis.

## Ranking (locus measurability × fit to the 25-min loop × chance to beat the named baselines × novelty)

| # | Candidate | Locus metric already instrumented? | Loop fit | Novelty risk | Score |
|---|---|---|---|---|---|
| 1 | **M1 dark-chroma confidence** | yes (deciles, hue error, stress test) | excellent (< 1 k params, loads w_perc) | medium | ★★★★★ |
| 2 | **M2 exposure-equivariant I-branch** | partly (log-exposure error; MILL blends to add) | very good | medium–high | ★★★★ |
| 3 | M3 HVI-aware supervision | yes (LPIPS, ΔE00) | perfect (loss-only) | medium | ★★★★ (as a chapter) |
| 4 | M4 repaired LCA | yes (edge PSNR) | good | high | ★★ |
| 5 | M5 illumination-normalised inference | no (needs new data) | good | high (data) | ★★ |

**Recommendation: M1 as the thesis method**, with M3's loss fix as its first loop wave (a loss change costs one
25-min run and M1's hue loss lives in the same file), and **M2 as the pre-committed pivot** if M1's bottom-decile gain
does not clear the decision rules after two loop rounds. The C1 ladder (A0/A2/A3/A4 + L1, fine-tune mode) is the
ablation chapter for either. Budget after Gate 0: ≈ 3 loop rounds (≈ 12 waves ≈ 6 h wall-clock on 4 GPUs), then
6 from-scratch runs for the final table (≈ 12 h wall-clock) + the ladder in fine-tune mode (≈ 1 h).

---

# Part II — C-series (the earlier question candidates; C1 = ablation chapter)


## Shared facts that constrain every candidate
- **Baseline protocol = the code, not the paper text**: 1000 epochs, batch 8, crop 256, Adam 1e-4 with 3-epoch warmup
  (epoch 1 at lr 0) then cosine, no effective gradient clipping, 485 LOLv1 train pairs. The paper text says 1500 epochs
  and 400² crops; those do not fit the released code or an 11 GB GPU at batch 8, and the code is what anyone can run. One full-protocol
  run on one RTX 2080 Ti = **R ≈ 9.1 h** measured (26.2 s/epoch train + 50-image validation each epoch; 7.3 h
  train-only; peak 9.8 GiB of 11; key `cost.projected_hours_full_schedule` in phase0_codebase.json). Validating
  every 5 epochs instead of every epoch brings R to ≈ 7.7 h. 4 GPUs → ≈ 10–12 runs/day; ≈ 70 runs/week.
  Same-seed run-to-run noise (non-deterministic CUDA kernels) is measurable (0.04 dB val PSNR after 2 epochs) and
  will be reported as a floor under the seed spread; bitwise-strict mode costs 1.5× and is not the default.
- Upstream reports **single runs with a random, unlogged seed**, and its training loop **scores every 10th
  checkpoint on the test split** (eval15); the released `best_PSNR`/`best_SSIM` weights imply selection on those scores. Our frozen protocol will hold out a validation subset of the 485 training pairs and select on it. So
  every candidate below produces, as a by-product, the first seeded reproduction of HVI-CIDNet on LOLv1.
- Three seeds per condition is the floor (plan §1). A difference smaller than the seed SD is "no measurable
  difference" — and that is a publishable thesis result here.
- Only LOLv1 is on disk. Anything else costs a download + checksum log, not GPU time.

---

## C1 — What in the HVI representation matters, under an identical CIDNet, a frozen loss, and matched seeds?  *(v4: rewritten as the nested ladder of `ralph/related/redteam/R2_design_redteam.md`, at the author's request)*

**Why the old C1 was wrong (R2 §1–§3).** "Swap the colour space" changed four things at once (branch split,
auxiliary-loss space, learnable k, residual space); a split-less sRGB arm is a different architecture; HSV-polar is a
strawman the authors already ran (R1: CVPR'25 Table 4 on LOL-v2-Real and CIDNet+ Table V on LOL-v1 — single runs, and
the sRGB-vs-HSV sign flips between them); and with n = 3 seeds no paired test can reach p < 0.05, so "within seed
spread" would have been a guaranteed non-finding. R1's verdict: partially done, not redundant — no seeded, validation-
selected, YCbCr-inclusive comparison exists in any restoration task.
**Survey reconciliation (SURVEY.md §1, gaps 1, 3, 4).** Two contrasts on the ladder have single-run precedents and are
stated as *seeded replications with mechanism localisation*, not new ground: (a) C_k on/off inside CIDNet — HVI-CIDNet+
(`yan2025hvicidnetplus`) reports C_k-only 27.99 vs full HVI 28.85 dB on LOL-v1, one run — this is A0 − A2; (b) YCbCr vs
HVI — TPCNet (`shi2025tpcnet`) ran HVI / LAB / YCbCr in *its own* network on LOL-v2-Real, one run, with YCbCr ahead
(24.98 vs 24.64); VCR (`cheng2026vcr`) and RHVI-FDD (`yang2026rhvifdd`) also ablate spaces in their own nets. YCbCr
has never been run inside CIDNet (A3, A4). No seeded colour-space comparison exists in any restoration task; the
seed-variance framing follows Bouthillier et al. (`bouthillier2021variance`) and Musgrave et al. (`musgrave2020reality`).
The published LOL-v1 spread the ladder must explain — 23.5–24.0 dB raw (third-party) vs 28.2 dB (paper, GT-mean) —
is SURVEY gap 4 (FusionNet `shi2025fusionnet`, PAL, issue #66).

**Question.** Along a nested ladder of single-factor steps inside the same two-branch CIDNet, with the same loss in
every arm and five matched seeds, which step moves LOL-v1 quality by more than the paired seed spread — and is the
C_k effect located where its mechanism predicts (dark pixels)?

**Common to all arms.** Same network and parameter count; residual taken in the working space; **frozen loss**
L = L_rgb (L1 + 0.5·SSIM + 50·edge + 0.01·VGG) + L_hvi at a constant k0 (L1 + 0.5·SSIM + 50·edge, **no VGG**), with
no gradient reaching k through the loss (upstream does not detach k; diagnostic arm U measures the drift that causes).
Val split scene-disjoint (§Protocol). Five matched seeds per arm (seed s fixes data order, crops, flips, and the init of
every shape-identical layer). Test-time inverse-transform knobs (gated, alpha, gamma) fixed to identity in every arm.

| Arm | Representation (I-branch / HV-branch) | Isolates (vs neighbour) | Runs |
|---|---|---|---|
| A0 | HVI, learned k | reference: upstream model under the fixed loss | 5 |
| A1 | HVI, k frozen at A0's median converged k | learned vs fixed k — **dropped if A0's k moves < 0.05** (then A1 := A0) | 5 (0) |
| A2 | HVI with k = 0 (Cartesian HSV: I = max, S·cos h, S·sin h) | **the C_k intensity collapse — primary contrast A0 − A2** | 5 |
| A3 | I = max / linear opponent chroma (Cb, Cr) | saturation-polar vs linear chroma (A2 − A3) | 5 |
| A4 | YCbCr (I = Y / Cb, Cr) | intensity definition max vs luma (A3 − A4); expect mainly an exposure effect | 5 |
| L1 | HVI learned k, L_rgb only | contribution of the auxiliary HVI loss (A0 − L1), secondary family | 5 |
| R (opt.) | split-less RGB reference (I = Y; HV-branch emits a 3-ch RGB residual) | sanity anchor only; **not** a point on the colour-space axis | 3 |
| U (diag.) | A0 with upstream's coupled-k loss | k loss-hacking check (k trajectory + PSNR) | 1 |

Dropped: HSV-polar (predictable, published) and split-less sRGB *as a colour-space arm*.

**Read-outs per run (R2 §4b).** Primary: the **final epoch-1000 checkpoint** (cosine ends at lr ≈ 0; selection-free).
Secondary: best-val-PSNR checkpoint. Oracle: test PSNR of every 10th checkpoint — **computed post hoc, once, by the
frozen `final_eval_test.py` in a dedicated pass after all arms finish**, from checkpoints saved every 10 epochs
(~0.8 GB/run), so training and selection never touch eval15 (integrity floor rule 4 kept literally); its JSON is
labelled `oracle`, never used to rank arms. Selection bias (old C2) = oracle − final and oracle − val-selected;
max-over-seeds of the oracle is the "paper-style" number.

**Metrics (R2 §4c).** Primary: **GT-mean PSNR with one scalar luminance gain** (never per-channel), mean over the 15
test images, per run. GT-mean has no citable origin beyond LLFlow/KinD/Retinexformer practice (SURVEY gap 5) and uses
the GT at inference (Retinexformer's leakage warning; GT-Mean Loss, Liao et al. ICCV 2025 `liao2025gtmean` quantifies
the 23.8 → 27.7 dB jump); the raw-PSNR decomposition below is reported alongside for exactly that reason. Secondary: raw PSNR, SSIM, LPIPS, ΔE00 (raw and after scalar gain), log-exposure error
log(mean_out/mean_gt), and the decomposition raw MSE ≈ gain error + GT-mean residual. Zero-run analyses on saved
outputs: per-GT-intensity-decile RGB MSE, ΔE00 and chroma-weighted circular hue error |Δh|·S_gt per arm and seed with
seed-level CIs; darkness stress test (inputs × 0.5, × 0.25 + Poisson–Gaussian noise) giving a dose–response curve of
Δ(A0 − A2) hue error; LOL-v2-Real evaluation only after deduplication against the LOL-v1 train set.

**Pre-registered decision rules (R2, verbatim in substance).**
1. Primary metric/read-out: GT-mean PSNR (scalar gain) at the final checkpoint, per run.
2. Primary contrasts: A0−A1, A0−A2, A2−A3, A3−A4, paired by seed (n = 5), Holm-corrected across the four.
   A0−L1 is a separate secondary family.
3. **Difference claimed** only if (a) the paired 95 % t-CI (df = 4) excludes 0 after Holm; (b) |mean Δ| ≥ 0.3 dB and
   |mean Δ| > 2·SD(Δ_s); (c) the sign of Δ_s agrees in ≥ 4 of 5 seeds; (d) a mixed model
   PSNR ~ arm + (1|image) + (1|seed) agrees in direction. Per-image Wilcoxon tests are descriptive only.
4. **Equivalence claimed** only if TOST with margin ± 0.3 dB rejects at α = 0.05; otherwise "inconclusive". The
   phrase "less than the seed spread" is never used as a claim.
5. **Mechanism claim for C_k** (A0 vs A2): the hue-error or ΔE00 difference in the bottom 3 intensity deciles has a
   seed-level CI excluding 0, while the top-5-decile difference includes 0 or is ≥ 3× smaller; the darkness stress
   test shows |Δ| increasing monotonically across × 1, × 0.5, × 0.25.
6. **Pipeline gate:** A0 mean raw PSNR ∈ [23.3, 24.3] dB and seed SD ≤ 0.5 dB before any other arm launches.
   If SD > 0.4 dB, raise seeds to 8 on A0, A2, A3 only.
7. Selection bias reported as (oracle − final) and (oracle − val-selected), mean ± SD over seeds, plus the
   paper-style max; never used to rank arms.
8. Frozen before launch, with hashes committed: loss weights, k0, the scene-cluster val split, the inverse-transform
   knobs, the metric code, the analysis script. eval15 is read only by the frozen final-eval script.
9. **Pivot trigger → C3:** the pipeline gate fails, or σ_seed > 0.6 dB even with 8 seeds.

**If it works.** "Step X of the ladder moves GT-mean PSNR by Δ = x ± s dB (paired, n = 5, Holm-corrected), and the
C_k gain sits in the darkest three deciles and grows as the input gets darker." **If it fails.** Every step is either
equivalent within ± 0.3 dB (TOST) — "inside CIDNet the HVI representation is not distinguishable from linear
luma/chroma at this power" — or inconclusive with the measured seed SD reported; the mechanism analysis and the
selection-bias numbers stand regardless. All three are a thesis.

**Cost (measured, `phase0_codebase.json`).** Validation every 5 epochs → ≈ 7.7 GPU-h per run (7.3 h train-only;
R2's 5–6 h estimate was optimistic). Core A0 + A2 + A3 + A4 + L1 = **25 runs ≈ 190 GPU-h ≈ 2.0 days on 4 GPUs**;
with A1 + R + U ≈ 34 runs ≈ 2.7 days. Order: the 5 A0 seeds first (pipeline gate + σ_seed + k trajectory ≈ 16 h
wall-clock), then the rest in waves of 4. One pilot pair (A0, A3) checks whether the ranking at 250/500/1000 epochs is
stable to 0.1 dB before any schedule shortening (R2 §4d); the schedule is re-annealed, never truncated.

**Protocol additions this candidate requires (instrument work, no training).** (i) Scene-disjoint val split — **done** (`auto-research/split_scene_v1.json`, 40 val / 445 train, sha b0dde627).
**Measured caveat:** 14 of the 15 LOL-v1 test images have a train near-duplicate at DINOv2 cosine > 0.9 (13 at > 0.95), and
24 train images share a scene cluster with the test set. Default: they stay in training (matched across arms, keeps
upstream comparability and the pipeline gate); the thesis states this, and the deduplicated LOL-v2-Real evaluation is
mandatory, not optional. (ii) k0 constant and detached in the loss.
(iii) Checkpoints saved every 10 epochs. (iv) Transforms kept in FP32 (no AMP on atan2 / max / pow).
(v) Parameter counts asserted identical across arms.

**Risk of triviality.** R1 §Triviality: A3 vs A4 and R may land within noise (the linear-reparameterisation
expectation), and that is stated as a prediction; A0 vs A2 and A2 vs A3 are the informative contrasts. Limitation
stated up front: loss weights and lr were tuned upstream for HVI (conservative for a null, anti-conservative for a win);
a 3-point lr sweep on A0 and A3 (1 seed, 250 epochs) is optional if budget allows.

## C2 — Seed variance and test-set selection bias  *(folded into C1's read-outs; kept as a heading for the record)*
Answered at zero extra cost by C1's design: σ_seed from the five A0 seeds (pipeline gate), and selection bias from
(oracle − final) and (oracle − val-selected), with the oracle computed post hoc, once, by the frozen final-eval script.
LOL-v1 reference points: README 23.81 dB (raw) / 27.71 (GT-mean); paper table 28.20 (GT-mean, single run).

## C3 — The density term: does k matter, and what happens near black?
**Question.** Fixed k ∈ {0.1, 0.2, 0.5, 1.0, 2.0} (code convention; the code's k is the reciprocal of the paper's)
vs learnable k (upstream default, init 0.2): does k change LOLv1 quality,
and does the exact-black singularity (inverse divides by C_k ≈ 0.025 at I≡0; hue → arbitrary) show up as measurable
error in the darkest intensity bins? (Measured: for I<1/255 the inverse gain is 0.014 per unit chroma, so any effect
is confined to pixels at or within one code value of black, plus whatever k does to training.)
**Why open.** No k sweep in the paper; the learnable k also receives gradient through the target transform HVIT(gt),
so the model can shrink its own loss by collapsing chroma — unexamined. RHVI-FDD / BC-IHV (2026) replace the
intensity law with new modules but never sweep the original.
**If it works.** "k is a sensitive knob: Δ = x ± s dB across the sweep; learned k drifts to k*; error is concentrated
in the bottom-decile intensity bin." **If it fails.** "Quality is flat in k within seed spread; the density term's
claimed role is not measurable on LOLv1" — a thesis, and a direct comment on the paper's ablation.
**Minimal experiment.** 6 conditions × 3 seeds = **18 runs** (≈ 165 GPU-h, ≈ 1.7 days on 4 GPUs); plus a free per-pixel analysis (PSNR/hue error binned
by GT intensity) on saved outputs. **Risk of triviality.** Low–medium (flat curves are plausible and still a result).

## C4 — Dual-space objective: which loss terms matter, with seeds?
**Question.** {RGB+HVI loss (default), RGB only, HVI only} × {with, without VGG-perceptual}: which of the six
objectives differ by more than the seed spread on LOLv1?
**Why open.** Paper's loss ablation is single-run on LOLv2-Real (23.22 / 23.32 / 24.11); the duplicated dual-space
objective has no Tier-1 precedent (SURVEY gap 6; U-Shape Transformer is the nearest); issue #163 asks how the
weights (edge 50, SSIM 0.5, VGG 0.01) were chosen; the perceptual loss shifts its RGB input to [0.5,1] before ImageNet
normalisation (range_norm), so the RGB-side perceptual term sees a systematically brightened image — worth measuring.
**Works / fails.** "Dual-space loss adds x ± s dB over RGB-only" / "the second loss space adds nothing measurable;
the perceptual term adds nothing measurable at weight 0.01." **Minimal experiment.** 6 × 3 = **18 runs**.
**Risk of triviality.** Medium: loss ablations are common; the seeded angle and the HVI-perceptual oddity are new.

## C5 — Robustness: do color-space models degrade differently under noise / JPEG / domain shift?
**Question.** Apply Gaussian noise (σ ∈ {5, 15, 25}/255), JPEG (q ∈ {90, 70, 50}) to LOLv1 test inputs, and
evaluate on LOLv2-Real test and unpaired sets (NIQE): does the color-space ranking from C1 hold?
**Why open.** RHVI-FDD argues max-RGB intensity is noise-sensitive but only tests its own fix; SURVEY gap 7: HVI's
robustness claims are untested, learned-k generalisation is examined only inside FusionNet/Multinex
(`shi2025fusionnet`), and MILL (`pilligua2025mill`) covers intensity levels only.
**Minimal experiment.** **0 training runs** — reuses C1 checkpoints; eval-only, ~1 GPU-h. The darkness/noise
dose–response part is now inside C1 (decision rule 5); the LOL-v2-Real part needs a download and deduplication against
the LOL-v1 train set. **Risk of triviality.** Medium; works only as C1's follow-on, not stand-alone.

## C6 — Efficiency: is CIDNet over-parameterised for a consumer GPU?
**Question.** Width scale {0.5, 0.75, 1.0} × 3 seeds: PSNR vs latency / VRAM on a 2080 Ti.
**Works / fails.** "Half-width loses x ± s dB for 3× speed" / "half-width matches full within seed spread".
**Minimal experiment.** 9 runs (cheaper than R each). **Risk of triviality.** High: monotone curves are expected
and the finding is generic to any U-Net; weakest link to the HVI idea.

---

## Ranking  (decidability × size of gap × survives a negative result)

| # | Candidate | Runs | Decidable with our compute | Gap size | Negative result still a thesis | Score |
|---|---|---|---|---|---|---|
| 1 | **C1 nested HVI ladder (A0/A2/A3/A4 + L1), 5 matched seeds; C2 folded in** | 25 (+9 opt.) | yes, ≈ 2.0 (2.7) days on 4 GPUs | large (the paper's central claim, never seeded; C_k on/off run once unseeded; YCbCr never inside CIDNet; k never swept) | yes: TOST/inconclusive + mechanism + selection bias | ★★★★★ |
| 2 | C3 density k + near black | 18 | yes, ≈ 1.7 days | medium–large (untested knob, real artefact) | yes | ★★★★ |
| 3 | C4 dual-space loss + seeds | 18 | yes, ≈ 1.7 days | medium (issue #163, perceptual oddity) | yes | ★★★ |
| 4 | C5 robustness | 0 | yes, hours | medium | partly | ★★★ (as C1's follow-on) |
| 5 | C6 efficiency | 9 | yes, ~1 day | small | weak | ★★ |

**Recommendation: C1 (the R2 ladder) as the thesis, with C2 folded into its read-outs and C5's dose–response test
inside its mechanism rule. C3 (density-k sweep) is the pre-committed pivot** (rule 9) and a close second overall.
Budget: 25 core runs ≈ 2.0 days on 4 GPUs (≈ 2.7 days with the optional A1, R and U arms), inside a two-week window.

Rejected families and why: a targeted new module (needs a pre-registered improvement and competes with 2026
follow-ups we cannot beat in a bachelor's budget); more datasets before the LOLv1 question is settled (adds download
and protocol risk, not evidence).
