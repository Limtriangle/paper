# R4 red-team: T3, test-time adaptation of HVI-CIDNet's exposure knobs

## Verdict

1. **Worth running, but only as a GT-oracle gated *decomposition study*.** It should not be pitched as a "TTA method". As proposed, the headline "recovers PSNR under brightness shift" is almost guaranteed to be true and almost guaranteed to be trivial. MILL's collapse is mostly a global over-exposure error, which any scalar gain chosen by an exposure loss removes.
2. **What must change.** (a) Run a zero-training GT-oracle phase first: per-image oracle over {pre-gain only} vs {all knobs}. This decides whether HVI knobs carry anything beyond auto-gamma. (b) Make the primary contrast *T3-full vs T3-gain-only under the same loss and target E*, so that the exposure prior cancels out. (c) Add the closed-form "mean-match pre-gain" baseline and the identity baseline, since MILL inputs contain up to 50% GT. (d) Retrain the aug baseline with 3 seeds and both a mismatched and a matched augmentation family. (e) Use the scene as the unit of replication, and pool with a de-duplicated LOLv2-Real test set to get beyond 15 scenes.
3. **Honest expected outcome.** "CIDNet's brightness-shift failure is roughly X% one scalar of exposure miscalibration, fixable without training. HVI's chroma knobs (k, alpha_s) add ≤ Y dB / ≤ Z ΔE." That is a legitimate bachelor's result if X, Y and Z are measured cleanly. The claim of a new method is not.

---

## 1. Is the target well-posed? Choosing the metric

**Attack.** Under MILL the GT is fixed, and the input is `(1-a)·low + a·GT`. The non-reference exposure loss pulls the mean local intensity toward a generic E, not toward this image's GT exposure. Three consequences follow:
- Raw PSNR rewards "E happens to match the LOL-GT brightness convention". It does not reward better enhancement. LOL-GT means vary a lot across images, so a single E gives an irreducible per-image exposure error.
- GT-mean PSNR, the CIDNet repo's global gray-level gain alignment to GT, removes exactly the error that T3 mostly fixes. The MILL collapse may then shrink to a small effect under GT-mean. That would leave little for T3 to recover on that metric, except where clipping destroyed information that no gain can restore.
- Tuning E on LOL is not per-image GT leakage. It is still a dataset-level prior, and the frozen network already embodies the same prior. On LSRW/SICE, whose GT tonal conventions differ, a LOL-tuned E is penalised by raw PSNR for reasons unrelated to enhancement quality.
- The MILL input itself leaks GT. At a = 0.5 the identity mapping alone scores about 7.8 + 20·log10(2) ≈ 13.8 dB (LOL-v1 low-input PSNR ≈ 7.8). That is essentially CIDNet's 14.1. A method that "trusts the input more" wins in a way that would not transfer to a real brighter capture.

**Consequence.** Raw PSNR alone makes the headline unfalsifiable: any auto-exposure wins. GT-mean alone can hide the whole effect. Neither tells you whether the *HVI knobs* did anything.

**Fix.**
- **Decompose the error for every arm**: MSE = (μ_out − μ_GT)² [exposure term] + residual. Report the fraction of MSE due to the exposure term, plus the clipped-pixel fraction (output ≥ 0.99).
- **Primary endpoints** (pre-registered):
  - P1, recovery: raw PSNR averaged over blend levels {20, 35, 50}%. It is legitimate here because under MILL, exposure correctness *is* the task. It is always shown next to the gain-only arm and the oracle-gain bound.
  - P2, beyond exposure: GT-mean PSNR and ΔE00 split into lightness vs chroma/hue parts (ΔL′ vs √(ΔC′²+ΔH′²)). This is the only metric on which k/alpha_s can claim credit.
- **E policy**: E_native = the mean output of the frozen network on in-distribution inputs of the tuning set. This is the network's own convention, and it is not taken from test GT. Report a sensitivity curve over E ∈ {0.3…0.6}. For cross-dataset sets, P2 is primary and raw PSNR is secondary.
- Add the **identity** and **"input gained to E, no network"** baselines to every MILL table.

## 2. Triviality: is this auto-gamma in disguise?

**Attack.**
- `alpha` is an output-side gain on I. Input gamma/gain is an input-side distribution alignment. Both mainly correct global brightness.
- With 1–5 scalars and an exposure loss, the gradient loop is a slow grid search. For one parameter it has a near-closed form: gain the input so its mean matches the LOL-low training mean.
- k is used in both the forward HVIT and the inverse transform. Changing it at test time shifts the HV-branch input away from what the network was trained on.
  - At k ≈ 0.2, C_k(0.05) ≈ 0.60 and C_k(0.5) ≈ 0.93.
  - Under a *brighter* input, C_k is already close to 1 for most pixels. So k has little leverage exactly where the shift happens.
  - Prediction: k barely moves, or moving it hurts.
