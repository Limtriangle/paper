# R3: Red-team of T1 (hue-rotation-equivariant HV branch for HVI-CIDNet)

## Verdict

1. **Do not run T1 as proposed.** Its main claim cannot hold. A model that is equivariant to hue rotation passes any hue cast straight through to the output: the output hue error equals the cast angle α exactly. Real white-balance and low-light casts are also not rotations. In the chroma plane they are translations plus scaling, i.e. diagonal gains in RGB. So both protocol (b) and the kill rule test the wrong property.
2. **Run T1 only as a narrower question.** The question becomes: *does hue equivariance built into the architecture beat hue augmentation for hue-faithful enhancement, especially with little training data?* Conditions: add an I-conditioned bias head that deliberately breaks the symmetry; train every arm from scratch on the same schedule; select and test on scene-disjoint data; and run a one-day pre-flight (no training) that can kill the project first.
3. **Move cast robustness into a separate canonicalisation front end** (gray-world or CAGE, which model translation plus scaling of the chroma plane). Evaluate it with von Kries / WB-emulator casts on the input while the ground truth stays fixed. The honest prior is that augmentation matches T1 (about 70%). Pre-register "T1 ties or loses" as the likely, publishable negative result.

---

## Fact-check of the brief (fix before writing anything)

- **arXiv 2406.09588** ("Learning Color Equivariant Representations") is by **Yang, O'Mahony & Allen-Blanchette**, not Lengyel et al. **CEConv** is Lengyel et al., NeurIPS 2023. 2406.09588 shows that CEConv's RGB-space hue rotation produces invalid RGB values, which breaks equivariance. That result is directly relevant to item 2.
- **"Illuminant Equivariant Networks for Computational Color Constancy"** appeared at **CCIW 2024** (LNCS), not ECCV 2024. Its group is the von Kries / photometric one: diagonal gains, which become offsets in log-RGB (see also "Offset equivariant networks", arXiv 2207.00292).
- **CAGE (arXiv 2608.10512)** does not work in HVI or on the "(H,V) chroma plane". It works in **AdaLAB**, an image-adaptive cylindrical CIELab space. From a **128×128 thumbnail** it predicts lightness-interval vertices, **chroma-scaling values** and a **hue-directional chroma offset** (a 2-D direction plus magnitudes per lightness vertex). That is a *lightness-dependent translation plus scaling of the chroma plane*, i.e. exactly group (ii) below. For HVI-CIDNet on LOL-v1 it reports **26.03 → 27.25 dB (+1.22)**. The abstract gives averages of +0.98 / +1.23 / +0.81 dB across backbones on LOLv1 / LOLv2-real / LOLv2-syn. There is no ΔE, no seeds and no stated checkpoint rule. The 26.03 baseline matches neither the third-party raw range (23.5–24.0) nor the usual GT-mean figures, so its eval protocol is unknown and **only your own retrain counts**. Code is linked from the project page.

---

## 1. The group mismatch

**Attack.** Take a near-gray pixel, RGB = v·(1,1,1) + c with small chroma c, and a von Kries gain g = (1+ε_r, 1+ε_g, 1+ε_b). The new pixel is ≈ v(1,1,1) + vε + c. HSV hexcone chroma is piecewise-linear in RGB and is normalised by max ≈ v. So the Cartesian chroma z = S·(cos 2πθ, sin 2πθ) maps as **z' ≈ z + t(ε)**. The shift t is the same for every near-gray pixel, whatever its brightness v or hue. That is a **translation**.

In HVI there is an extra effect. I' = max(gR) changes by a factor that depends on which channel is the maximum. So the chroma is also **scaled** by C_k(I')/C_k(I) (for example, sin^0.2 changes slowly, but not uniformly).

Saturated pixels behave differently. A pure primary (1,0,0) → (1+ε_r,0,0) keeps its hue and keeps S = 1, so it is a **fixed point**. Other rim hues are warped tangentially by an amount that depends on the hue.

A rotation does the opposite of all this: it fixes the gray centre and moves every rim hue by the same angle. **A white-balance error is defined by gray turning colored, and a rotation cannot produce that.**

