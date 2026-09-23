# phase0_related.md — what HVI-CIDNet claims, ablates, and leaves open

Owner: `writing`. Phase 0 deliverable (HVI-PLAN.md §Phase 0, step 1). Read alongside
`ralph/results/phase0_codebase.json` (experiment's ground truth on cost and protocol).

Sources: the CVPR 2025 paper (arXiv 2502.20272, fetched by a subagent, section/table
references given inline), its earlier version (arXiv 2402.05809), the upstream code at
`/home/work/research/code/HVI-CIDNet` (commit `eb43d7d`, 2026-03-09, read directly), and
the upstream README. Everything under "code says" was read from source; everything under
"paper says" was read from the fetched paper; "our observation" is ours and is not a claim.

---

## 1. What the code does (read from source, commit eb43d7d)

### 1.1 The HVI transform (`net/HVI_transform.py`, class `RGB_HVI`)

- Forward `HVIT(rgb)`: computes HSV-style `value = max(R,G,B)`, `hue` (six-sector, in
  `[0,1)`), `saturation = (max - min) / (max + eps)`, then
  `color_sensitive = (sin(value * pi/2) + eps) ** k`, and
  `H = color_sensitive * saturation * cos(2 pi hue)`, `V = color_sensitive * saturation * sin(2 pi hue)`,
  `I = value`. Output channels `[H, V, I]`, with `H, V` in `[-1, 1]` and `I` in `[0, 1]`.
- `k` is `density_k`, a **trainable** `nn.Parameter` initialised to `0.2` (the comment says it
  is the reciprocal of the paper's k). The chroma plane is therefore collapsed toward the
  origin as intensity goes to zero, with a learned exponent.
- Inverse `PHVIT(hvi)`: clamps `H, V` to `[-1,1]`, `I` to `[0,1]`, divides `H, V` by
  `color_sensitive(I)` recomputed from the **output** intensity, recovers hue by `atan2`
  and saturation by the norm, then standard HSV to RGB. The inverse uses `self.this_k`, a
  Python float cached during the last forward call (`k.item()`), so **no gradient flows
  into `k` through the inverse**; `k` is trained only through the forward transform.
- Two inference-time knobs exist that are off by default: `gated` (`alpha_s = 1.3`
  saturation scale) and `gated2` (`alpha = 1.0` global scale). The README's `--alpha`,
  `--alpha_s`, `--gamma` flags drive these for unpaired datasets.

### 1.2 The network (`net/CIDNet.py`, `net/LCA.py`)

- Two U-shaped branches, channels `[36, 36, 72, 144]`, heads `[1, 2, 4, 8]`, no
  normalisation in the up/down blocks (`norm=False`).
  - **HV branch** takes all three HVI channels (`Conv 3 -> 36`) and outputs two channels.
  - **I branch** takes the intensity channel only (`Conv 1 -> 36`) and outputs one channel.
- Six **Lighten Cross-Attention (LCA)** pairs, one per stage on the way down and up. Each
  LCA = LayerNorm, cross-attention block `CAB` (query from own branch, key/value from the
  other branch, depthwise-conv projections, channel attention normalised along the last
  dim, Restormer-style), then a gated feed-forward `IEL` (expansion 2.66).
  - `I_LCA`: `x = x + CAB(...)`; `x = x + IEL(norm(x))` (two residuals).
  - `HV_LCA`: `x = x + CAB(...)`; `x = IEL(norm(x))` (**no residual around the FFN**). The
    comment says "IEL and CDL have same structure"; the asymmetry is in the code as shipped.
- Output: `output_hvi = cat(hv_0, i_dec0) + hvi` (a global residual in HVI space), then
  `PHVIT` back to RGB. The network predicts an HVI *residual*.
- Our observation (code path, `CIDNet.forward`): at stage 3 the encoder downsamples the
  **pre-LCA2** features (`IE_block3(i_enc2)`, `HVE_block3(hv_2)`), while the LCA2 outputs
  feed only the skip connections `v_jump2`/`hv_jump2`. Whether this is intended is not
  stated anywhere. It is a fact about the released weights, not a claim about the paper.

### 1.3 The loss (`train.py` lines 62-64, `loss/losses.py`, `data/options.py`)

```
loss_rgb = L1(rgb) + D(rgb) + E(rgb) + P_weight * P(rgb)
loss_hvi = L1(hvi) + D(hvi) + E(hvi) + P_weight * P(hvi)     # hvi = HVIT(output_rgb) vs HVIT(gt)
loss     = loss_rgb + HVI_weight * loss_hvi
```

| term | class | default weight (options.py) | note |
|---|---|---|---|
| L1 | `L1Loss` | `L1_weight = 1.0` | mean absolute error |
| D | `SSIM` | `D_weight = 0.5` | structure term |
| E | `EdgeLoss` | `E_weight = 50.0` | MSE of Laplacian-pyramid residuals (Gaussian 5-tap) |
| P | `PerceptualLoss` (VGG19 conv1_2, conv2_2, conv3_4, conv4_4, MSE) | `P_weight = 1e-2` | applied identically to the 3-channel HVI tensor, whose `H, V` lie in `[-1,1]` |
| HVI | scalar | `HVI_weight = 1.0` | weight of the whole HVI-space sum |

- The released LOL-v1 weights come in two flavours, `w_perc.pth` and `wo_perc.pth` (README
  table); the README reports PSNR/SSIM/LPIPS for each with and without GT-mean rescaling.
- The **VGG perceptual term is computed on HVI tensors as if they were images**: VGG input
  normalisation is applied to `H, V` in `[-1,1]`. This is what the code does; the paper's
  description is checked in §2.

### 1.4 Training protocol (code defaults, `data/options.py`, `train.py`)

| setting | default |
|---|---|
| dataset for `lol_v1` | train `LOLdataset/our485`, validation **`LOLdataset/eval15`** |
| batch / crop | 8 / 256 |
| epochs | 1000, checkpoint every 10 (`snapshots`) |
| optimizer | Adam, lr 1e-4 |
| schedule | cosine annealing with restart (`cos_restart=True`), 3 warm-up epochs |
| augmentation | random crop and flips in the dataset class; optional random gamma `[0.60, 1.20]` on the input (`--gamma`, off by default) |
| gradient clipping | `grad_clip=True`, `clip_grad_norm_(…, 0.01)` |
| precision | FP32 (no AMP in `train.py`) |

- **Our observation (integrity-relevant):** upstream's "validation" set for LOL-v1 is
  `eval15`, i.e. **the LOL-v1 test split**. Per-checkpoint metrics are printed on it and the
  README's numbers come from a checkpoint chosen that way (the README also lists a separate
  "test finetuning" row and warns against it). Under our floor (rule 4) the plan must carve
  a validation subset out of `our485` and never let selection see `eval15`.
- **Our observation (code):** `clip_grad_norm_` is called **before** `optimizer.zero_grad()`
  and `loss.backward()` (`train.py` lines 66-71). It therefore clips the gradients of the
  *previous* step, which are then zeroed. The clipping is a no-op on the gradients actually
  applied. Any protocol we freeze should state whether we keep this as-is (faithful) or fix
  it (a protocol change).
- **Our observation (data):** the dataset class reseeds Python's `random` from
  `np.random.randint` per item; seed control for a reproducible run needs to be added at the
  script level (experiment's instrument work).
- GT-mean: `measure.py --use_GT_mean` rescales the output by the ratio of the GT's grey mean
  to the output's grey mean before computing PSNR/SSIM. The README reports both; the plan
  must pick one and say which.

### 1.5 What the README adds (README, 2026-03 state)

- Released weights: LOL-v1 (`w_perc`, `wo_perc`, `test_finetuning`), LOL-v2-real
  (`best_PSNR`, `best_SSIM`, `w_perc`), LOL-v2-syn (`w_perc`, `wo_perc`, `generalization`),
  LOL-Blur, SICE, SID, FiveK. Hosted on Hugging Face (`fediory/HVI-CIDNet-*`).
- README LOL-v1 rows (as printed, not our measurements): `w_perc` 23.8091 / 0.8574 / 0.0856
  (no GT mean) and 27.7146 / 0.8760 / 0.0791 (GT mean); `wo_perc` 23.5000 / 0.8703 / 0.1053
  and 28.1405 / 0.8887 / 0.0988. A peer-trained LOL-v1 checkpoint reaches 24.7401 PSNR on an
  RTX 4070. These are **the authors' numbers**; they never enter the paper as ours.
- The authors state that "some of the training parameters we are no longer able to provide"
  and that the weights are reproducible "by parameter tuning". Exact reproduction of the
  README numbers is therefore not guaranteed by the released config.
- Random gamma augmentation (added 2025-01) is claimed to improve cross-dataset
  generalisation (NIQE/BRISQUE on DICM/LIME/MEF/NPE/VV).
- Follow-up: HVI-CIDNet+ (arXiv 2507.06814, "Beyond Extreme Darkness"), separate repo.
  FusionNet (NTIRE 2025 LLIE winner) fuses HVI-CIDNet with other models.

---

## 2. What the paper claims (CVPR 2025, arXiv 2502.20272v2)

Section numbers refer to the final version. Numbers are copied as printed; none is ours.

### 2.1 The three contributions (§1, near-verbatim)

1. **A new color space, HVI**, "uniquely defined by polarized HS and trainable intensity",
   which "eliminates the color space noise arising from the HSV space". The two named
   HSV defects are (i) *red discontinuity*: red sits at both ends of the hue axis, so the
   same color is far apart in Euclidean terms; (ii) *black plane noise*: the whole V=0
   plane maps to one RGB black, so near-black chroma is ill-conditioned. Polarization
   (`h = cos(pi h/3)`, `v = sin(pi h/3)`) fixes (i); the collapse function
   `C_k = (sin(pi I_max/2) + eps)^(1/k)` with trainable `k` fixes (ii) by shrinking the
   chroma radius toward zero as intensity goes to zero (Eqs. 4-5). Inverse in Eq. 6, with
   user knobs `alpha_S`, `alpha_I`, described as "a surjective mapping".
2. **CIDNet**, a dual-branch UNet with six Lighten Cross-Attention (LCA) blocks that models
   intensity and chroma concurrently in HVI; "1.88M" parameters and "7.57GFLOPs" at
   256x256 (Table 1 caption). LCA = cross-attention block CAB (query from own branch,
   key/value from the other) + intensity enhancement layer IEL (I-way) or color denoise
   layer CDL (HV-way), Eqs. 14-18.
3. "Outperforms various types of state-of-the-art (SOTA) methods on different metrics across
   10 datasets."

### 2.2 The loss as described (§4.4, supplement §10.2)

Main text Eq. 7: `L = lambda * l(HVI) + l(sRGB)`. Supplement Eq. 22:
`l = lambda_1 L1 + lambda_d L_SSIM + lambda_e L_edge + lambda_p L_perc`.
**No numeric value of any lambda is printed in any version.** The code defaults (§1.3) are
the only record; the README says some training parameters can no longer be provided.

### 2.3 Headline numbers (Table 1, PSNR / SSIM / LPIPS, CIDNet row)

| split | printed | which weights (README cross-check) |
|---|---|---|
| LOL-v1 (GT-mean, per caption) | 28.201 / 0.889 / 0.079 | PSNR+SSIM from `wo_perc` (28.1405/0.8887), LPIPS from `w_perc` (0.0791) |
| LOL-v2-real | 24.111 / 0.871 / 0.108 | "best Normal" 24.1106/0.8675/0.1162 (SSIM 0.871 vs 0.868 elsewhere) |
| LOL-v2-syn | 25.705 / 0.942 / 0.045 | `wo_perc` no GT-mean 25.7048/0.9419/0.0471 |

The earlier arXiv version (2402.05809 v3, Tables I-II) prints both flavours: with perceptual
loss (wP) and without (oP), each with and without GT-mean. E.g. LOL-v1 wP 23.809/0.857
(normal) -> 27.715/0.876 (GT-mean); oP 23.500/0.870 -> 28.141/0.889. The final paper's
single row silently takes the best of these per column.

Other headline claims: Sony-Total-Dark 22.904/0.676, "surpasses the second-best by 6.678 dB";
LOL-Blur 26.572/0.890/0.120 (Table 10); SICE Mix+Grad pooled 13.435/0.642 (Table 2);
unpaired NIQE 3.523 average, from a separately trained "LOLv2+" model with random gamma
(§10.8, the paper itself says it "avoid[s] direct comparisons" there).
Plug-in claim (Table 3, LOL-v2-real): wrapping six other networks in HVIT/PHVIT raises PSNR
for all six (+0.381 to +3.562 dB); SSIM drops for SNR-Aware (-0.009) and LPIPS worsens for
FourLLIE (+0.011), so "improves across metrics" is not uniformly true in its own table.
Cross-dataset (Table 5, train LOL-v1 -> test LOL-v2-syn): CIDNet 19.457/0.817/0.193, but
only with the extra hue-bias mechanism (Eqs. 12-13) that the main model does not use;
without it 17.545 (Table 6).

### 2.4 Protocol as stated (§5.1, §10.2)

Adam (0.9, 0.999), lr 1e-4 -> 1e-7 cosine, "a single NVIDIA 2080Ti or 3090". LOL-v1 and
LOL-v2-real: 400x400 crops, 1,500 epochs, batch 8. LOL-v2-syn: batch 1, 500 epochs, no
crop. Test-time reflect-pad to a multiple of 8; GT-mean on LOL-v1 only (Eq. 21). Not
stated: augmentation, warm-up, gradient clipping, checkpoint-selection rule, seed. The code
defaults differ from the paper (crop 256, 1000 epochs, warm-up 3, clipping on).

---

## 3. What the paper ablates (every row, LOL-v2-real, PSNR / SSIM / LPIPS)

**Table 4 (main).** Color-space rows use a UNet + self-attention proxy, not CIDNet.

| group | row | PSNR | SSIM | LPIPS |
|---|---|---|---|---|
| color space | sRGB | 20.062 | 0.825 | 0.137 |
| | HSV | 21.349 | 0.801 | 0.167 |
| | HVI, polarization only | 21.558 | 0.821 | 0.149 |
| | HVI, C_k only | 21.536 | 0.825 | 0.179 |
| structure | UNet baseline | 19.306 | 0.778 | 0.222 |
| | + self-attention | 22.313 | 0.835 | 0.126 |
| | dual branch + self-attention | 23.159 | 0.856 | 0.116 |
| loss | HVI only | 23.221 | 0.854 | 0.132 |
| | sRGB only | 23.319 | 0.857 | 0.123 |
| full | HVI-CIDNet | 24.111 | 0.871 | 0.108 |

**Table 7 (LCA sub-modules):** no CAB 19.938/0.835/0.138; no IEL 22.647/0.855/0.126;
no CDL 22.324/0.847/0.136; all 24.111/0.871/0.108.
**Table 12 (what each branch sees):** Half-HVIT (I-branch <- I, HV-branch <- full HVI)
24.111/0.868/0.108; Separate (HV-branch <- HV only) 23.734/0.857/0.141; Full (both <- HVI)
23.814/0.859/0.127.
**Table 13 (no network; GT intensity substituted, mean PSNR over LOL-v1+v2):** HSV 14.346;
+polarization 20.632; +C_k 25.046; HVI 27.115.
**Table 6 (cross-dataset extras):** without Eqs. 12-13 17.545; Eq. 12 only 18.112; Eq. 13
only 18.458; both 19.457.
**Earlier version (2402.05809 v3, Table V):** the same ablation printed sRGB+LCA 18.606 and
HSV+LCA 13.237 PSNR on the same dataset; the final version prints 20.062 and 21.349. The
old loss ablation had HVI-only 22.113 vs the final 23.221. The old text explains the weak
HVI-only loss: "using only the HVI loss does not allow k to converge" because k sits in the
inverse transform between the two losses.

**Never ablated, in any version:** YCbCr / LAB / HSL / YUV under the same network (YCbCr
appears only through the Bread baseline); the value of k (fixed vs trainable, a sweep, or
the learned value per dataset); the choice of the collapse function F (sine vs linear vs
log, Eqs. 9-11, justified only by a gradient-stability argument); the HVI-loss weight
lambda_c; the edge and SSIM terms individually; alpha_S / alpha_I; depth, width or number
of LCA stages; epsilon; any seed.

---

## 4. What it leaves open

### 4.1 The paper's own list (§11 "Limitation and Unstudied issues", §8.2, §10.3)

- Whether a better collapse function than Eq. 9 exists.
- Only supervised training; unsupervised, semi-supervised and zero-shot untested.
- HVI and CIDNet cannot be trained separately (no ground truth exists in HVI).
- Other tasks: one SwinIR x2 super-resolution try gave +0.14 dB; nothing else.
- Replacing the Transformer with Mamba; use inside large vision models.
- The hue-bias parameters gamma_G, gamma_B cannot be set for an unknown camera.
- LPIPS is worse than GLARE on LOL-v2-real and worse than ZeroDCE cross-dataset; BRISQUE
  does not beat RetinexNet.

### 4.2 Our observations (gaps a careful reader sees; not claims)

1. **No seed spread anywhere.** Every ablation is a single run, and the differences it
   interprets are small: polarization-only vs C_k-only differ by 0.022 dB; HVI-only vs
   sRGB-only loss by 0.098 dB; the three Table 12 rows lie within 0.4 dB. The code draws an
   unlogged random seed per run. Whether any of these rows is distinguishable from noise is
   unknown. *This is the single largest open gap and is decidable with our compute.*
2. **Ablation numbers moved between versions** (HSV 13.237 -> 21.349; sRGB 18.606 ->
   20.062; HVI-only loss 22.113 -> 23.221) under the same stated protocol, and the full
   model's SSIM is 0.871 in Table 4 but 0.868 in Table 12, the old tables, and the README.
3. **One proxy network per color space.** The color-space ablation uses UNet+self-attention,
   not CIDNet, and compares only sRGB, HSV and two HVI halves. No YCbCr, LAB, HSL or YUV
   control; no "HSV with a wrap-aware hue loss" control. Polarization is a property of any
   cos/sin hue embedding (the paper concedes YCbCr already solves hue discontinuity), so the
   experiment does not isolate what HVI adds over a cheap fix.
4. **k is never studied.** Trainable k (init 0.2 in code, i.e. paper k = 5) is the one
   learned part of the "new color space", yet no fixed-k baseline, no sweep, no learned
   value is reported. Supplement figures show k in {1, 3, 10, 50} qualitatively only.
5. **Loss weights are unreported and partly unablated.** Five lambdas, none printed; the
   SSIM term appears only in the supplement; edge (weight 50 in code) and SSIM terms are
   never removed; lambda_c never swept. The VGG perceptual term is applied to HVI tensors
   with `H,V` in `[-1,1]` (code), which the paper does not discuss.
6. **The headline row mixes checkpoints** (perceptual on/off per column; §2.3). The old
   version disclosed this, the final one does not.
7. **Checkpoint selection on the test split** (code §1.4; README ships `best_PSNR`,
   `best_SSIM`, `best_GT_mean` weights for LOL-v2-real). Published numbers are therefore
   max-over-checkpoints on the test set. Any number we produce under a proper validation
   split will be lower, and that gap is itself a measurable quantity.
8. **C_k destroys dark chroma by construction** (chroma radius -> 0 as I_max -> 0, and the
   inverse divides by C_k + 1e-8). Framed as denoising; never tested on content where dark
   chroma matters; no color-fidelity metric (CIEDE2000, hue error) is reported despite the
   color-bias motivation. Only PSNR/SSIM/LPIPS/NIQE/BRISQUE.
9. **No robustness study.** No noise-level, JPEG, resolution, ISO or camera sweep; the one
   cross-dataset table uses a mechanism absent from the main model; random gamma is a
   training-time trick evaluated only with no-reference metrics.
10. **GT-mean** is a post-hoc brightness alignment applied to LOL-v1 only; the final version
    prints no LOL-v1 number without it.
11. **Efficiency is reported at one resolution** (256x256) and inference times in the
    plug-in table carry no hardware in the final version. Nothing on width/depth trade-off,
    and the shipped code has two asymmetries (§1.2) that no ablation covers.
12. **Invertibility was downgraded** from "one-to-one" (old) to "surjective" (final) with a
    clip set D (§10.2); the transform is not invertible near black.
13. **Code vs paper protocol mismatch** (crop 256 vs 400, 1000 vs 1500 epochs, clipping
    that is a no-op, warm-up unmentioned). "Reproducing the paper" and "running the code"
    are different experiments; the plan must name which one is the baseline.

### 4.3 What this means for candidate questions (for master; not a ranking)

Gaps 1, 3, 4, 5 and 7 are each decidable on four 2080 Ti with three seeds per cell and each
survives a negative result: "HVI is not distinguishable from YCbCr/HSV under the same
network at three seeds" is a thesis; so is "trainable k does not beat fixed k"; so is "the
published LOL-v1 number is X dB above what validation-based selection yields". Gap 8 needs
a color-fidelity metric and possibly data we do not have. Gap 9 needs extra datasets and
their checksums.

## 5. Closest related work (one line each; every entry verified in `custom.bib`)

*(filled after the citation-verification pass)*
