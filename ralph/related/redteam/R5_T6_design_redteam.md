# R5 — Red-team of T6 "HVI-space distillation" (CIDNet → width-reduced CIDNet)

## Verdict
1. As written, the headline claim ("student is within 0.3 dB of the teacher at ~3x fewer FLOPs") is probably true without distillation. The teacher is only 1.9M params, LOL-v1 is tiny, and 15 test images plus seed noise are about the size of the effect. So the KD contribution can't be identified.
2. The likely null has a cause: the teacher was trained on the same 485 pairs, so its outputs on training inputs are close to GT and carry little extra information. KD only has a real chance with a transfer set the teacher did not fit (extra or unlabeled low-light inputs, strong augmentation) and/or a strictly stronger teacher (HVI-CIDNet+, whose LOL-v1 weights are released, or a CIDNet+Retinexformer average).
3. The design is salvageable as a small, careful thesis if the claim becomes "where on the width/FLOPs Pareto curve, and from which transfer data, does HVI-component KD beat from-scratch and pruning baselines". The intensity/chroma split has to be tested as a 2x2 factorial with component-specific error metrics, not asserted from branch names.

Facts checked (web, 2026-09-24):
- **HVI-CIDNet+ code and weights** are released in a separate repo, github.com/shikangbiao/CIDNet_extension, with Google Drive weights for LOL-v1, v2-real/syn, SICE and others. The repo bundles `open_clip`, so it uses CLIP-type priors. I did not verify its LOL-v1 number or its params/FLOPs.
- **FusionNet** (NTIRE 2025 winner; ESDNet + Retinexformer + CIDNet with linear fusion) reports 13.54M params, 50.29 GFLOPs and 25.17 dB raw on LOL-v1. The HVI-CIDNet README says FusionNet weights are not in that repo, and I could not confirm public LOL-v1 FusionNet weights.
- **NTIRE 2026 E-LLIE** (arXiv 2605.02212):
  - Data: 3024x4032 smartphone images, 349 train / 49 val / 102 test pairs, test GT withheld. The budget is ~1M params.
  - Ranking: aggregated rank over SSIM, LPIPS, DISTS, LIQE, MUSIQ and Q-Align. PSNR is not part of it, and ties are broken by params.
  - HVI entries: Efficient-HVI (957k params, rank 5), sysu_701 (965k, rank 12, U-Net cut from 5 to 4 levels with compressed channels), Cidaut (797k, rank 17, NAFBlock-based NIEL).
  - Distillation: I found no mention of KD in the report, which matches the premise.

---

## Item-by-item: Attack / Consequence / Fix

### (1) Is "small student ≈ teacher" trivially true or false? What does the width curve look like?

**Attack.**
- **Parameter and FLOP counts.** CIDNet's convolution and attention parameters scale roughly with C². At 36→24 channels params fall to ~0.85M and FLOPs by ~2.25x. At 36→18, params fall to ~0.47M and FLOPs by ~4x. "3x fewer FLOPs" therefore means about 20–21 channels.
- **Expected curve.** On LOL-v1 (485 train / 15 test, mostly indoor, heavy exposure ambiguity), I expect the from-scratch width-vs-PSNR curve to be almost flat between 36 and ~18 channels on GT-mean PSNR (a drop of ≤0.3–0.5 dB). It should then bend at ~12 channels (~0.2M) and fall steeply below that.
- **Raw PSNR.** Raw PSNR is dominated by global-exposure error. It swings by ~0.5–1 dB across seeds and epochs for the same model, so raw PSNR shows no clean curve at all.
- **Sub-1M HVI nets do fine.** The NTIRE-2026 efficient HVI entries (0.8–0.97M) are competitive, which is further evidence that half-width CIDNet is not capacity-starved.
- **Teacher number is test-selected.** The released teacher's 23.8 raw / 27.7 GT-mean was obtained by the original repo's practice of evaluating on the test set during training and keeping the best epoch. A student selected on a validation split will look ~0.3–0.8 dB worse from selection bias alone.