Low-light color bias is also not a rotation. Black-level offsets and channel-dependent noise are additive in RGB. After S = (max−min)/max they become a translation of size about b/I plus heteroscedastic noise of size about σ/I. That is an **I-dependent translation field** plus noise, again not a rotation.

There is a second, sharper problem. **A strictly SO(2)- or C_n-equivariant network (n ≥ 2) cannot output any fixed nonzero chroma vector**, because the only rotation-invariant vector is 0. So T1 structurally *cannot learn* a constant bias correction (f(x) = x − t) or any preferred chroma direction, such as blue-channel noise being worse than green. If LOL's low→GT mapping contains a systematic chroma offset, pure T1 loses PSNR on LOL-v1, and it does so by construction.

**When does a real global hue rotation happen?** Almost only in editing: a hue slider, or a cyclic RGB channel permutation, which is ±120°. A B↔R swap is a *reflection*, which is not in SO(2). Colored or mixed LED lighting produces spatially varying diagonal gains, not rotations. Narrowband light collapses saturation. The closest physical case is a **mismatched colour-correction matrix** across devices. A gray-preserving 3×3 CCM acts as a general 2×2 linear map on the chroma plane in *linear* RGB (rotation plus shear plus scaling), and after gamma/HSV only its small rotation component survives approximately. Even in that case, equivariance *preserves* the device's rendering rather than correcting it.

**Consequence.** The motivation "robust to color casts / WB shifts" is broken. The group does not match the nuisance. In addition, pure T1 cannot represent the bias corrections LOL may need.

**The right groups.**
- (i) WB error: diagonal gains in *linear* RGB, (ℝ₊)³ modulo intensity. These are translations in log-chromaticity and approximately translation plus scaling in the chroma plane near gray.
- (ii) Low-light colour bias: an I-dependent chroma translation plus noise. This is what CAGE models, per lightness vertex.
- 2-D similarity (rotation + scale) equivariance is the wrong fix. Scale-equivariance requires bias-free, degree-1 homogeneous networks, but chroma denoising needs thresholds tied to the noise level, which are scale-dependent.

