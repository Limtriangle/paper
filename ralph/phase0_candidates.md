# phase0_candidates.md — thesis candidates (master)

Status: **v8** (2026-09-24 02:35 UTC): v6 = the author's requested "v5 method candidates"; v7 folded in the author's novelty checks M1–M3 (their numbering); **v8 adds the six transfer-style candidates T1–T6 with the author's verdicts and re-ranks: T1 (+T3) recommended, M2 pivot.** Part I below is new: five
method candidates M1–M5 under the author's new Gate 0 criteria (INBOX line 18). Part II is the earlier C-series
(v5, survey-reconciled); **C1, the R2 nested ladder, is now the ablation chapter of whichever method wins**, and C3–C6
are kept for the record. Evidence keys are in `ralph/related/survey.bib` unless noted; file pointers use
D = related/D_hvi_followups.md, E = related/E_evaluation.md, CJ = results/phase0_codebase.json, R2 = redteam/R2.

---

# Part I — Method candidates (new Gate 0 criteria; numbering follows the author's novelty checks in `ralph/related/novelty/`)

**Novelty verdicts (author's checks, 2026-09-24): M1, M2, M3 are all INCREMENTAL.** Each candidate below therefore
states the *narrowly novel version* the check identified, the closest work it must cite, the strongest baseline it
must beat, and the check's own "cheapest deciding experiment" mapped onto our 25-min loop. v6 → **v7**.

## The fast-iteration loop every M-candidate uses (built by experiment; being validated on one pair now)
- **Init:** released LOL-v1 `w_perc.pth` (sha256 logged in `ralph/results/phase0_weights.json`).
- **Iteration run:** 50 epochs from those weights, short warmup then cosine re-annealed to the new end, lr recorded;
  scene-disjoint val (40 pairs, split `scene_v1`) every epoch; **≈ 25 min on one 2080 Ti, 4 variants per wave**
  (≈ 10 waves/day ≈ 40 variants/day). eval15 never read. Selection = the candidate's **locus metric on val** plus
  val GT-mean PSNR (scalar gain) as the guard that the global number did not regress.
- **Validity guard:** the loop is trusted only if the A0-vs-A2 ranking after 50 fine-tune epochs agrees in sign and
  rough size with the 1000-epoch from-scratch pair (`phase0_finetune_rankcheck.json`, due ≈ 8 h after dispatch).
  If it disagrees, iteration runs move to 150-epoch fine-tunes (≈ 75 min) and the check is repeated.
- **Final table only:** best component + upstream baseline + the strongest re-implementable baseline × **3 seeds from
  scratch**, 1000 epochs (≈ 7.7 GPU-h each); test read once by `final_eval_test.py`; the C1 ladder is run as the
  ablation chapter (fine-tune mode by default, ≈ 2 GPU-h for 5 arms). Analysis by the frozen `analysis_c1.py` rules
  (paired-by-seed, Holm, TOST ± 0.3 dB, decile mechanism rule).
- **Data:** LOL-v1 on disk; LOL-v2-Real (deduplicated against LOL-v1 train) and MILL's benchmark / SICE are downloads
  with logged checksums — needed by M1's locus and by every final table's generalisation column.

## M1 — Exposure-conditioned HVI: per-image transform parameters for brightness-shifted inputs
**Locus + evidence.** MILL (`pilligua2025mill`, D): CIDNet's luminance PSNR falls 26.38 → 17.72 dB at a 20 % blend
toward GT and 14.12 at 50 %, trailing Retinexformer at every level; NTIRE 2026 zero-shot CIDNet 13.85 dB, below
gamma correction at 14.91 (`ciubotariu2026ntire`); `du2026atp` "significant luminance deviations". Upstream's only
answer is random-gamma augmentation (off by default, U[0.6, 1.2], CJ).
**Novelty check (`novelty/M1_exposure_conditioned.md`): INCREMENTAL.** Exposure conditioning/normalisation is taken:
MILL (intensity-prediction + scene-invariance losses), ENC (CVPR 2022, feature-level exposure normalisation),
CLE-RWKV (FiLM on a brightness scalar, HVI supervision), BC-IHV's AdaLN exposure modulation, AutoLumNet (per-image
tone curve), CAGE (image-adaptive colour space). **Not found anywhere:** predicting the HVI transform's *own*
parameters (k, gain, gamma) per image from input statistics with an exact inverse in PHVIT.
**Component (the narrowly novel version).** A tiny network reads intensity-histogram statistics of the input and
outputs k(x), a gain and a gamma applied *inside* HVIT, inverted exactly in PHVIT; trained with an
**exposure-consistency loss** (same scene at different input exposures → same HVI chroma and same output; jitter
applied to I only, which HVI allows and RGB does not). Comes with the analysis of *why* a fixed global k collapses
when the input brightens (C_k saturates, chroma scale changes) and how conditioning removes it. Loads w_perc; adds
≈ 2 k params.
**Metric.** Worst-level and mean PSNR/ΔE over LOL-v1 GT-blends α ∈ {0, 0.1, 0.2, 0.35, 0.5} and input gains
{× 0.5, × 2, × 4} on val; MILL's 11 levels and SICE zero-shot if downloaded; log-exposure error; GT-mean PSNR guard.
**Baselines to beat (from the check).** (b) upstream random-gamma/gain augmentation at the *same augmentation budget*
and no conditioning — the strongest; (c) augmentation + a **zero-parameter wrapper** (scale input so mean(I) matches
the LOL-v1 training mean, run frozen CIDNet, invert) — my former "illumination-normalised inference" idea, now a
baseline; CIDNet + MILL's intensity-prediction and triplet losses; PAL (`li2026pal`) and GT-mean loss
(`liao2025gtmean`); InterLight (`wang2026interlight`), ENC, CLE-RWKV, AutoLumNet reported.
**Fast loop (the check's deciding experiment, ported).** Wave 1: (a) vanilla fine-tune, (b) + gamma/gain aug,
(c) + aug + wrapper, (d) + aug + predicted k/gain/gamma. **Go/no-go:** (d) beats (b) and (c) by ≥ 1 dB at the worst
brightness level while staying within 0.3 dB on standard LOL-v1 val; otherwise M1 is a preprocessing trick and is
dropped. Waves 2–3: consistency-loss weight, which statistics feed the predictor, jitter range.
**Novelty risk (one line).** Medium: the per-image *transform* parametrisation is unclaimed, but the locus is crowded
(MILL, ENC, InterLight) and the wrapper baseline may already take most of the gain.

## M2 — Spatially adaptive, noise-calibrated density: a per-pixel k(x) with a conditioning bound
**Locus + evidence.** Exact black → arbitrary hue (CJ hvi_transform); the paper downgraded HVI to "surjective"
(phase0_related §4.2.12); BC-IHV (`ai2026bcihv`) ties the inverse-gradient range to the intensity law (log-IHV 1001×
vs Box-Cox 12×, λ learned 0.82/0.65/0.57 per dataset) but keeps k global; HVI-CIDNet+ needed a region-refinement block
for dark regions; MILL's ΔE76 rises 10.6 → 25 under blends. Our instrument already exports per-decile ΔE00 and
chroma-weighted hue error; R2 rule 5 predicts A0−A2 effects concentrate in the bottom 3 deciles.
**Novelty check (`novelty/M2_adaptive_density.md`): INCREMENTAL, not taken.** No HVI derivative makes k or C_k
per-pixel or noise-aware (CIDNet+, BC-IHV, RHVI-FDD, TCA-Net, VCR, InterLight, CAGE, UCAMNet, HAIMNet, DLFE-Net all
keep one global k). Closest: RHVI-FDD (per-pixel refined I′ into the unchanged C_k — implicitly spatial), BC-IHV
(global λ with closed-form inverse conditioning), CAGE (lightness-conditioned chroma scaling, global per image).
Conceptual precedent: ISP chroma suppression (US 9142012 family: per-pixel Cb/Cr gain from luminance × a
high-frequency noise proxy) — must be cited, not reinvented.
**Component (the narrowly novel version).** **k(x) predicted per pixel from (I, S, σ(I))** with σ a physically
calibrated Poisson–Gaussian noise estimate, under the constraint **C_{k(x)}(I) ≥ c·σ(I)/I** so the inverse
amplification of chroma noise is bounded per pixel — extending BC-IHV's global κ analysis to a spatial field; shown to
be a Wiener-like chroma shrinkage inside an exactly invertible encoding (k(x) is a function of the input, so PHVIT has
it). Plus, folded in from M3: the **confidence-weighted circular-hue loss** on dark pixels and the **dark-decile
hue/ΔE00 protocol** as a secondary contribution (no HVI paper reports it). Loss-side k0 frozen and detached (R2 §1b).
Loads w_perc; adds < 1 k params.
**Metric.** ΔE00 and |Δh|·S_gt in deciles 1–3 on val; darkness stress test (× 0.5, × 0.25 + Poisson–Gaussian) as
dose–response; global GT-mean PSNR must stay within ± 0.1 dB.
**Baselines to beat (from the check).** (b) global k + **RHVI-style intensity refinement** (1×1 + 5×5 DW conv on I,
equal parameters); (c) global k + **post-hoc luminance/HF chroma-suppression LUT** (gain(Y, |∇Y|) on HV before
decoding, 2–3 learned scalars — the ISP baseline); CAGE if code is available; BC-IHV's law re-implemented as a global
control; A2 (k = 0) and A0 from the ladder.
**Fast loop (the check's deciding experiment, ported).** Wave 1: (a) global k, (b) + IRM, (c) + LUT, (d) k(x) with
bound. **Go/no-go:** (d) beats both (b) and (c) by ≥ 0.5 ΔE00 or ≥ 2° hue in deciles 1–2 at equal global PSNR
(± 0.1 dB); confirmed later across 3 seeds. Otherwise drop or fold in as an ablation. Waves 2–3: σ calibration source,
bound constant c, predictor inputs, hue-loss weight.
**Novelty risk (one line).** Medium–low among the three: the per-pixel, noise-calibrated, bounded k(x) is unclaimed
and carries a provable statement; the risk is that the ISP LUT baseline (c) matches it.

## M3 — Chroma-confidence gating with a guided-filter chroma prior in the HV branch
**Locus + evidence.** As M2 (dark, low-saturation pixels); the HV branch's output is unreliable exactly where C_k is
small.
**Novelty check (`novelty/M3_chroma_confidence.md`): INCREMENTAL — the most crowded of the three.** "Gate the HV
branch by an intensity-derived confidence" is already colonised: CMIG-Net (arXiv 2608.01886, an explicit CIDNet
extension recalibrating chrominance conditioned on intensity), ICDNet (arXiv 2605.02627, intensity-aware chromaticity
gate on the input), TCA-Net (`wu2026tcanet`, confidence-thresholded I↔HV attention + chroma-leakage suppression),
WIRNet's gated LCA (NTIRE 2026), HAIMNet (`wang2026haimnet`), VCR (`cheng2026vcr`). Classic precedents to cite:
luma-guided chroma smoothing (joint bilateral / guided filter with Y as guide) and luminance-guided colour propagation.
**Component (the narrowly novel version).** Keep the confidence gate but make the low-confidence branch an explicit
**guided-filter / learned-propagation blend toward an intensity-anchored smoothed chroma prior**, paired with a
**confidence-weighted circular-hue loss** and the **dark-decile hue/ΔE00 + colour-noise-artefact-count protocol** —
no surveyed work confirms this triplet together.
**Baselines to beat.** CIDNet + CMIG-Net's recalibration and/or TCA-Net's thresholded cross-attention (re-implemented
or from released outputs), at matched global PSNR/SSIM; the M2 baselines (b)/(c) apply too.
**Fast loop (the check's deciding experiment, ported).** Zero-run first step: pull public CIDNet / CMIG-Net /
TCA-Net outputs if released, bin dark val pixels by decile, compute hue/ΔE00 per bin against a quick guided-filter-gated
CIDNet variant. **Go/no-go:** if CMIG-Net/TCA-Net already close most of the dark-decile gap without the fallback, M3
collapses to a re-parametrisation and is dropped. Otherwise wave 1: gate on/off × prior on/off × hue-loss on/off.
**Novelty risk (one line).** High: four 2026 works gate chroma by intensity inside this lineage; only the specific
triplet (prior fallback + matched loss + decile protocol) is unclaimed, and that is a thin margin.

## M4 — HVI-aware supervision: replace the meaningless VGG-on-HVI term and fix the range shift  *(no author check yet)*
**Locus + evidence.** `range_norm=True` maps x → (x+1)/2 before ImageNet normalisation (vgg_arch.py:228-231, CJ):
RGB is fed as [0.5, 1] and (H, V, I) get VGG features with no perceptual meaning (R2 §1d); never mentioned in the
paper. README: wo_perc 23.50 / 28.14 (GT-mean) vs w_perc 23.81 / 27.71 — the perceptual term lowers the GT-mean
number. Only non-RGB composite-loss precedent: U-Shape Transformer (`peng2023ushape`).
**Component.** Loss-only: VGG on correctly-ranged RGB only; on the HVI side a C_k-weighted chroma-structure loss
(SSIM on (H, V) weighted by C_k(I_gt)) and an explicit hue term. Zero parameters; the natural first wave of M1–M3.
**Metric.** LPIPS and ΔE00 (global and low-saturation pixels), GT-mean PSNR. **Baselines.** w_perc / wo_perc
fine-tuned identically, PAL, GT-mean loss, U-Shape's Lab/LCH loss, VCR's colour-distribution alignment.
**Fast loop.** Wave 1: {upstream loss, range fixed, VGG off HVI, both}. **Novelty risk.** Medium: a loss recombination
plus the documentation of an undocumented range shift; a chapter, not a headline.

## M5 — Repaired and symmetric LCA fusion  *(no author check yet)*
**Locus + evidence.** HV_LCA lacks the FFN residual; I_LCA5's output is overwritten (CIDNet.py:105, 109) so 70,960
parameters never get a gradient; stage 3 consumes pre-LCA2 features (:94-95) (CJ, phase0_related §1.2). No follow-up
fixes these; TCA-Net, HAIMNet, WIRNet replace the fusion instead. **Component.** Repair the three defects, then a gated
bidirectional LCA. **Metric.** Edge PSNR, PSNR in high-gradient regions, GT-mean PSNR. **Baselines.** Upstream;
TCA-Net, HAIMNet, WIRNet (reported). **Novelty risk.** High: bug fixes are not a method and gated LCA exists; the
measured size of the defects is the safe finding.

## Transfer-style candidates T1–T6 (author's novelty checks `ralph/related/novelty/T1–T6`, 2026-09-24)
Verdicts as written: **NOVEL-IN-HVI: T1, T3, T4, T6 (thin). INCREMENTAL: T2, T5.** None of the six checks states a
numeric go/no-go; the thresholds below are master's proposals and are marked as such.

### T1 — Hue-rotation-equivariant HV branch (+ hue augmentation + circular hue loss)  *(author's lean: primary)*
**Verdict:** NOVEL-IN-HVI. No paper combines rotation/steerable-equivariant convs with the HVI chroma branch; the
mechanism exists (CEConv, NeurIPS 2023, arXiv 2310.19368; "Learning Color Equivariant Representations", arXiv
2406.09588, which already identifies hue as the 2D rotation group in HSL; hypertoroidal covering, arXiv 2603.04256;
illuminant-equivariant nets for colour constancy, ECCV 2024) and the target problem is attacked non-equivariantly by
CAGE (arXiv 2608.10512, AdaLAB/AdaCCT) and HVD-Net (continuous hue encoding). HVI makes this exact: a global hue
rotation by Δh is a rigid rotation of the (H, V) vector field by 2πΔh, with I untouched.
**Locus.** Colour casts / white-balance shifts in low light: hue error and — the equivariance-specific quantity — the
*spread* of the output hue error across synthetic input rotations of the same scene; ΔE00 under simulated WB gains.
Measurable on val with zero new data: rotate val inputs by Δh ∈ {± 10°, ± 20°, ± 40°} and apply WB gains.
**Component.** Replace the first conv block(s) of the HV branch with a CEConv-style hue-rotation-equivariant lifting
conv over a discrete group H_n (n = 8–12) — where the cast is still a pure rotation, before any mixing with I — plus a
circular (von Mises / cosine) hue loss and hue-rotation augmentation. **Conceptual point the thesis must own:** an
equivariant branch maps a rotated input to a rotated output, so alone it *preserves* a cast; the correction comes from
pairing equivariant features with an **invariant global cast estimator** (group-pooled head predicting the rotation to
undo) — "equivariant features, invariant estimate, exact undo in HVI". Loads w_perc for every unchanged tensor; the
lifting layer starts fresh (≈ n × the first block's params).
**Baselines to beat.** (i) CIDNet fine-tuned identically **with hue-rotation augmentation and the circular loss but a
standard conv** — the fair control (augmentation alone may buy most of the robustness); (ii) CAGE's AdaCCT plug-in if
code is released, else reported; (iii) HVD-Net's continuous hue encoding (reported).
**Fast loop (the check's deciding experiment, ported).** Zero-run first: the released model's hue-error spread under
input rotations (the gap to close). Wave 1: {control, +aug+circular loss, +equivariant lifting, +lifting+cast head}.
**Go/no-go (master's proposal):** the equivariant variant cuts the hue-error spread across rotations by ≥ 50 % relative
to the augmented control at equal global PSNR (± 0.1 dB) and lowers hue error under WB casts by ≥ 2°; otherwise
"augmentation suffices" and T1 is dropped. Waves 2–3: group size n, which blocks are lifted, cast-head design.
**Novelty risk (one line).** Low–medium on mechanism (unclaimed in HVI), medium on outcome: hue augmentation alone is
the threat, and real casts are not pure rotations (they change S and I per channel), which bounds the exactness.

### T3 — Test-time adaptation of HVI-CIDNet's own knobs (k, α_s, α_i, γ, I-branch norm)  *(author's lean: extension)*
**Verdict:** NOVEL-IN-HVI as a component-wise assembly. Every block is taken (Zero-DCE non-reference losses;
Retinex-unrolling test-time fine-tuning, arXiv 2202.05972 — the closest mechanism; SALVE, arXiv 2212.11484; genetic
per-image gamma search, arXiv 2505.11246; few-parameter TTA for SR/open-set restoration, arXiv 2310.19011, 2312.02197),
but nobody adapts HVI-CIDNet's exposed inference knobs per image; upstream sets them as fixed CLI flags.
**Locus.** Brightness-shifted and out-of-distribution inputs: MILL's 26.4 → 17.7 dB collapse at a 20 % blend, NTIRE
2026 zero-shot 13.85 dB. **Zero training:** it is inference-time optimisation, so it fits "no runs" and any primary.
**Component.** Freeze the network; per image, 10–50 Adam steps on {k, α_s, α_i, γ, I-branch norm affine} (a few dozen
scalars) minimising a Zero-DCE-style non-reference loss (exposure control + colour constancy + spatial consistency,
optionally NIQE); ≈ 1–2 s/image on a 2080 Ti.
**Baselines to beat.** Frozen CIDNet at default knobs; the genetic gamma search (arXiv 2505.11246); the zero-parameter
mean-intensity normalise/invert wrapper (M1's baseline (c)).
**Deciding experiment (zero runs).** On val GT-blends α ∈ {0.1, 0.2, 0.35, 0.5} and gains {× 0.5, × 2, × 4} (MILL's 11
levels if downloaded): PSNR/ΔE recovery vs frozen, wall-clock per image, and the in-distribution regression.
**Go/no-go (master's proposal):** recover ≥ 1/3 of the 26.4 → 17.7 dB gap on the blended set at ≤ 2 s/image with an
in-distribution loss ≤ 0.2 dB; otherwise it is a footnote. **Risk (one line).** Non-reference losses drift toward
over-exposure and flat colour; the in-distribution guard is what keeps it honest.

### T2 — Heteroscedastic chroma-uncertainty head on the HV branch — **INCREMENTAL**
Kendall & Gal-style log-variance head + Gaussian/Laplacian NLL on chroma; closest UCAMNet (MMM 2026, HVI + variance-
guided intensity), GSAD (NeurIPS 2023), U2CLLIE (arXiv 2508.04176). Baseline: deterministic HV branch and UCAMNet. Loss +
tiny head, loop-fit; locus = darkest deciles (ΔE00, hue error, AUSE calibration). No threshold stated. Kept as an
optional add-on to M2 (same locus), not a primary.

### T4 — Learned loss weights for the dual-space objective — **NOVEL-IN-HVI (transplant)**
Uncertainty weighting (Kendall, Gal & Cipolla, CVPR 2018), GradNorm (ICML 2018) or DWA over the 2 spaces or all 8 terms;
baseline = upstream weights (1.0 / 0.5 / 50 / 0.01, issue #163). Loss-only, perfect loop fit — but its headline claim is
convergence speed, which fine-tuning from converged weights cannot show; the from-scratch 3-seed final would. Natural
companion to M4. Locus = the weights themselves; metric PSNR/LPIPS/SSIM + epochs-to-target.

### T5 — Illumination/SNR-gated LCA — **INCREMENTAL**
Attn = softmax(QKᵀ/√d ⊙ σ(W·I_map)) with a 1×1 gate; closest CMIG-Net (arXiv 2608.01886), TCA-Net, WIRNet, HAIMNet.
Baseline: plain LCA and CMIG-Net. Small module, loop-fit; would need Sony-Total-Dark for the check's protocol. Same
crowded neighbourhood as M3/M5 → low.

### T6 — HVI-space distillation into a small student (split I / HV losses) — **NOVEL-IN-HVI (thin)**
Teacher HVI-CIDNet+ or an ensemble; closest MirrorDistill (arXiv 2609.25331; LOL-v2-Real 24.08 dB at 4.38 GMACs),
DLIENet (PR 2025). Student is width-reduced, so released weights do not load; teacher inference first. Efficiency
thesis, weak tie to a failure locus → low.

## Ranking (locus measurability × fit to the 25-min loop × chance to beat the named baselines × novelty margin)

| # | Candidate | Locus metric instrumented? | Loop fit | Novelty verdict (author's checks) | Score |
|---|---|---|---|---|---|
| 1 | **T1 hue-equivariant HV branch + invariant cast estimator** (+ T3 as the brightness-shift extension) | yes, zero new data (synthetic rotations / WB gains on val) | very good (lifting layer new, rest loads w_perc) | NOVEL-IN-HVI | ★★★★★ |
| 2 | **M2 noise-calibrated per-pixel k(x) with bound** (+ M3 hue loss, decile protocol) | yes | excellent | INCREMENTAL, unclaimed slice with a provable bound | ★★★★ |
| 3 | T3 test-time knob adaptation | partly (blends/gains on val; MILL data optional) | zero training | NOVEL-IN-HVI (assembly) | ★★★★ (as extension) |
| 4 | M1 exposure-conditioned HVI parameters | partly | very good | INCREMENTAL | ★★★ |
| 5 | T4 learned loss weights / M4 HVI-aware supervision | yes | perfect (loss-only) | NOVEL-IN-HVI (transplant) / — | ★★★ (chapter) |
| 6 | M3, T2, T5 (chroma gating / uncertainty / gated LCA) | yes | good | INCREMENTAL, crowded | ★★ |
| 7 | T6 distillation, M5 repaired LCA | partly | mixed | thin / low | ★★ |

**Recommendation (v8): T1 as the thesis method, T3 as its zero-training extension** — together "HVI-CIDNet robust to
photometric shift: equivariant chroma under hue casts, adapted intensity knobs under brightness shift", two loci that
are both measurable on the validation split with no new data. **Pivot: M2** if T1's wave 1 shows augmentation alone
closes the hue-error spread (the stated go/no-go), since M2 shares the fine-tune loop and the decile protocol. M4/T4
loss work is wave 1 of either. The C1 ladder (fine-tune mode) is the ablation chapter. Budget after Gate 0 unchanged:
≈ 3 loop rounds (≈ 6 h wall-clock), T3 zero-run sweeps on saved fine-tunes, then 9 from-scratch runs for the final table
(≈ 18 h wall-clock) + the ladder in fine-tune mode.

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
