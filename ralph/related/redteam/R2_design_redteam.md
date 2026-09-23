# R2 - Red-team of C1 (colour-space swap in HVI-CIDNet)

## Verdict

1. C1 is not worth running as designed. "Swap the colour space" changes four things at once: the branch split, the auxiliary-loss space, learnable k, and the residual space. With n=3 seeds, a permutation test can never reach two-sided p<0.05, and the per-image paired tests are pseudo-replication. Any outcome would be uninterpretable or would repeat the paper's own single-run ablation (sRGB 27.26 / HSV 25.86 / HVI ~28.1 GT-mean, LOLv1).
2. What must change: hold the loss fixed in every arm (L_rgb plus a frozen-k HVI loss with no VGG term). Replace the space list with a nested ladder of single-factor steps (HVI -> fixed-k -> k=0 -> YCbCr -> RGB). Use 5 matched seeds. Make the final cosine-schedule checkpoint the primary result (val-selected is secondary, and the logged test-oracle checkpoint gives C2 at no cost). Pre-register GT-mean PSNR as the primary metric with a seed-level test and a TOST equivalence margin.
3. Add the free per-intensity-bin and near-black hue-error analysis on the saved outputs. That turns "HVI wins by x dB" into a mechanism result: where in the intensity range the gain comes from, and whether C_k is the cause.

---

## 1. Confounds in "swapping the colour space"

### 1a. The 1-channel / 2-channel branch split
- **Attack.** The architecture hard-codes one "intensity" channel for the I-branch and two "chroma" channels as the HV-branch output. HVI, HSV and YCbCr each have a natural choice (I=max, V=max, Y=luma). sRGB has none. Any 1+2 split of RGB is either arbitrary (G alone, R+B) or is a colour transform in its own right (luma plus opponent channels = YCbCr). HSV's natural chroma pair is (H, S) with H circular. Predicting H as a scalar under L1 puts a discontinuity at the red wrap (0 <-> 1), and that is exactly the "red noise" the paper uses to motivate HVI. Also, I=max and Y=luma differ: max is non-smooth, and it saturates on coloured highlights.
- **Consequence.** Each arm turns into a different architecture or output parametrisation. "sRGB vs HVI" then measures "no luma/chroma split vs split". "HSV vs HVI" measures "hue wrap-around vs none", which is known and predictable. None of these contrasts isolates the colour space.
- **Fix.** Never have a split-less sRGB arm inside the two-branch net. Build a nested ladder where each step changes one thing:
  HVI(learned k) -> HVI(fixed k) -> HVI(k=0 = Cartesian HSV: S·cos, S·sin, I=max) -> YCbCr-max (I=max, chroma = linear Cb,Cr) -> YCbCr (I=Y).
  Drop HSV-polar. It is a strawman with a known failure mode, the paper already ran it, and it only shows that hue wrap is bad. If an "sRGB" reference is required, run it as a separate architecture: I-branch gets Y, the HV-branch gets RGB and outputs a 3-channel RGB residual, and it is reported as a different model, never as a point on the colour-space axis.

### 1b. What L_hvi becomes in the non-HVI arms
- **Attack.** There are three options, and each tests a different hypothesis. (i) Compute the loss in each arm's own space: representation and loss change together, and the loss scale changes too (Cb,Cr lie in [-0.5, 0.5], H,V in [-1, 1], hue in [0, 1] with wrap), so the effective loss weights differ per arm. (ii) Drop it: the HVI arm keeps two loss terms and the others keep one, so the HVI arm gets roughly twice the L1+SSIM+edge gradient. (iii) Keep it in HVI: this gives a clean representation-only test. However, if the HVIT inside the loss uses the model's learnable k and gradients flow through it, the network can shrink L_hvi by raising k. C_k = (sin(πI/2)+ε)^k ≤ 1, so a larger k shrinks the chroma magnitudes and the chroma error with them. That is loss-scale hacking, not better output.
- **Consequence.** With option (i), a win cannot be attributed to the representation. With option (ii), it is a loss-capacity confound. With option (iii) and an undetached k, k's final value is partly an artefact of the loss.
- **Fix.** Use option (iii) with a frozen loss transform. L = L_rgb + L_hvi(HVIT_k0), where k0 is a constant and no gradient reaches k through the loss, and the HVI arm uses the same constant. Every arm then optimises the same objective, and only the working representation changes. Check in code whether upstream detaches k in the loss. If it does not, add one diagnostic run with the upstream coupled loss to show how much k drifts. For the loss factor, add at most one extra arm, HVI rep + L_rgb only, which measures how much of the gain is the auxiliary loss.