**Fix (the defensible choice for a bachelor's thesis).** Narrow T1 to **hue-rotation equivariance with an honest motivation**: *hue-faithful enhancement that treats all scene hues identically* (no learned hue prior, no directional chroma bias, weight sharing across hues, so potentially more sample-efficient). Evaluate it with the **joint** rotation protocol (see item 4).

Add one explicit symmetry-breaking term, **T1b: out_z = F_equiv(x) + b(I)**, where b is a tiny MLP from the local/global I to a 2-vector. It captures sensor-fixed chroma bias, and the size of ‖b‖ measures how much LOL actually needs a preferred direction.

Handle casts separately with a **canonicalisation front end** for the correct group: shades-of-gray / gray-world in linear RGB (non-learned translation removal), or CAGE (learned, I-dependent translation plus scaling). Do not pivot the whole thesis to diagonal-gain equivariance. It is a known result (CCIW 2024, offset-equivariant networks), and for a restoration model with a fixed GT it collapses into canonicalisation anyway (item 4).

---

## 2. Does equivariance survive the rest of CIDNet?

Treat (H,V) as a complex field z (frequency-1 irreducible representation) and I as an invariant scalar.

| Component | Exact equivariance in vanilla form? | Cheap fix |
|---|---|---|
| HVI forward, C_k(I) | Yes. A hue shift preserves HSV max and min, so I = max is **exactly** invariant and (H,V) rotates exactly | none |
| HV-branch input conv on (H,V,I) | **No.** A real conv mixes H, V and I | Complex conv on z. I enters only as an invariant gate (z·σ(conv(I))) or as a modulus-conditioned term. A linear map from invariant → vector must be zero |
| Real conv biases on vector channels | **No** | Remove them (bias = 0 on complex channels) |
| Complex conv (C→C) | Yes, exactly, and it is the *complete* SO(2)-equivariant linear family (multiplication by a·1 + b·J) | none. Note: this halves the HV parameters but keeps the same FLOPs (C² complex MACs = 4C² real MACs) |
| CEConv-style RGB rotation about the gray axis | **Wrong group for HVI.** It changes max, hence I, and yields invalid RGB (2406.09588) | Do not use CEConv. Use complex convs in HVI |
| Discrete C_n group conv | Exact only at multiples of 360°/n, so ±10/20/40° are *not* covered for n = 3 or 4 | Use the continuous complex version |
| Activations | GELU/ReLU per real component: **No** | modReLU, or a gate: z·σ(f(\|z\|, I)) |
| Restormer gated FFN (GELU(x1)⊙x2) | **No** | GELU(Re/\|·\| invariant of z1) · z2, i.e. invariant gate × vector |
| LayerNorm (WithBias) over real channels | **No.** Subtracting a mean over mixed H/V components adds a (m,m) vector; per-component affine weights and bias break it | Complex RMS-norm: divide by sqrt(mean\|z\|²) with a real positive scale per complex channel and no bias. Subtracting the complex channel-mean is also equivariant |
| HV_LCA (Q from HV, K,V from I) | **No.** Values come from the invariant I branch and are *added* to the vector stream | Values must come from the HV stream. Attention weights come from invariants: Re(q_a·k̄_b) (Hermitian product, HV–HV), or [\|q_hv\|, k_i]. The I branch can only *gate* HV, and can no longer inject content into it. This is a real information-flow change and a confound (see the A3/T1 comparison) |
| I_LCA (Q from I, K,V from HV) | **No.** Vector values enter the invariant stream | Values = invariant features of HV (\|z\|, Re(z_a z̄_b)) |
| Restormer L2-norm of q,k over space, temperature | Yes if applied to the complex modulus | none |
| Strided conv / transposed conv / pixel (un)shuffle | Yes if weights are complex and the channel pairing is kept through the reshapes | Keep pairing explicit (use a complex dtype) |
| Bilinear resize, skip concat | Yes | none |
| Global residual cat(hv,i)+hvi | Yes (sum of equivariant terms plus an invariant I) | none |
| Inverse PHVIT (÷C_k(I_out), atan2, norm, HSV→RGB, clamp) | Yes. atan2 shifts by α; S and I are invariant; an HSV hue shift keeps channels in [0,1], so clamp is harmless | none |
| Input quantisation | A rotated 8-bit image is no longer 8-bit | Rotate on the fly in float HVI, never via saved uint8 |

**Loss.** The loss does not affect the *structural* claim, because equivariance is a property of the architecture. It does matter for the augmentation arm and for what "better" means:
- L1 on (H,V) is anisotropic: errors along the 45° directions cost √2 more.
- SSIM on H and V separately, the Laplacian L1 and **VGG applied to the (H,V,I) tensor as if it were RGB** are all not rotation-invariant. The last one is perceptually meaningless as well.
- With a non-invariant loss, the joint-augmentation arm sees different effective loss weights at different angles, so augmentation looks worse than it should.

**Fix:** in all arms, replace the HVI-part L1 with |Δz| (complex modulus) and drop VGG-on-HVI. Alternatively keep the original loss in all arms and run one ablation. Keep L_rgb as is, because it defines the task.

**Unit test (mandatory):** ‖f(R_α x) − R_α f(x)‖ / ‖f(x)‖ < 1e-5 in fp32 for random α on random inputs, at initialisation and after training. Anything larger is a bug.

---

## 3. Would hue-rotation augmentation achieve the same thing?

**Attack.** With *joint* augmentation (rotate input and GT by the same α ~ U[0°, 360°)), the network sees every angle during training. There are no "unseen angles", and learned equivariance is usually within noise of built-in equivariance in-distribution. The baseline's I branch is already exactly invariant (I = max is unchanged by hue shifts), so only the HV branch and the LCA blocks need to learn the symmetry, which is a small job. Also, LOL has few strongly saturated pixels, so rotations change little and the effect size is small.

**Experiments that separate the two (and what each predicts):**
- **Sample efficiency.** Train on 10 / 25 / 100% of the scene clusters with a *fixed iteration budget* (not a fixed epoch count). Built-in equivariance should help more at low data. This is the only non-tautological win. Prediction: at 10–25% data, T1b beats A1 by 0.1–0.5 dB; at 100%, they are within 0.2 dB.
- **Unseen angles** (train A1 with α ∈ ±30°, test at 180°). T1 wins **by definition**. Report it as a sanity plot, never as evidence.
- **Equivariance error.** Zero for T1 by construction. This is informative only for A0/A1: it shows how much equivariance augmentation actually learned.
- **Parameter count.** "Fewer parameters" is a counting artefact of weight tying at equal FLOPs. Compare against A3 (a width-reduced baseline at T1's parameter count), and report FLOPs and latency too, since complex ops are often slower on a 2080 Ti.
- **Extreme angles.** The same tautology as unseen angles.

**Honest prediction.** Under natural colours (α = 0, full data): A0 ≥ A1 ≈ T1b, with T1 (no bias head) possibly −0.2 to −0.5 dB because it loses hue priors and the bias correction. Under joint rotation: A0 degrades (magnitude unknown, possibly < 0.5 dB on LOL's low-saturation content), while A1 and T1b stay flat. **Probability that A1 is within the equivalence margin of T1b on everything except the low-data regime: about 70%.**

---

## 4. Invariance vs equivariance (the central flaw)

**Attack.** Protocol (b) rotates the *input* and keeps the GT fixed. That target requires **invariance**, f(R_α x) = f(x) = y. An equivariant network satisfies f(R_α x) = R_α f(x). If f(x) ≈ y, then f(R_α x) ≈ R_α y, so the output hue error is **exactly α at every pixel**. The HVI chroma error is |e^{iα} − 1|·|z_y| = 2 sin(α/2)·|z_y|, which is 0.17 / 0.35 / 0.68 of the chroma magnitude at 10° / 20° / 40°. The result of T1 on (b) is known before running: it is the identity line.

Meanwhile A0 can partly "undo" rotations of the LOL-v1 test images because 14 of the 15 scenes are memorised from training. So the comparison is decided by memorisation, not by the architecture.

The only way to be both equivariant inside and invariant outside is **canonicalisation**. Estimate ĝ(x) with ĝ(gx) = g·ĝ(x), then output F(ĝ(x)⁻¹·x). Something has to break the symmetry and supply a reference for what "no cast" means:
- For translations and gains, a physical reference exists: achromatic surfaces (gray-world, shades-of-gray), or a learned estimator such as CAGE.
- For **hue rotations there is no physical reference.** Only learned semantic priors ("wood is orange") can supply one, so rotation-cast removal is ill-posed.

Worse, once an exact canonicaliser exists, *any* backbone F becomes invariant. Backbone equivariance adds nothing to cast robustness beyond passing the canonicaliser's residual error through unchanged instead of transforming it unpredictably. **"Robust to casts without per-image estimation" is therefore impossible by construction.**

**Consequence.** T1 as designed would "lose" its own headline experiment, or win it only by accident.

**Fix. Split the thesis into two separately evaluated claims:**
- **(A) Equivariance claim** (T1's real contribution). Protocol: rotate input and GT *jointly* by α ∈ {0°, 30°, …, 330°} in float HVI. Metrics: mean and spread of PSNR / ΔE00 across α, and equivariance error for the non-equivariant arms. Motivation: hue-faithful enhancement. It only makes sense where the degradation preserves hue, which the pre-flight checks (item 7).
- **(B) Invariance/cast claim.** Protocol: input-only casts from the *right* group (von Kries in linear sRGB over 2500–8000 K relative to 6500 K, plus the Afifi & Brown WB emulator, ICCV 2019), GT fixed, on scene-disjoint images only. Arms: canonicaliser × backbone {gray-world, CAGE} × {CIDNet, T1b}, all trained with the same input-only cast augmentation (LOL pairs have no WB casts, so without it nothing learns cast removal).
- **Drop hue-rotation-as-cast** from (B) entirely. Keep one plot showing T1's output hue error equals α exactly, as a sanity check.

---

## 5. Cross-device sets

**Attack.**
- **LOLv2-Real** includes LOL-v1 scenes, so it leaks into LOL-v1 training.
- **SID** is RAW and extreme low light (0.1 s vs 10 s). You would have to choose an ISP, including its WB, so *you* define the cast. SID is also far out of LOL's noise distribution, so it tests denoising.
- **LSRW** has a small test split (about 50 pairs), with handheld capture and possible misalignment.
- **DICM, LIME, MEF, NPE and VV** give only NIQE, and **NIQE is computed on luminance, so it is blind to colour.** It cannot support any colour claim.
- A "cross-device gain" mixes sensor noise, the ISP tone curve, the CCM and exposure. It tests domain generalisation, not hue equivariance.
- If a dataset's inputs have *no* cast relative to their GT, it cannot test cast robustness at all.

**Consequence.** As planned, the cross-device table cannot support either claim.

**Fix.**
- Deduplicate the LOLv2-Real test set against LOL-v1 train+test (pHash plus DINOv2 cosine similarity, manual confirmation; report how many images are removed). Deduplicate LSRW likewise and check alignment (report PSNR of GT vs a warped GT).
- **Measure each dataset's input→GT chroma shift before using it**: the S-weighted circular mean Δθ, and the mean Δ(a*, b*) after brightness matching. This labels each set as "hue-preserving" (tests claim A) or "hue-correcting" (tests claim B).
- Drop SID, or use only the published SID-sRGB split as a pure denoising stress test, with no colour claim.
- For unpaired sets, report NIQE only as a luminance-quality check, and label it that way. Add a no-reference cast indicator (gray-world / shades-of-gray angular deviation of the output) only as supporting evidence.
- Physically correct casts come from the synthetic von Kries / WB emulator on paired scene-disjoint data, not from the cross-device sets.

---

## 6. Fine-tuning from the released weights

**Attack.**
- Complex layers cannot inherit real weights. Projecting each 2×2 block onto aI + bJ works only at the input layer, because hidden channels have no H/V pairing.
- The modified LCA blocks change what the I branch receives (invariant HV features instead of raw ones), so the I branch is *also* off its pretrained distribution.
- "Fine-tune 50 epochs" therefore gives A0/A1 about 1000 + 50 converged epochs against roughly 50 epochs for a randomly initialised T1 HV branch. That is a large bias *against* T1.
- Freezing the I branch in all arms does not fix it, because T1's I branch sees different inputs.
- A 50-epoch fine-tune of A1 from non-augmented weights also under-trains augmentation relative to a from-scratch A1.

**Consequence.** The fast loop would rank arms by how well they were initialised, not by their architecture.

**Fix.**
- **Fast loop:** every arm **from scratch**, the same short schedule (300 epochs, cosine; about 2.5 h for A0 on one 2080 Ti and an estimated 3–4 h for T1), the same seeds, and selection on a **scene-disjoint validation split** (cluster the 485 training GTs by scene, hold out about 10% of clusters, roughly 45–50 images).
- **Check that the fast loop predicts the final ranking:** train A0 and T1b at 300 and 1000 epochs. If the ranking or gap flips (gap change > 0.3 dB), the fast loop is not trustworthy for this comparison.
- Fixed iterations for the data-fraction runs.
- Report wall-clock time and memory per arm.

---

## 7. Statistics, seeds, GT-mean, test overlap, CAGE, and other reviewer attacks

**Attacks, with fixes:**
- **15 test images, 14 of them near-duplicates of training scenes.** LOL-v1 test measures interpolation or memorisation, and for colour it lets non-equivariant models recall each scene's true hues.
  **Fix:** the primary endpoint lives on the pooled scene-disjoint set (held-out clusters + deduplicated LOLv2-Real test + LSRW). Report LOL-v1 test only for comparability, run once at the end.
- **Checkpoint chosen on the test split** (in the original CIDNet protocol).
  **Fix:** select on the validation split for every arm, including the CIDNet retrain. Mark all paper numbers as "reported" and never mix them into the statistics.
- **3 seeds.** CIDNet's seed and checkpoint spread on LOL-v1 is plausibly 0.2–0.4 dB (third-party raw results span 23.5–24.0). With 3 seeds, a true 0.3 dB difference cannot be established.
  **Fix:** use a hierarchical bootstrap over seeds × images for paired differences, and "matches" = TOST equivalence with a pre-registered margin of ±0.3 dB PSNR / ±0.3 ΔE00 (90% CI inside the margin). A wide CI is reported as "inconclusive", never as "matches". Use 5 seeds for the two arms in the primary comparison (A1 vs T1b) if the CI is wide after 3.
- **GT-mean.** CIDNet's GT-mean is a single scalar gain from the gray-image means. It does not touch chroma but hides exposure errors.
  **Fix:** report raw and GT-mean PSNR. Compute colour metrics (ΔE00, hue error, cast residual |mean Δ(a*, b*)|) without GT-mean. Never use per-channel mean matching, which would delete the cast.
- **Hue-error metric.** Hue is undefined at low saturation.
  **Fix:** use the S_gt-weighted circular error on pixels with S_gt > 0.1 and I_gt > 0.1, plus the modulus of the chroma-vector error |z_out − z_gt|.
- **Multiple comparisons** across many protocols and metrics.
  **Fix:** one primary endpoint per claim (below). Everything else is secondary and descriptive.
- **CAGE as a baseline.** A single run, a baseline of unclear protocol, and no ΔE.
  **Fix:** retrain CAGE+CIDNet with the official code under our protocol and seeds. If our retrain does not reproduce at least half of the +1.22 dB, report that as a finding. Do not tune CAGE less than T1: give every arm the same hyperparameter budget (for example, a learning-rate sweep over {1e-4, 2e-4} on validation only).
- **Pre-flight (one day, no training).** Answer three questions on LOL train + scene-disjoint validation:
  - (P1) Is there a systematic directional chroma offset between the low input and GT, as a function of I? A large offset means pure T1 cannot fit it, so T1b is required.
  - (P2) How much does *released* CIDNet degrade under joint hue rotation (mean over α of ΔPSNR, ΔΔE00)?
  - (P3) Does input→GT hue shift at all on each evaluation set (the hue-preserving vs hue-correcting labels from item 5)?
- **Novelty.** Complex/U(1)-equivariant nets and colour-equivariant CNNs exist (CEConv; 2406.09588; hypertoroidal colour equivariance, arXiv 2603.04256). The contribution is "hue equivariance for LLIE in HVI, and whether it beats augmentation". Say that plainly.
- **"Matches PSNR" as the goal.** A tie in PSNR plus exact equivariance is a thin result unless the low-data win appears. Pre-register that.
- **The claim about k.** C_k is invariant, so k is irrelevant to the symmetry. Do not claim otherwise.

---

## Revised design

Claim A: hue equivariance vs augmentation. Claim B: cast robustness via canonicalisation. Claim B runs only if Phase 1 does not kill T1.

### Arms

| Arm | What it isolates | Runs (fast loop, 300 ep) | Runs (final, 1000 ep) |
|---|---|---|---|
| A0: CIDNet retrained (our protocol, invariant \|Δz\| loss) | reference | 2 seeds | 3 (5 if needed) |
| A1: A0 + joint hue-rotation aug, α ~ U[0°, 360°) | equivariance by augmentation (the real competitor) | 2 | 3–5 |
| A3: A0 width-reduced to T1b's parameter count | the "fewer parameters" confound | 2 | 0 unless it beats A0 |
| T1: complex HV branch, invariant attention/norm/gates, no bias | pure built-in equivariance; cost of losing all directional priors | 2 | 0 unless the P1 bias ≈ 0 |
| T1b: T1 + I-conditioned bias head b(I) | built-in equivariance plus controlled symmetry breaking (main T1 variant) | 2 | 3–5 |
| A1 / T1b at 10% and 25% of clusters (fixed iterations) | sample efficiency, the only non-tautological advantage | 2 × 2 × 2 = 8 | 3 seeds × best fraction × 2 arms = 6 |
| **Phase 2 (Claim B):** GW+A0, GW+T1b, CAGE+A0, CAGE+T1b, A2 (A0 + input-only von Kries/WB-emulator aug), all trained with input-only cast augmentation | canonicaliser vs learned invariance, and whether an equivariant backbone behaves better behind a canonicaliser | 5 × 2 = 10 | 5 × 3 = 15 |

Budget: Phase 1 fast loop is about 18 runs × roughly 3 h ≈ 55 GPU-h (≈ 14 h wall on 4 GPUs). Phase 1 final is about 12 runs × roughly 10 h ≈ 120 GPU-h (≈ 30 h wall). Phase 2 final is about 150 GPU-h. This fits in about two weeks of machine time.

### Evaluation

| Protocol | Metric | What a T1 win looks like |
|---|---|---|
| E0 unit test: random α, random inputs | relative equivariance error | < 1e-5 for T1/T1b. Otherwise it is a bug and not a result |
| E1 natural colours, pooled scene-disjoint set (+ LOL-v1 test reported once) | PSNR raw/GT-mean, SSIM, LPIPS, ΔE00, cast residual | T1b equivalent to A0 and A1 within ±0.3 dB / ±0.3 ΔE00 (TOST) |
| E2 joint hue rotation α ∈ {0°, 30°, …, 330°} on scene-disjoint hue-preserving sets | mean and max−min over α of PSNR/ΔE00; equivariance error for A0/A1 | T1b's mean over α ≥ A1's. The spread being 0 is expected, not a win |
| E3 data efficiency (10/25/100%) on E1 + E2 | PSNR/ΔE00 of T1b − A1 per fraction | gap ≥ +0.3 dB at ≤ 25% data with CI excluding 0, shrinking at 100% |
| E4 hue-bias diagnostic | per-hue-bin (12 bins) ΔE00 variance; ‖b(I)‖ for T1b | lower across-hue error variance for T1b than A1 |
| E5 (Phase 2) input-only von Kries 2500–8000 K + WB emulator, GT fixed, scene-disjoint | ΔE00, cast residual, S-weighted hue error, PSNR vs cast strength (area under the curve) | CAGE+T1b ≥ CAGE+A0 and GW+T1b ≥ GW+A0 within or above the margin. T1 alone under hue-rotation cast gives hue error = α (sanity plot only) |
| E6 cross-dataset (deduplicated LOLv2-Real, LSRW) | same as E1, plus the measured input→GT cast per set | a domain-generalisation statement only, interpreted per the hue-preserving vs hue-correcting label |
| E7 unpaired sets | NIQE (luminance only) + gray-world angular deviation | supporting evidence only; no colour claim from NIQE |

## Pre-registered decision rules

1. **Primary endpoint, Claim A:** PSNR difference T1b − A1 on the pooled scene-disjoint set, averaged over E2 angles, at 25% data. **Secondary:** the same at 100% data, and ΔE00.
2. **Primary endpoint, Claim B:** ΔE00 area under the cast-strength curve (E5, von Kries), CAGE+T1b vs CAGE+A0.
3. "T1 better" = 95% hierarchical-bootstrap CI of the difference excludes 0 in T1's favour. "Equivalent" = 90% CI inside ±0.3 dB / ±0.3 ΔE00. Anything else = "inconclusive".
4. Select checkpoints only on the scene-disjoint validation split. Touch the LOL-v1 test and the external test sets once per final model.
5. If P1 shows a directional input→GT chroma offset whose mean |Δz| exceeds 0.02 (in HVI units, over pixels with I > 0.1), drop pure T1 and keep only T1b.
6. If the fast-loop gap between A0 and T1b changes by more than 0.3 dB between 300 and 1000 epochs, run final comparisons at 1000 epochs only.
7. Report every arm and seed that was run, including failures.

## Kill criteria

- **K0 (pre-flight, day 1).** If released CIDNet under joint rotation (P2) loses < 0.3 dB mean PSNR **and** < 0.5 ΔE00 on scene-disjoint data, there is no problem for equivariance to solve. Stop T1 and pivot to Claim B only (canonicaliser study with CIDNet).
- **K1 (fast loop).** If T1b is worse than A0 on validation E1 by > 0.5 dB and a width/LR sweep does not close the gap, kill T1. The equivariant constraint costs too much capacity.
- **K2 (augmentation matches, replaces the original kill rule).** If A1 is equivalent to or better than T1b on E1 **and** E2 **and** at every data fraction in E3, the T1 claim is dead. Write it up as a negative result: "augmentation suffices; built-in hue equivariance gives no measurable benefit for LLIE." Do not run Phase 2 with T1b; run it with A0 only.
- **K3 (Phase 2).** If CAGE+T1b is not better than CAGE+A0 on E5 (by rule 3), drop the "equivariant backbone behind a canonicaliser" claim.
- **Never kill on** equivariance error, unseen-angle tests or parameter count. T1 wins those by construction, so they carry no evidence.