**Consequence.**
- "Within 0.3 dB of the teacher" is then either trivially met by a scratch student (the KD contribution is moot) or trivially failed (a selection artifact).
- The teacher–student gap that KD could close is probably ≤0.5 dB GT-mean at 18–24 channels. That is inside the noise of 15 images and 3 seeds.

**Fix.**
- **Run the width sweep first (Week 1).** Train from scratch at {12, 18, 24, 36} channels on the full schedule with ≥2 seeds and validation-based checkpoint selection. Also re-run the teacher (36 channels) under the same protocol, or at minimum re-score the released weights with the same fixed-epoch rule.
- **Choose the student width from the curve.** Use the width where the scratch gap to the teacher is ≥0.7 dB GT-mean. That is likely 12 channels, or 18 channels with depth also cut (as sysu_701 did, 4 levels instead of 5).
- **Define gap and headroom.** Gap = teacher − scratch, and KD headroom is that gap. Report the fraction of the gap that KD recovers rather than a single "within X dB" number.

### (2) Stronger-teacher availability; is same-architecture (self-)distillation meaningful?

**Attack.**
- **Same-architecture teacher.** With the released CIDNet as teacher, this is compression KD with a ~2–4x capacity ratio and identical inductive bias. Its knowledge on the training inputs is almost the labels.
  - On 485 pairs a 1.9M-param net is well fit. I expect its outputs on train images to be ~30+ dB to GT (measure this).
  - Output KD on those inputs therefore approximates "supervised loss with slightly smoothed labels". Dark knowledge in regression consists of the teacher's residual error structure, and on train data that residual is small.
- **HVI-CIDNet+.**
  - Weights exist (see above), but it uses vision-language priors (a CLIP-type encoder plus Prior-guided Attention Blocks).
  - Its feature maps don't align one-to-one with a pure CIDNet student. Output-level HVI KD still works.
  - Its LOL-v1 advantage over CIDNet under a common protocol is unverified.
  - Teacher inference cost during training is fine on a 2080 Ti.
- **FusionNet.** LOL-v1 weights are not confirmed. It is also an sRGB-fused output, so it has no HVI features.

**Consequence.**
- With the same-architecture teacher and LOL-v1-only inputs, expect KD − scratch ≈ 0–0.2 dB.
- "Self-distillation"-style gains (born-again networks) are documented mainly for classification. For pixel regression with near-GT teacher outputs, the prior is weak.

**Fix.**
- **Use three teachers, compared on the same protocol:**
  - T1: CIDNet, same architecture.
  - T2: HVI-CIDNet+ (released LOL-v1 weights). Use output KD in HVI space, plus I/HV features only if its branch structure is kept.
  - T3: a cheap home-made ensemble, the pixel average (or a least-squares linear fusion fitted on train) of the released CIDNet and Retinexformer LOL-v1 weights. This is the FusionNet idea without needing FusionNet weights.
  - Keep a teacher only if it beats T1 by ≥0.5 dB GT-mean on validation.
- **Add a transfer set the teacher did not fit.** Candidates: LOL-v2-real/syn training lows (unlabeled use), SICE under-exposed images, the unpaired sets (DICM, LIME, MEF, NPE, VV), and heavy augmentation of LOL-v1 lows (random gamma or exposure scaling, crops, noise). Distill on these as well: "function matching" with consistent augmentation between teacher and student.
  - This is the single change most likely to make KD beat scratch.
  - It has to be controlled with the same extra inputs used without the teacher (arm A9c below).

### (3) Does the intensity-vs-chroma split make sense given cross-attention? Making it falsifiable