- alpha_s (default 1.3) is a plausible lever for the ΔE blow-up: over-saturation on inputs that are already colourful. But MILL's ΔE rise is probably dominated by the lightness error.

**Consequence.** If gain-only ≈ full, T3 reduces to "auto-exposure pre-processing for CIDNet". NTIRE 2026 already shows plain gamma (14.91) beating zero-shot CIDNet (13.85).

**Fix.** Run a knob ablation ladder with the same loss, the same E and the same step budget:
- G0: closed-form mean-match pre-gain (no optimisation)
- G1: pre-gain/gamma only
- G2: output alpha only
- G3: G1 + alpha
- G4: G3 + alpha_s
- G5: G4 + k (both variants: k_inv only, and k_fwd = k_inv tied)
- G6: G5 + I-branch LayerNorm affine (expressivity arm; expect overfitting)

Separating pre-gain from post-gain is a real mechanism test. If the frozen network clips highlights, post-hoc alpha cannot recover them but pre-gain can. The clipped-pixel fraction makes this visible. Also run a grid-search version of G1/G3, so the claim is about the *knob set and loss*, not the optimiser.

## 3. Does TTA hurt in-distribution?

**Attack.** On LOL-v1, 14 of 15 test scenes have near-duplicate training scenes, and the released checkpoint may have been selected on the test set. The frozen output is therefore close to memorised per-image brightness. A generic-E pull moves it away from that, so ungated TTA will very likely lose raw PSNR in-distribution. Per-image instability comes from init, lr and step count; with no stochasticity, seeds are irrelevant. The NR losses are gameable. Gray-world colour constancy is wrong for LOL scenes with dominant colours, and LOL-GT is not gray-balanced. NIQE/IQA priors are adversarially easy to exploit, and optimising them makes NIQE evaluation circular.

**Consequence.** "No loss on LOL-v1" is either false (ungated) or true by construction (gated), and then it only says something about the detector.

**Fix.**
- Bound the knobs by parametrisation (e.g., pre-gain ∈ [0.25, 1], alpha ∈ [0.7, 1.3]). Use a proximity penalty to the trained values, with early stopping on loss plateau. Fix N and lr on the tuning set only.
- **Gate**: adapt only if the input mean / 95th percentile falls outside the range seen in LOL-low training inputs. Report the detector's AUROC and false-positive rate on unshifted LOL-v1 and LOLv2-Real. Also report ungated results, because the gate itself is an auto-exposure heuristic.
- Report the sensitivity band over lr × N (e.g., 3×3) as the variability measure, instead of seeds.
- Put colour constancy at weight 0 as the default, with gray-world as an ablation. **Drop NR-IQA from the loss.** If NIQE is evaluated, it must never be optimised.

## 4. Is the augmentation baseline the real killer?