### 1c. Learnable k and the global residual exist only in HVI
- **Attack.** The HVI arm has an extra learnable scalar and an intensity-dependent gain. The residual "out = f(x) + x" is taken in the working space, and a residual in max/polar-chroma coordinates is a different inductive bias from a residual in RGB.
- **Consequence.** An HVI win could come from k (adaptive near-black compression) and not from the space. A k that never moves off its initial value would make "learned" meaningless.
- **Fix.** Give every arm the residual in its own working space; that is part of what "working in space X" means, so it stays. Separate k with two arms: fixed k (frozen at A0's converged value, or at init if k barely moves) and k=0. Log k every epoch in A0 at no cost. If |k_final − k_init| < 0.05, merge the learned-k and fixed-k arms and say so.

### 1d. VGG perceptual loss on H,V,I tensors
- **Attack.** ImageNet VGG normalised with RGB mean and std, applied to (H, V, I) in [-1, 1], gives features without perceptual meaning. In option (i) it becomes a different arbitrary regulariser in every arm.
- **Consequence.** A small but uncontrolled per-arm difference in the objective (weight 0.01, but VGG feature magnitudes are large).
- **Fix.** Remove the VGG term from the second-space loss in all arms. Keep VGG only on RGB. The edge and SSIM terms stay because they are defined on any tensor, but they are computed in the same frozen HVI in every arm.

### Cleanest set of contrasts
A full factorial (space × split × k × loss × residual) is 30+ cells and too big. A nested ladder of five representation arms under one fixed loss, plus one loss arm, identifies each factor as the difference between neighbouring arms (see the revised design table).

---

## 2. Triviality risk

- **Attack.** YCbCr is an affine, invertible 3×3 map of RGB. Inside the 3-channel branch the first conv absorbs it exactly. What remains differs only in three ways: (1) what the 1-channel branch sees, (2) the output parametrisation plus residual, (3) optimiser geometry (Adam is not rotation-invariant, and per-coordinate scales change). HSV-polar has a discontinuity at the hue wrap. HVI with k=0 is ill-conditioned near black: S = (max−min)/max is pure noise when max ≈ 0. C_k exists to suppress exactly that.
- **Predicted outcomes (GT-mean PSNR, LOLv1, relative to A0 = HVI learned k):**
  - fixed k: |Δ| < 0.15 dB, uninformative in PSNR unless k moves a lot.
  - k=0 (Cartesian HSV): −0.2 to −0.6 dB, concentrated in the lowest intensity decile and in hue error on dark pixels. **Informative.**
  - YCbCr-max vs k=0: small, ±0.3 dB. Tests "nonlinear max/saturation chroma vs linear opponent chroma". **Informative either way.**
  - YCbCr (Y) vs YCbCr-max: tests the intensity definition. Likely shifts raw PSNR (exposure) more than GT-mean PSNR.
  - RGB-reference (split-less): ≈ YCbCr within seed noise. **Predictable, uninformative about the colour space.** Keep only as a sanity anchor, if at all.
  - HSV-polar: −1 to −2.5 dB with visible red/black artefacts. **Predictable and already published.** Drop.
- **Consequence.** In C1 as proposed, at most 1–2 of the 4 contrasts carry new information, and with n=3 they would come out as "n.s." anyway.
- **Fix.** Spend the runs on the arms marked informative. State these predictions in the pre-registration. A confirmed prediction then counts as evidence for the mechanism, not as "HVI wins".

---

## 3. Statistical power

- **Attack 1 (n=3).** For a two-sample t-test (α=0.05 two-sided, power 0.8, df=4), the minimum detectable effect is about 3.0–3.3 σ_seed: 0.6–1.3 dB for σ = 0.2–0.4 dB. That exceeds every plausible effect except HSV-polar. An exact permutation test with 3 vs 3 has 20 splits, so the smallest two-sided p is 0.10. **It cannot reject at 0.05.**
- **Attack 2 (per-image tests).** A Wilcoxon over the 15 test images from one checkpoint pair treats images as the replication unit, while the claim is about training procedures. Two seeds of the same arm will often differ "significantly" per image. Run seed 1 vs seed 2 of A0 as a negative control; I expect it to fail. This is pseudo-replication. It also generalises only to these 15 images from one camera setup.
- **Attack 3 (the null claim).** "Changes PSNR by less than the seed spread" is a failure to reject, so with n=3 it is almost guaranteed to be found. It is not evidence of equivalence.
- **Consequence.** 15 runs could produce "HVI better, n.s." or "no difference", and neither result could be defended.
- **Fix.**
  - **5 seeds, matched across arms.** Seed s fixes data order, crops, flips and the init of every layer whose shape is identical across arms. That allows a paired-by-seed analysis: Δ_s = PSNR(A0, s) − PSNR(Ax, s), a one-sample t-test with df=4, and an exact sign-flip permutation test over the 2^5 = 32 flip patterns (smallest two-sided p = 1/16 = 0.0625). The t-test is therefore primary and the permutation test is a robustness check. Pairing removes shared seed variance; if the correlation between arms is ρ≈0.5, σ_Δ ≈ σ_seed. The paired MDE is (t_.975,4 + t_.8,4)/√5 · σ_Δ ≈ 1.66·σ_Δ, or about 0.4–0.7 dB for σ_Δ = 0.25–0.4. That is realistic for C_k effects only if they are ≥0.4 dB, so the per-bin analysis (§5) is where the sensitivity comes from.
  - Model the per-image level with a mixed model: PSNR_{a,s,i} ~ arm + (1|image) + (1|seed) + (1|seed:arm). Inference on arm uses seed-level degrees of freedom. Report the image-level ICC.
  - 5 seeds × 5–6 arms beats 3 seeds × 5 arms. The two strawman arms (HSV-polar, split-less sRGB) are the ones to cut.
  - Measure σ_seed from the first 5 A0 seeds before launching the other arms. If σ_Δ > 0.4 dB, go to 8 seeds on A0 / k=0 / YCbCr-max only.

---

## 4. Protocol validity

### 4a. The validation split and scene overlap
- **Attack.** LOL-v1 pairs are multiple exposures and near-duplicate framings of a limited set of scenes. A random val subset shares scenes with the training set (and likely the test set does too). Val PSNR is then inflated and rewards memorisation, which biases selection toward late, overfit epochs. Removing about 40 pairs also shrinks the training set by about 8%.
- **Fix.** Cluster all 500 images (485 train + 15 test) by scene with DINOv2 or CLIP embeddings plus pHash on the GT. Make val = about 40 pairs from clusters that contain no test image and no remaining training image. Report how many test images have a train-set near-duplicate (cosine > 0.9); that is a caveat that belongs in the thesis. The smaller training set is matched across arms, so it is acceptable. Do not retrain on the full 485 afterwards.

### 4b. Checkpoint selection, and C2 at no extra cost
- **Attack.** Selecting on test is the upstream flaw. Selecting on a noisy 40-image val set adds its own variance.
- **Fix.** Pre-register three read-outs per run:
  - **Primary:** the final checkpoint at epoch 1000. The cosine schedule ends at LR≈0, so this is a natural, selection-free point.
  - **Secondary:** the best val-PSNR checkpoint.
  - **Oracle (logged, never used for claims):** test PSNR every 10 epochs, written to a separate file by a frozen script.
  
  C2 selection bias = oracle − final, and oracle − val-selected. The "paper-style" number is max over seeds of oracle, and it shows how the reported 28.2 arises. This costs about 100 × 15 inferences per run, which is negligible. Declare it in the pre-registration so it does not count as peeking.

### 4c. GT-mean vs raw
- **Attack.** LOL-v1 GT exposure is arbitrary. Raw PSNR is dominated by global brightness error, which the I-branch and the intensity definition (max vs Y) control most directly, and it probably has the largest seed variance. GT-mean deletes that component. If GT-mean scaling is per channel, it also deletes colour casts, and with them the chroma effect under test. It also uses the GT at inference.
- **Fix.** Pre-register **GT-mean PSNR with one scalar gain on luminance** as the primary metric. Secondary metrics: raw PSNR, SSIM, LPIPS, ΔE00 (raw and after scalar gain), and log-exposure error log(mean_out / mean_gt). Report the decomposition raw MSE ≈ gain error + GT-mean residual, so a raw-PSNR difference can be attributed to exposure or to structure and colour. Never apply per-channel gain.

### 4d. Compute feasibility on a 2080 Ti
- **Estimate.** 485 pairs / 8 ≈ 61 iterations per epoch, so 1000 epochs ≈ 61k iterations. CIDNet is about 1.9M params and about 7.6 GFLOPs forward at 256²; with backward plus two VGG passes (RGB and HVI), that is about 0.1 TFLOP per sample, or 0.8 TFLOP per iteration. At a realistic 3–5 TFLOPS FP32 on a 2080 Ti, that is about 0.2–0.3 s per iteration, or 3.5–5 h of training per run. Validating every epoch on 40 full-res 400×600 images adds about 1–2 h; validating every 5 epochs makes that negligible. Memory: channel-wise attention is linear in pixels, so batch 8 at 256² plus VGG should fit in 11 GB. Verify in the first 200 iterations.
- **Total.** About 5–6 h per run, 4 parallel single-GPU runs (not DDP, which would change the effective batch). 30 runs ≈ 8 waves ≈ 40–48 h wall-clock. Feasible.
- **Precision.** FP16 AMP must not touch atan2, division by max, or pow(·, k); keep the transforms in FP32 or they produce NaN or bias near black. Turing has no bf16. cuDNN non-determinism is present; accept it as part of the seed variance and report it.
- **Shortened schedules.** If epochs are cut, re-anneal the cosine schedule to the new end; do not truncate it. Arms can differ in convergence speed: better-conditioned spaces converge faster, and a short schedule favours them. Run one pilot pair (A0 and YCbCr-max) at 1000 epochs, compare the ranking at 250, 500 and 1000 from val curves, and shorten only if the Δ is stable to within 0.1 dB.

### 4e. Test-time knobs
- **Attack.** Upstream inference exposes brightness, gating and gamma parameters on the inverse transform.
- **Fix.** Fix them to identity or defaults for all arms, and list them in the pre-registration.

---

## 5. Novelty and meaning

- **Attack.** The HVI and CIDNet+ papers already publish a single-run colour-space ablation on LOLv1: sRGB 27.26, HSV 25.86, HVI ≈28.1 (GT-mean, test-selected), plus polarisation-only and C_k-only rows. "HVI wins by 0.8 ± 0.3 dB" is therefore a replication with error bars. That is legitimate, but it is not a finding about why. A null result with n=3 is not a finding at all.
- **Consequence.** Weak thesis claim: "confirmed/unconfirmed, with variance."
- **Cheap additions:**
  1. **Per-intensity-bin error analysis (zero runs, recommended).** Bin test pixels by GT intensity (max RGB) into deciles. Per bin, report RGB MSE, ΔE00 and chroma-weighted circular hue error |Δh|·S_gt, per arm and seed, with seed-level CIs. The mechanism claim of HVI is specifically that C_k fixes colour noise near black. This test is falsifiable: it predicts that A0 vs k=0 differences are concentrated in the bottom 2–3 deciles and are near zero above the median. Global PSNR is dominated by mid-tones and hides this, so this analysis also rescues the power problem.
  2. **Learned vs fixed k (about one arm).** This only matters if k moves. The k trajectory is logged for free; decide on the arm after the A0 pilot.
  3. **LOLv2-Real evaluation (zero runs).** LOLv2-Real extends and contains LOL-v1 captures, so deduplicate against the LOL-v1 train set by hash or embedding before using it as a generalisation test. Otherwise it measures memorisation. It is a good secondary check but does not explain a mechanism.
  4. **Synthetic darkness stress test (zero runs).** Darken the test inputs by ×0.5 and ×0.25 and add Poisson-Gaussian noise. Then plot the Δ(A0 − k=0) hue error against the darkening factor. It is a dose-response curve for C_k.
- **Recommendation.** Make (1) the core analysis and (4) its dose-response extension, both at zero training cost. Then the claim becomes: "HVI's gain is [is not] located where its mechanism predicts (I < p30), and the size of that gain grows [does not grow] as the input gets darker."

---

## 6. What else a CVPR-level reviewer would attack

- **Test set of 15 images from one sensor.** Report per-image Δ plots and leave-one-image-out stability. Show the LOLv2-Real (deduplicated) numbers.
- **Hyperparameters tuned for HVI.** The loss weights (50× edge, 0.5 SSIM) and the LR were tuned upstream for HVI, which advantages the HVI arm. Either run a small LR sweep ({5e-5, 1e-4, 2e-4}, 1 seed, 250 epochs) for A0 and the YCbCr-max arm, or state this explicitly as a limitation that favours HVI (a conservative direction for a null, anti-conservative for a win).
- **Capacity mismatch.** HVI-branch input is 3 channels and output 2; confirm that parameter counts are identical across arms. The ladder keeps them identical by construction.
- **GT noise.** LOL-v1 GT has its own noise and colour casts, so ΔE00 against a noisy GT has a floor. Report ΔE00 on a smoothed GT as a sensitivity check.
- **Hidden multiple comparisons.** 5 contrasts × 5 metrics × 3 read-outs is a lot of chances to find something. Pre-register one primary contrast set (the ladder steps), one metric and one read-out. Apply Holm correction across the 4 ladder contrasts. Everything else is exploratory.
- **Reproducibility of the baseline.** A0 must reproduce the third-party 23.5–24.0 dB raw range. If A0 falls outside it, the pipeline is broken; stop and debug before running the other arms.
- **Seed-to-seed k variance.** If k converges to different values across seeds, report the distribution. k is then weakly identified, which is itself a finding.

---

## Revised minimal design

Common to all arms: the same two-branch net, the same parameter count, a residual in the working space, and a fixed loss. That loss is L_rgb (L1 + 0.5 SSIM + 50 edge + 0.01 VGG) plus L_hvi with a frozen k0 (L1 + 0.5 SSIM + 50 edge, no VGG). The val set is scene-disjoint. Five matched seeds per arm.

| Arm | Representation (I-branch / HV-branch out) | What it isolates (vs neighbour) | Runs |
|---|---|---|---|
| A0 | HVI, learned k | Reference (upstream model, with the fixed loss) | 5 |
| A1 | HVI, k frozen at A0's median converged k | Learned vs fixed k (drop if k moves < 0.05; then A1 := A0) | 5 (0 if dropped) |
| A2 | HVI with k=0 (= Cartesian HSV: I=max, S·cos, S·sin) | **The C_k intensity collapse (primary contrast A0 vs A2)** | 5 |
| A3 | I=max / linear opponent chroma (Cb,Cr) | Nonlinear saturation-polar chroma vs linear chroma (A2 vs A3) | 5 |
| A4 | YCbCr (I=Y / Cb,Cr) | Intensity definition max vs luma (A3 vs A4). Expect mainly a raw-PSNR/exposure effect | 5 |
| L1 | HVI learned k, L_rgb only | Contribution of the auxiliary HVI loss (A0 vs L1) | 5 |
| (opt.) R | Split-less RGB reference (I=Y, HV-branch outputs an RGB residual) | Sanity anchor only; not on the colour-space axis | 3 |
| (diag.) U | A0 with upstream coupled-k loss (if k is not detached upstream) | k loss-hacking check (k trajectory + PSNR) | 1 |

Total: 25–30 core runs (+4 optional/diagnostic), about 40–48 h wall-clock on 4× 2080 Ti. Dropped arms: HSV-polar (predictable, already published) and split-less sRGB as a colour-space arm.

---

## Pre-registered decision rules

1. **Primary metric and read-out:** GT-mean PSNR (single scalar luminance gain) at the final epoch-1000 checkpoint, averaged over the 15 LOL-v1 test images, per run.
2. **Primary contrasts:** A0−A1, A0−A2, A2−A3 and A3−A4, each paired by seed (n=5), with Holm correction across the 4. A0−L1 is a separate, secondary family.
3. **Difference claimed** only if all of the following hold. (a) The paired-by-seed 95% t-CI (df=4) of Δ excludes 0 after Holm correction. (b) |mean Δ| ≥ 0.3 dB (smallest effect of interest) and |mean Δ| > 2·SD(Δ_s). (c) The sign of Δ_s agrees in at least 4 of the 5 seeds. (d) The mixed model PSNR ~ arm + (1|image) + (1|seed) agrees in direction. Per-image Wilcoxon tests are reported as descriptive only.
4. **Equivalence claimed** only if TOST with margin ±0.3 dB rejects at α=0.05. Otherwise the result is labelled "inconclusive". The phrase "less than the seed spread" is not used as a claim.
5. **Mechanism claim for C_k** (A0 vs A2): the difference in chroma-weighted hue error, or in ΔE00, in the bottom 3 GT-intensity deciles has a seed-level CI that excludes 0. The corresponding difference in the top 5 deciles has a CI that includes 0 or is at least 3× smaller. The darkness stress test shows |Δ| increasing monotonically across ×1, ×0.5 and ×0.25.
6. **Pipeline gate:** A0 mean raw PSNR must fall in [23.3, 24.3] dB and seed SD ≤ 0.5 dB before any other arm is launched. If SD > 0.4 dB, raise seeds to 8 on A0, A2 and A3 only.
7. **Selection bias (C2):** report (oracle − final) and (oracle − val-selected) per arm, as mean ± SD over seeds, plus max-over-seeds of the oracle as the "paper-style" number. These numbers are never used to rank arms.
8. **Frozen before launch:** loss weights, k0, the val split (by scene-cluster ID), the test-time inverse-transform knobs, the metric code and the analysis script, with hashes committed. The test set is evaluated by the frozen script only.
9. **Pivot (C3) trigger:** if the pipeline gate (6) fails, or if σ_seed > 0.6 dB even with 8 seeds, stop C1 and pivot to the density-k sweep.