**Attack.**
- **Features are entangled.** The LCA cross-attention blocks exchange information between the I and HV branches at every scale. I-branch features encode chroma context and vice versa, so "I-branch feature KD = intensity knowledge" is a naming assumption.
- **The output split is cleaner.** CIDNet's final outputs are an I-map and an HV-map, recombined by the inverse HVI transform.
- **The HVI transform is not fixed.**
  - CIDNet's HVI transform has a learnable collapse parameter (density_k, in C_k(I) = (sin(πI/2)+ε)^(1/k)). The teacher's HVI space and a freshly trained student's HVI space differ, so HVI-space targets aren't comparable unless k is shared.
  - C_k(I)→0 at dark pixels, so HV magnitudes and HV losses are inherently near zero exactly where "darkness weighting" puts weight. The two effects interact.

**Consequence.**
- Any claim like "chroma knowledge transfers more" can't be falsified if it rests on branch-feature losses alone.
- It could also be an artifact of loss scale: the I and HV terms have different natural magnitudes.

**Fix.**
- **Fix the transform.** Freeze the student's k to the teacher's learned value, or compute all KD targets with a fixed, shared HVI transform.
- **Run a 2x2 factorial at output level:** {I-KD off/on} × {HV-KD off/on}.
  - Balance each term by gradient norm (or normalise each by its teacher-vs-GT loss on train) so that "which term" is not "which weight".
- **Measure component-specific errors on the test set:**
  - Intensity error: L1 on I = max(RGB), PSNR on I, and raw-minus-GT-mean PSNR, i.e. how much of the error is global exposure.
  - Chroma error: ΔE on the CIELAB a*b* channels only, or HV-L1 restricted to I>τ.
- **Pre-registered prediction.** I-KD should reduce intensity error (and raw PSNR more than GT-mean PSNR) with no effect on chroma error, and HV-KD the reverse.
  - The split is refuted if both terms move both error types equally, or if the interaction is as large as the main effects.
- **Control for an arbitrary split.** Split the teacher's output channels (or features) in a way unrelated to I/HV, for example a random orthogonal mix of the 3 HVI channels, and apply the same two-term KD. If this does as well, the HVI split adds nothing.
- **Feature level.** Run feature-level branch KD only as a secondary experiment, and report CKA between the I- and HV-branch features at each level to quantify the entanglement.

### (4) Baselines that must be beaten

**Attack.**
- **From-scratch baseline.** The only fair comparison is a from-scratch student with the identical schedule and selection rule, on both the short and the full schedule.
- **Plain RGB output KD.** Without it, "HVI space" can't be credited.
- **Initialisation confound.** "Fine-tune from width-pruned weights" mixes the init effect with the KD effect: pruning plus fine-tuning is itself a compression baseline.
- **Precision baselines.** FP16 or INT8 of the full teacher often beats a width-halved FP32 student on real latency on a 2080 Ti, which has FP16 tensor cores.
- **NTIRE-2026 entries aren't comparable.**
  - Different data (smartphone 3024x4032, 349 train pairs).
  - Different metrics (the ranking uses SSIM, LPIPS, DISTS, NR-IQA and Q-Align, not PSNR).
  - Hidden test GT.
  - Their LOL-v1 numbers mostly don't exist.

**Consequence.** Without these baselines a reviewer attributes any gain to init, schedule or color space rather than to distillation, and dismisses the efficiency claim.

**Fix.** Required baselines, matched width, schedule and selection rule:
- B1: scratch.
- B2: pruned-init plus supervised fine-tuning (structured L1 channel pruning of the teacher down to the student width).
- B3: RGB output KD.
- B4: HVI output KD without the split (single loss).
- B5: the teacher in FP16, and INT8 post-training quantisation via TensorRT or torch.ao if it works, reported for PSNR and latency.
- B6: published lightweight LOL-v1 numbers, re-run where code exists. Retinexformer (1.61M params, 15.57 GFLOPs, 25.16 dB, test-selected) is a sanity anchor.