**Attack.** Random gamma γ ∈ [0.6, 1.2] on inputs with mean ≈ 0.05–0.1 covers means up to about 0.17–0.25. MILL 20% (mean ≈ 0.15) is inside that range, and 50% (≈ 0.25) is at the edge. The augmentation will likely close most of the gap at 10–35%. An augmentation that *matches* the test family (random blend toward GT, which is essentially MILL's own training idea) will very likely beat any TTA on MILL. Retraining is cheap on 4×2080Ti (hours).

**Consequence.** T3's contribution may shrink to "no retraining needed, and it handles shifts the augmentation did not foresee".

**Fix.**
- Aug baseline with **3 seeds**, trained with the released recipe. Report the seed SD; third-party retrains already span 23.5–24.0.
- Two augmentation families:
  - A1: repo gamma, mismatched with the MILL blend.
  - A2: blend-toward-GT, matched to MILL. This is the honest upper reference.
- Test both on a **family not covered by either** (linear-gain exposure protocol, SICE).
- Add the arm **A1 + T3**, to test complementarity.
- **Honest framing**: train-time vs test-time robustness under *foreseen* vs *unforeseen* shift. T3 is only a meaningful win if it beats A1 on unforeseen shifts, or adds to it. It is not expected to beat A2 on MILL.

## 5. Is the Retinexformer control needed?

**Attack.** Retinexformer has no alpha_s/k analogue. The "same TTA" there is just pre-gain + output gain, so it confounds backbone quality, training recipe and shift sensitivity. It cannot isolate the effect of HVI knobs; the within-CIDNet ladder (G1 vs G5) does that.

**Consequence.** As framed it is a weak and misleading control.

**Fix.** Keep it only as a **generality arm**: does gain-only TTA recover the same share of the collapse in an RGB backbone? It costs almost nothing (released LOL-v1 checkpoint, frozen). Claim "HVI knobs matter" only from G5 − G1 within CIDNet.

## 6. Protocol validity and statistics

**Attack.**
- The MILL blend is synthetic and injects GT (structure, clean colour, halved noise).
- LOLv2-Real, LSRW and SICE change scene, camera and GT style along with exposure.
- 15 test scenes is tiny, and they are near-duplicates of training scenes.
- Pooling 15 scenes × 5 blend levels as 75 "independent" pairs is pseudo-replication.
- The MILL 0% number (26.4) is above third-party retrains (23.5–24.0), which suggests a test-selected checkpoint.
- Runtime must be comparable across arms.

**Consequence.** Inflated significance, and an "exposure shift" effect that is really scene/camera/style shift or GT leakage.

**Fix.**
- **Gate 0**: reproduce MILL's curve with the released checkpoint before anything else. If the collapse does not reproduce, re-motivate.
- **Clean isolators of exposure shift**:
  - (i) Synthetic **linear-gain protocol**: inverse-sRGB, then ×{1.5, 2, 3, 4}, then sRGB, then clip. Scene, camera and GT are fixed, and no GT enters the input.
  - (ii) **SICE within-sequence**: same scene and camera, several real exposures. Metrics are GT-mean PSNR/ΔE00 plus output consistency across exposures, i.e. the per-scene std of outputs, which needs no GT.
  - MILL is kept for comparability with the literature.
  - LOLv2-Real is stratified by input brightness as a real but confounded check.
  - Unpaired/NIQE results are exploratory only.
- **Replication unit = scene.** Average over blend levels per scene first, or fit a mixed model with a scene random effect. Use a paired Wilcoxon test and a bootstrap 95% CI over scenes. For retrained arms, the seed is a second unit: report seed-mean ± SD, and compare against T3 only if the gap exceeds 2×SD.
- **Enlarge n**: add the LOLv2-Real test set after hash + visual **de-duplication against all of LOL-v1** (LOLv2-Real overlaps LOL-v1; this must be verified). That gives roughly 100 or more scenes. Tune only on a scene-disjoint split that the network never saw, e.g. de-duplicated LOLv2-Real *train* scenes, not LOL-v1 training images, which the network has memorised.
- **Runtime**: same GPU, full resolution, batch 1, warm-up excluded, median over 50 runs. Report the frozen forward time, the TTA wall-clock (N steps) and the grid-search variant, and state the aug-retrain cost as amortised GPU-hours.

## 7. Novelty and meaning

**Attack.** Per-image optimisation with Zero-DCE losses, and test-time adaptation for restoration, both already exist (e.g., test-time degradation adaptation for open-set restoration, arXiv 2312.02197; per-image self-supervised Retinex unrolling, arXiv 2202.05972). "TTA of a few scalars" would read as incremental at CVPR. A reviewer would accept a *finding*, not the method.

**Fix: zero-training mechanism additions.**
- **Brightness transfer curve** of frozen CIDNet: μ_out vs μ_in across MILL levels and linear-gain levels. This shows the learned approximately constant gain that over-exposes brighter inputs. It explains the collapse and yields a closed-form "invert-the-transfer" calibration (G0′).
- **Oracle decomposition** (GT-selected per image): oracle-gain vs oracle-all-knobs. This bounds what any loss could extract from the knob family.
- **Knob trajectories** vs input brightness: which knob moves, and its correlation with shift level, e.g. Spearman of Δk, Δalpha, Δalpha_s vs μ_in. The pre-registered prediction is that alpha/pre-gain carry about 90% and k about 0.
- **Clipping analysis**: pre-gain vs post-gain under highlight clipping.
- If alpha_s moves systematically and lowers ΔC′, that is the one HVI-specific result worth a figure.

---

## Revised design

### Arms

| Arm | What it isolates | Cost |
|---|---|---|
| F0 frozen CIDNet, official knobs | reference failure | 0 |
| ID identity (input as output) | GT leakage in MILL | 0 |
| GAM gamma/gain to E, no network | "no network needed" floor (NTIRE) | 0 |
| G0 closed-form mean-match pre-gain → CIDNet | trivial auto-exposure | 0 |
| G0′ invert frozen transfer curve | calibration without optimisation | 0 |
| S static knobs tuned on the tuning split (dataset-level) | per-image vs global calibration | minutes |
| G1…G5 TTA ladder (same loss, E, N) | contribution of each knob | minutes/protocol |
| G6 + LN affine | expressivity vs overfitting | minutes |
| G1/G3 grid-search variants | optimiser irrelevance | minutes |
| O-gain / O-all oracles (GT-selected per image) | upper bounds, knob-family ceiling | minutes |
| A1 retrain + repo gamma aug ×3 seeds | train-time robustness, foreseen-mismatched | ~hours ×3 |
| A2 retrain + blend aug ×3 seeds | matched-aug ceiling | ~hours ×3 |
| A1 + G_best | complementarity | minutes |
| R Retinexformer frozen + gain-only TTA | generality, not HVI isolation | minutes |

### Protocols

| Protocol | Metric (primary first) | What a win looks like |
|---|---|---|
| LOL-v1 as-is (15, memorised) + LOLv2-Real test de-duplicated, unshifted | raw PSNR, GT-mean PSNR, gate FPR | gated T3 within 0.1 dB of F0; ungated loss reported |
| MILL blend 0/10/20/35/50 on the pooled set | P1 raw PSNR (20–50 avg); P2 GT-mean PSNR + ΔC′H′; exposure-MSE share; clip % | G_best ≥ G0 + 0.3 dB (P1) *and* G5 > G1 on P2 with CI excluding 0 |
| Linear-gain ×1.5–4 (clean synthetic) | same | same pattern holds without GT leakage |
| SICE within-sequence | GT-mean PSNR, ΔE00, cross-exposure output std | lower cross-exposure std than F0 and A1 |
| LSRW / LOLv2-Real stratified by brightness | GT-mean PSNR, SSIM, LPIPS | no regression vs F0; gains grow with μ_in |
| Unpaired sets | NIQE (exploratory, never optimised) | report only |

## Pre-registered decision rules

- **D0.** The MILL collapse reproduces with the released checkpoint (≥ 6 dB raw drop at 50%). Otherwise re-scope.
- **D1 (knobs vs gain).** Compare O-all − O-gain on P1 and P2 over the pooled MILL + linear-gain sets. If < 0.3 dB and < 1 ΔE00, report "HVI knobs carry no exposure-shift information beyond a gain". The thesis becomes the decomposition study, and G4/G5 are reported only as negatives.
- **D2 (TTA vs trivial).** T3 is claimed as a method only if G_best − G0 ≥ 0.3 dB on P1 with a bootstrap CI over scenes excluding 0 *and* it does not lose on P2.
- **D3 (HVI-specific).** A HVI-specific claim requires G5 − G1 > 0 on P2 (CI excludes 0) on MILL *and* linear-gain.
- **D4 (vs augmentation).** "Competitive with retraining" requires G_best ≥ A1 seed-mean − 1 SD on P1 at 20–50%. "Complementary" requires A1 + G_best > A1 by ≥ 0.3 dB. Beating A2 is not expected and not claimed.
- **D5 (in-distribution).** The gated arm must be within 0.1 dB of F0 on unshifted pooled data, with gate FPR ≤ 5%. Ungated numbers are always shown.
- All hyper-parameters (knob set, N, lr, loss weights, E, gate threshold) are frozen on the tuning split before any test protocol is run. The test protocols are run once.

## Kill criteria

- **K1.** O-all ≈ O-gain (D1 fails) *and* G0/G0′ recovers ≥ 90% of G_best's P1 gain. Kill T3 as a method; write the decomposition/calibration thesis.
- **K2.** The frozen CIDNet GT-mean PSNR drop under MILL at 50% is < 1 dB and clipping is < 1%. The collapse is then pure exposure, and only a calibration story remains.
- **K3.** A1 (3 seeds) beats G_best by more than 2 SD at every level *and* has no in-distribution cost. Drop the robustness claim and keep only "no retraining".
- **K4.** Ungated T3 loses > 0.5 dB in-distribution *and* gate AUROC < 0.9. No deployable claim.
- **K5.** The results flip sign across the lr × N sensitivity band. The method is unstable, so report it as negative.

## Probability estimate

- **P(T3 beats the augmentation-retrain baseline A1, repo gamma aug, on raw PSNR under MILL, averaged over 20–50%, by more than seed noise) ≈ 0.30.**
  - Most of that probability comes from the 50% level, which is at or beyond the augmentation range, and from the pre-gain knob, not the HVI knobs.
- Against a matched blend augmentation (A2): ≈ 0.05.
- P(HVI-specific knobs, G5 − G1, give a significant P2 gain) ≈ 0.25.
- P(T3 as a whole beats closed-form G0 by ≥ 0.3 dB) ≈ 0.35.