For NTIRE-2026:
- Either treat it as related work only.
- Or, if the E-LLIE train/val data is downloadable, add a secondary evaluation on its 49-pair validation set under the ≤1M-param budget. Report SSIM and LPIPS there. Retrain Efficient-HVI or sysu_701 only if their code is public; otherwise cite them with an explicit "not comparable" note.

### (5) Fast-loop validity

**Attack.**
- **Short schedules favour KD.** The teacher gives dense, smooth, already-consistent targets, which speed up convergence. Fine-tuning from pruned teacher weights starts the student next to the teacher's function.
- **At full schedule.** Scratch catches up, so the ranking "KD > scratch" found in minutes can shrink to zero or flip.
- **Precomputing teacher outputs/features breaks things:**
  - It blocks random crops, flips and gamma augmentation unless features are cropped with multiple-of-16 alignment through the U-Net down-sampling.
  - It blocks the transfer-set fix from item (2).
  - Storage: a full-res level-0 feature map at 600x400x36 in FP16 is ~17MB per image per map, so tens of GB.
  - Online teacher inference of a 1.9M net in FP16 costs little compared with the student backward pass.

**Consequence.** The screening results mainly measure convergence speed, and the thesis would report a short-schedule artifact.

**Fix.**
- **Screen, then confirm.** Use the fast loop only to screen, with 2 seeds at ~20% of the schedule. Confirm every arm that enters the main table at the full default CIDNet schedule, from scratch and from pruned init. Time one epoch first and budget ~4–8 GPU-h per run (estimate).
- **Plot learning curves.** Show validation PSNR vs epoch for scratch and KD on the same axes. "KD accelerates but doesn't raise the asymptote" is itself a reportable finding.
- **Run the teacher online** in eval mode, FP16 under no_grad.

### (6) Is "performance at a specific params/FLOPs budget" a strong enough contribution? What would a CVPR reviewer say?

**Attack.** A CVPR reviewer would likely raise four points:
- "Incremental: standard KD applied to an existing architecture; KD for LLIE already exists (MirrorDistill, DLIENet, 2022 KD-LLIE)."
- "Single tiny dataset; gains within noise; no latency; not compared to NTIRE efficient methods; the HVI split is not shown to matter versus RGB KD."
- A single operating point (one width) makes a weak claim.

For a bachelor thesis the bar is lower. It is fine if the study is clean, pre-registered, and reports a null honestly.

**Consequence.** The contribution is weak as a method paper and adequate as a well-controlled empirical study, and only if the questions are sharper.

**Fix.** Recast the contribution as three questions:
- **Pareto.** Does HVI-KD shift the PSNR-vs-{params, FLOPs, measured latency} frontier across widths {12, 18, 24} (not one point) relative to scratch and pruning?
- **Source of gain.** Is it the teacher, the transfer data, or the color space? Arms A5 vs A4, A9 vs A9c, and A10.
- **Component transfer.** Does intensity or chroma knowledge transfer? Use the factorial from item (3), with component-specific metrics.

Evaluate on LOL-v1 plus LOL-v2-real (and v2-syn if time allows) so that the claim isn't resting on 15 images. A negative answer to Q1, together with a positive or mechanistic answer to Q2 or Q3, is still a thesis.

### (7) Statistics: seeds, scene overlap, GT-mean, latency

**Attack.**
- **Power.** 3 seeds × 15 test images gives low power for a 0.3 dB effect when the seed SD of CIDNet-style training on LOL-v1 is probably ~0.2–0.5 dB (raw is worse).
- **Scene overlap.** LOL-v1 contains near-duplicate indoor scenes and repeated setups. A random validation split taken from train leaks scenes.
- **GT-mean erases the most likely KD effect.** GT-mean rescales output brightness to GT and so removes global exposure error. If KD mainly transfers the teacher's exposure calibration (intensity knowledge), the effect shows in raw PSNR and vanishes in GT-mean.
- **Latency.**
  - At 600x400 a 0.5–1M-param net on a 2080 Ti is launch- and memory-bound, so 3x fewer FLOPs may give only ~1.2–1.6x lower latency.
  - FLOP counters (thop, ptflops) often miss matmul and attention ops or count them inconsistently.

**Consequence.**
- The main comparison may be underpowered.
- Validation-based selection may be optimistic.
- Raw vs GT-mean disagreements will be misread.
- The efficiency claim may not hold up on measured latency.

**Fix.**
- **Seeds and testing.** Use 5 seeds for the main pairwise comparison (KD vs scratch at the chosen width); 3 seeds are fine for secondary arms. Use a paired test over images × seeds, either a hierarchical bootstrap (resample seeds, then images) or a mixed model. Report mean ± SD and the 95% CI of the paired difference.
- **Pre-register the thresholds:** Δ = 0.3 dB and the metric (raw PSNR primary, GT-mean secondary, plus SSIM and LPIPS).
- **Leak-free validation split.** Build scene-disjoint validation by clustering the training GTs (perceptual hash or DINO/CLIP embedding plus agglomerative clustering) and holding out whole clusters (~50 images). Select checkpoints on validation only (fixed rule: best validation, or last-N average) and evaluate on test once.
- **Report raw and GT-mean side by side, plus the exposure gap.** The exposure gap = GT-mean PSNR − raw PSNR, i.e. how much error is pure global brightness. Interpret it through the split hypothesis: I-KD should shrink the gap.
- **Latency protocol.**
  - Setup: batch 1; LOL resolution 600x400 and 1920x1080; FP32 and FP16; `cudnn.benchmark=True`; ≥50 warm-up runs; `torch.cuda.synchronize()`.
  - Timing: median and p90 over ≥300 runs, with the HVI transform and its inverse included, and peak memory reported.
  - FLOPs: a single tool that counts matmuls (fvcore or a manual count for attention), stated explicitly.
  - Also report CPU single-thread latency if you want a deployment angle.

---

## Revised design

Default student width W* is chosen from A1, where the scratch gap to the teacher is ≥0.7 dB GT-mean (likely 12–18 channels). KD arms run at W*; the Pareto sweep repeats the key arms at 3 widths. GPU-h figures are estimates, to be recalibrated after timing one epoch. The screening pass costs ~20% of full.

| Arm | What it is | Isolates | Cost (2080 Ti) |
|---|---|---|---|
| A0 | Teacher CIDNet-36 re-trained (or released weights re-scored) under the val-selection protocol; train-set PSNR of the teacher's outputs | True teacher score; how label-like the teacher is on train (predicts KD headroom) | 2 seeds × ~8h, or ~0h if re-scoring only |
| A1 | Scratch width sweep {12, 18, 24, 36}, full schedule | Capacity curve, and whether any KD headroom exists | 4 widths × 2 seeds × ~5h ≈ 40 GPU-h |
| A2 (B1) | Scratch at W* | Primary baseline | 5 seeds × ~5h |
| A3 (B2) | Pruned-init + supervised fine-tune at W* | Init effect vs KD | 3 seeds × ~3h |
| A4 (B3) | RGB output KD (T1) | Plain KD | 3 seeds |
| A5 (B4) | HVI output KD, single loss, shared frozen k (T1) | Color space of the KD loss (vs A4) | 3 seeds |
| A6/A7 | HVI output KD, I-only / HV-only; gradient-norm balanced; A5 is the both-on cell of the 2x2 | Component transfer (intensity vs chroma), measured with I-error, ΔE-chroma and the exposure gap | 2 × 3 seeds |
| A6r | Random-mix "split" control (two-term KD on non-I/HV channel mixes) | Whether the HVI split matters beyond having two terms | 3 seeds |
| A8 | Feature KD (1x1 adapters, per level), all / I-branch / HV-branch; CKA report | Feature-level transfer and entanglement (secondary) | 3 × 2 seeds |
| A9 | Best KD loss + transfer set (LOL-v2 lows, SICE-under, unpaired sets, gamma/exposure aug), teacher online | Transfer-data effect | 5 seeds × ~8h |
| A9c | Same extra inputs with no teacher (augmentation only / self-training from the student's own EMA) | Separates "more inputs" from "teacher signal" | 3 seeds |
| A10 | Stronger teacher: T2 HVI-CIDNet+ (output KD) and/or T3 CIDNet+Retinexformer average | Teacher-quality effect (enter only if ≥0.5 dB better than T1 on val) | ~0.5 day setup + 3 seeds |
| A11 (B5) | Teacher FP16; INT8 PTQ if feasible | Whether quantisation beats KD on the latency Pareto | ~2h |
| A12 | Darkness-weighted vs uniform KD (on the best arm) | Whether the weighting matters (and its interaction with C_k collapse) | 3 seeds |
| P | Repeat A2, A3, best KD (and A9) at widths {12, 18, 24} | Pareto shift vs one point | ~3 × 3 × 3 × 5h ≈ 135 GPU-h |
| X | Secondary eval: LOL-v2-real (train and test there for A2 / best KD); optional NTIRE-26 E-LLIE val under ≤1M | Generalisation beyond 15 images | ~40 GPU-h |

Total ≈ 350–450 GPU-h ≈ 4–5 days wall-clock on 4× 2080 Ti at full schedule, plus screening. Run screening at 20% schedule on 2 seeds first, then promote at most 4 KD arms to full.

---

## Kill criteria (pre-registered)

- **K1 (no headroom).** In A1, if the scratch student at 18 channels is within 0.3 dB (GT-mean, val) of the A0 teacher, move to W*=12. If even at 12 channels the gap is <0.5 dB, drop the "KD closes the gap" framing and pivot to the Pareto/compression study with pruning and quantisation as the main arms.
- **K2 (label-like teacher).** If teacher outputs on LOL-v1 train are ≥30 dB PSNR to GT, do not run train-only output KD as a main claim. Only A9 (transfer set) and A10 (stronger teacher) remain as the KD hypothesis.
- **K3 (full-schedule null).** If at the full schedule the best KD arm − A2 is <0.15 dB (val, 2-seed pilot) and A9 − A9c is <0.15 dB, stop adding KD variants and write the negative result with the learning-curve analysis.
- **K4 (split not identifiable).** If the component-specific error changes from A6 and A7 differ by less than 1 seed-SD, or A6r matches A5, drop the "which knowledge transfers" claim.
- **K5 (efficiency claim).** If the FP16 teacher's latency is ≤ the FP32 student's at 600x400 and 1080p, the efficiency claim must be stated as params/FLOPs only, or compared FP16-to-FP16. Do not claim a deployment speedup.
- **K6 (teacher).** Drop T2/T3 if they are not ≥0.5 dB (GT-mean, val) better than T1 under the common protocol, or if T2 cannot be run offline within a day.

---

## Probability estimate

**P(distilled student beats the equal-size from-scratch student by >0.3 dB PSNR on LOL-v1 test, mean over 3 seeds, full schedule, validation-selected checkpoints) ≈ 0.20** for the proposal as written (same-architecture CIDNet teacher, LOL-v1-only inputs, ~0.5–0.9M student).

- ~0.45 if measured at the short fast-loop schedule, because convergence speed inflates it.
- ~0.30–0.35 with a transfer set (A9) and/or a verified stronger teacher at W* ≈ 12–18 channels.
- ≤0.15 on GT-mean PSNR, since that metric removes the exposure calibration KD most plausibly transfers.
- The raw-PSNR estimate also includes a sizeable chance of a >0.3 dB "win" that is noise. Hence 5 seeds and a paired CI for the main comparison.
