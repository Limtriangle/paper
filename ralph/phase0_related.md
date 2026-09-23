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
| P | `PerceptualLoss` (VGG19 conv1_2, conv2_2, conv3_4, conv4_4, MSE, `range_norm=True`) | `P_weight = 1e-2` | applied to both the RGB and the HVI tensor; input range shifted, see below |
| HVI | scalar | `HVI_weight = 1.0` | weight of the whole HVI-space sum |

- The released LOL-v1 weights come in two flavours, `w_perc.pth` and `wo_perc.pth` (README
  table); the README reports PSNR/SSIM/LPIPS for each with and without GT-mean rescaling.
- **Perceptual-loss input range** (`loss/vgg_arch.py` lines 228-231; confirmed in
  `phase0_codebase.json` facts.losses.Perceptual): the extractor is built with
  `range_norm=True`, so every input is mapped `x -> (x+1)/2` **before** ImageNet mean/std
  normalisation. For the HVI tensor (`H, V` in `[-1,1]`) this lands `H, V` in `[0,1]`, a
  valid image range. For the **RGB** tensor, already in `[0,1]`, it lands in `[0.5, 1]`: the
  RGB-side perceptual term sees a systematically brightened, contrast-halved image. The
  oddity is on the RGB side, not the HVI side. The paper does not mention `range_norm`.

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
  and 28.1405 / 0.8887 / 0.0988. A peer-trained LOL-v1 checkpoint is listed at 24.7401 PSNR
  on an RTX 4070 (third-party README claim, **unverified**, no paper). These are **the
  authors' numbers**; they never enter the paper as ours.
- The authors state that "some of the training parameters we are no longer able to provide"
  and that the weights are reproducible "by parameter tuning". Exact reproduction of the
  README numbers is therefore not guaranteed by the released config.
- Random gamma augmentation (added 2025-01) is claimed to improve cross-dataset
  generalisation, measured by NIQE (`mittal2013niqe`) and BRISQUE (`mittal2012brisque`) on the five unpaired sets DICM/LIME/MEF/NPE/VV [their dataset papers are
  **unverified**, no bib entries; the sets are named as the upstream README names them].
- Follow-up: HVI-CIDNet+ (`yan2025hvicidnetplus`, TCSVT 2026; arXiv 2507.06814), separate repo. The
  README also names FusionNet (`shi2025fusionnet`, CVPRW 2025) as the authors' NTIRE 2025
  LLIE challenge entry that fuses HVI-CIDNet with other models; the challenge report
  `liu2025ntire` lists it first.

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
for all six (+0.381 to +3.562 dB); SSIM drops for SNR-Aware (`xu2022snr`, -0.009) and LPIPS
worsens for FourLLIE (`wang2023fourllie`, +0.011), so "improves across metrics" is not
uniformly true in its own table.
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
inverse transform between the two losses. **This contradicts the code** (§1.1): `PHVIT` uses
`self.this_k`, a Python float captured by `k.item()` in the last forward call, so no gradient
reaches k through the inverse at all. In the released code k is trained only through the
forward `HVIT` calls (the HVI-space loss on `HVIT(output_rgb)` vs `HVIT(gt_rgb)`, and the
residual add); the RGB-space loss cannot move k. Whichever explanation is right, the paper's
stated mechanism is not the shipped one.

**Never ablated, in any version:** YCbCr / LAB / HSL / YUV under the same network (YCbCr
appears only through the Bread baseline `guo2023bread`); the value of k (fixed vs trainable, a sweep, or
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
- Other tasks: one SwinIR x2 super-resolution try gave +0.14 dB (`liang2021swinir`); nothing else.
- Replacing the Transformer with Mamba (cf. `weng2024mambaLLIE`); use inside large
  vision models.
- The hue-bias parameters gamma_G, gamma_B cannot be set for an unknown camera.
- LPIPS is worse than GLARE (`zhou2024glare`) on LOL-v2-real and worse than Zero-DCE
  (`guo2020zerodce`) cross-dataset; BRISQUE (`mittal2012brisque`) does not beat RetinexNet
  (`wei2018retinex`).

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
   control (YCbCr and YUV appear only inside other methods: Bread `guo2023bread` and
   LYT-Net `brateanu2025lytnet`); no "HSV with a wrap-aware hue loss" control. Polarization is a property of any
   cos/sin hue embedding (the paper concedes YCbCr already solves hue discontinuity), so the
   experiment does not isolate what HVI adds over a cheap fix.
4. **k is never studied.** Trainable k (init 0.2 in code, i.e. paper k = 5) is the one
   learned part of the "new color space", yet no fixed-k baseline, no sweep, no learned
   value is reported. Supplement figures show k in {1, 3, 10, 50} qualitatively only.
5. **Loss weights are unreported and partly unablated.** Five lambdas, none printed; the
   SSIM term appears only in the supplement; edge (weight 50 in code) and SSIM terms are
   never removed; lambda_c never swept. The VGG perceptual term's `range_norm` shifts the
   **RGB** input to `[0.5, 1]` before ImageNet normalisation (code, §1.3), which the paper
   does not discuss; the HVI input is the one that lands in a valid range.
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

## 5. Closest related work (one line each; every key exists in `custom.bib` and was verified)

Sources: the author's literature survey in `ralph/related/` (SURVEY.md, INDEX.md, slices A-F,
survey.bib, 103 entries) merged into `custom.bib` on 2026-09-23 after writing's own
verification pass (five subagents, one fetched page per entry: Crossref, CVF open access,
arXiv, OpenAlex, ACL Anthology, JMLR, MLSys, NeurIPS, IJCAI; DBLP and Semantic Scholar are
blocked from this host). 103/103 survey entries verified; corrections applied: Bread author
order (publisher: Guo, Hu), Retinexformer second author (Hao Bian), HVI-CIDNet+ is now IEEE
TCSVT 36(8) 2026 with a different author list from the arXiv v1, InterLight is IJCAI 2026,
Multinex is CVPR 2026, TPCNet is ECCV 2026 under a changed title, LHSI author order per the
WACV proceedings, Diffusion-in-the-Dark pages 4134-4145, PIRM publisher year 2019,
Zero-DCE++ print issue TPAMI 44(8) 2022, the two Pilligua keys merged into
`pilligua2025mill`. Still arXiv-only (venue claims not backed by a proceedings page):
`yang2026rhvifdd`, `yang2026cage`, `wu2026tcanet`, `yan2026yuvrevisit`, `bai2026logdomain`,
`ai2026bcihv`, `han2026clerwkv`, `li2026pal`, `du2026atp`, `pilligua2025mill`,
`shafi2026iphoneblur`, `ciubotariu2026ntire`, `yan2026ntireellie`. `cui2022iat`'s BMVC 2022
venue rests on the arXiv comment plus an indexed proceedings URL (site unreachable that day).

### 5.1 The HVI line itself
- `yan2025hvi` (CVPR 2025, pp. 5678-5687): the paper under study; §2-§4.
- `yan2024onecolorspace` (arXiv 2402.05809): earlier version; prints wP/oP and normal/GT-mean
  numbers separately and the numeric loss ablation the final version turned into a figure.
- `yan2025hvicidnetplus` (TCSVT 2026): adds vision-language priors and a region refinement
  block on top of HVI; its Table V is a single-run sRGB/HSV/HVI comparison on LOL-v1 (GT-mean).
- `shi2025fusionnet` (CVPRW 2025, NTIRE 2025 LLIE winner): linear fusion of CIDNet,
  Retinexformer and a CNN; states that a trainable k makes HVI data-dependent.
- `liu2024ntire`, `liu2025ntire`, `ciubotariu2026ntire`, `yan2026ntireellie`: the challenge
  reports (hidden test GT, composite PSNR/SSIM/LPIPS ranks); HVI entries rank 1st in 2025,
  4th-12th in 2026; zero-shot CIDNet scores 13.85 dB on NTIRE 2026 data (per the report).

### 5.2 Works that extend or criticise HVI (slice D)
- `yang2026rhvifdd` (arXiv): max-RGB intensity is sensitive to positive noise spikes; robust
  HVI plus a DCT decoupling module; single-run HSV/HVI/RHVI comparison.
- `ai2026bcihv` (arXiv): replaces the linear intensity by a learnable Box-Cox law for a
  rectified-flow enhancer; no sRGB/HSV/YCbCr arm.
- `wu2026tcanet` (arXiv): argues the weak point is the two-stream fusion, not the color
  representation; thresholded cross-attention.
- `cheng2026vcr` (TCSVT 2026): channel-level luminance/chrominance inconsistency in HVI
  methods; variance-guided channel recalibration; HVI vs HSV only.
- `wang2026haimnet` (TIP 2026): replaces the CIDNet interaction with attention modulation and
  gated affine fusion; 11 datasets.
- `wang2026interlight` (IJCAI 2026): intrinsic illumination priors and sensor-level augmentation.
- `shi2025tpcnet` (ECCV 2026): Kubelka-Munk physical constraints; single-run HVI/LAB/YCbCr on
  LOL-v2-real with YCbCr ahead (24.98 vs 24.64 dB, as printed there).
- `han2026clerwkv` (arXiv): controllable enhancement conditioned on target luminance; uses
  HVI for noise-decoupled supervision.
- `li2026pal` (arXiv) and `du2026atp` (arXiv): per-pair photometric inconsistency dominates
  pixel losses; retrained CIDNet at 23.97 dB on LOL-v1 without GT-mean (their number).
- `pilligua2025mill` (arXiv): CIDNet degrades sharply when input brightness moves off the
  training distribution (26.4 -> 17.7 dB at a 20% blend toward GT, their numbers).
- `brateanu2026multinex` (CVPR 2026): calls HVI's learnable mappings data-dependent and
  unstable; multi-prior Retinex alternative.
- `he2025dlfenet` (Sensors 2025), `verma2025qcidnet` (CVPRW 2025), `lin2025jarvisir`
  (CVPR 2025): reuse CIDNet as a module (detail/noise branches, video quality, autonomous
  driving restoration).
- `cheng2026lhsi` (WACV 2026): a learnable HSI space for white-balance editing, the nearest
  "learned polar color space" outside LLIE.

### 5.3 Color-space and decomposition approaches (slice A)
- `land1977retinex`: the Retinex decomposition every Retinex-family method invokes.
- `guo2023bread` (IJCV 2023): luminance/chrominance split with the enhanced luminance guiding
  a chrominance mapper; YCbCr-like; the closest two-branch, two-space precedent.
- `brateanu2025lytnet` (SPL 2025): fixed YUV split, lightweight Y and UV paths with cross-fusion.
- `zhang2022dccnet` (CVPR 2022): gray image plus an explicit color histogram, re-injected
  through a pyramid color embedding.
- `li2021ucolor` (TIP 2021): RGB, HSV and Lab encoded jointly with attention (underwater).
- `guan2025cstnet` (NeurIPS 2025): a learnable YCbCr-like converter for nighttime deraining,
  the closest Tier-1 "learnable color space" idea.
- `wu2026catformer` (TCSVT 2026): learnable per-pixel von Kries adaptation then CIELAB.
- `yan2026yuvrevisit`, `bai2026logdomain`, `yang2026cage` (arXiv): YUV frequency analysis,
  log-domain intensity/chroma decoupling, adaptive LAB with saturation rectification.
- `chobola2024colie` (ECCV 2024): implicit neural illumination in HSV, zero-reference.
- `cui2022iat` (BMVC 2022), `wang2022lcdpnet` (ECCV 2022): sRGB with a learned global color
  matrix/gamma, and local color-distribution priors.
- `ma2022csdnet` (TNNLS 2022): context-sensitive Retinex decomposition, two streams.
- `smith1978hsv` (SIGGRAPH 1978): the HSV definition.

### 5.4 Canonical deep LLIE 2017-2022 (slice B)
- `lore2017llnet` (PR 2017): the first deep LLIE autoencoder.
- `wei2018retinex` (BMVC 2018): RetinexNet and LOL-v1 (485/15).
- `yang2021lolv2` (TIP 2021): LOL-v2 real (689/100) and synthetic (900/100).
- `zhang2019kind` (ACM MM 2019), `zhang2021kindpp` (IJCV 2021): illumination/reflectance
  branches; KinD++ adds multi-scale illumination attention.
- `wang2019deepupe` (CVPR 2019): predicts an illumination map from expert-retouched pairs.
- `yang2020drbn` (CVPR 2020): recursive band network, semi-supervised.
- `xu2020fide` (CVPR 2020): frequency-based decomposition and enhancement.
- `guo2020zerodce` (CVPR 2020), `li2021zerodcepp` (TPAMI 2022): zero-reference curves and
  the 10K-parameter version; the color-constancy loss lives here.
- `jiang2021enlightengan` (TIP 2021): unpaired adversarial training.
- `zamir2020mirnet` (ECCV 2020): multi-resolution streams with selective fusion.
- `liu2021ruas` (CVPR 2021), `wu2022uretinex` (CVPR 2022), `ma2022sci` (CVPR 2022):
  Retinex unrolling with NAS, Retinex unfolding, self-calibrated illumination.
- `xu2022snr` (CVPR 2022): SNR-routed transformer/CNN, a plug-in host in HVI-CIDNet Table 3.
- `wang2022llflow` (AAAI 2022): conditional normalizing flow; strong GT-mean baseline.
- `zamir2022restormer` (CVPR 2022), `wang2022uformer` (CVPR 2022), `chen2022nafnet`
  (ECCV 2022), `liang2021swinir` (ICCVW 2021): the restoration backbones; Restormer's MDTA +
  GDFN is what the LCA block in CIDNet follows.

### 5.5 Deep LLIE 2023-2025, non-HVI (slice C)
- `cai2023retinexformer` (ICCV 2023): the size-matched Retinex transformer baseline (1.53M
  vs 1.88M params); its README documents the GT-mean test option and advises against it.
- `yi2023diffretinex` (ICCV 2023), `hou2023gsad` (NeurIPS 2023), `yin2023clediffusion`
  (ACM MM 2023), `jiang2024lightendiffusion` (ECCV 2024), `lan2025efficientdiffusion`
  (CVPR 2025): the diffusion line; GSAD is the LPIPS competitor in Table 1.
- `fu2023pairlie` (CVPR 2023): self-supervised from pairs of low-light shots.
- `liang2023cliplit` (ICCV 2023), `yang2023nerco` (ICCV 2023), `wu2023skf` (CVPR 2023),
  `xu2023smg` (CVPR 2023): CLIP prompts, implicit neural fitting, semantic guidance,
  structure modeling.
- `wang2023llformer` (AAAI 2023): UHD benchmark and axis-based transformer.
- `shi2024zeroig` (CVPR 2024), `wang2024quadprior` (CVPR 2024): zero-shot and zero-reference
  with physical priors.
- `weng2024mambaLLIE` (NeurIPS 2024): state-space backbone (the "Mamba" the paper names as
  future work).
- `zhou2024glare` (ECCV 2024): codebook retrieval; beats HVI-CIDNet on LOL-v2-real LPIPS.
- `yu2024lmtgp` (ECCV 2024): semi-supervised mean teacher.
- `zhang2025cwnet`, `sun2025retinev`, `wang2025bridge` (ICCV 2025): causal wavelets, event
  cameras, unsupervised fine-tuning of generative priors.

### 5.6 Evaluation methodology, reproducibility, statistics (slice E)
- `li2022llie` (TPAMI 2022), `liu2021benchmarking` (IJCV 2021), `zhao2025lowlightvision`
  (TNNLS 2025): surveys and benchmarks; metric rankings disagree across families.
- `nguyen2024diffusiondark` (WACV 2024): documents LOL train/test scene overlap and the
  brightness gap between train and test GT (supplement S3.2).
- `pilligua2025mill` (arXiv): LOL-type sets fix one brightness per scene; multi-intensity test.
- `liao2025gtmean` (ICCV 2025): defines brightness mismatch and moves GT-mean into training.
- `wang2009mse` (SPM 2009): why PSNR/MSE punish global intensity shifts people barely see.
- `wang2004ssim`, `zhang2018lpips`, `mittal2013niqe`, `mittal2012brisque`, `blau2018pirm`:
  SSIM, LPIPS, NIQE, BRISQUE, and the perception-distortion index.
- `sharma2005ciede2000`: CIEDE2000, the color-fidelity metric the paper does not report.
- `bouthillier2021variance` (MLSys 2021), `pineau2021reproducibility` (JMLR 2021): variance
  from seeds and hyperparameters changes benchmark conclusions; the reproducibility checklist.
- `musgrave2020reality` (ECCV 2020): test-set model selection inflates reported progress.
- `recht2019imagenet` (ICML 2019): test-set reuse and adaptive overfitting.
- `shafi2026iphoneblur` (arXiv): a restoration benchmark that reports mean +- SD over three
  seeds (0.2-0.4 dB PSNR spread, their numbers).
- `dror2018hitchhiker` (ACL 2018), `koehn2004bootstrap` (EMNLP 2004): paired significance
  tests and bootstrap resampling for small test sets (15 images).

### 5.7 Losses and architectures (slice F)
- `johnson2016perceptual` (ECCV 2016), `ledig2017srgan` (CVPR 2017): VGG perceptual loss.
- `zhao2017loss` (TCI 2017): L1/L2/SSIM/MS-SSIM comparisons; loss-weight sensitivity.
- `lai2017lapsrn` (CVPR 2017), `zamir2021mprnet` (CVPR 2021), `afifi2021exposure`
  (CVPR 2021): Laplacian-pyramid and edge losses of the kind CIDNet's E term uses.
- `jo2020investigating` (CVPRW 2020): LPIPS as a training loss and weight sensitivity.
- `peng2023ushape` (TIP 2023): the one precedent for one composite loss duplicated across RGB
  and a second color space (Lab/LCH, underwater).
- `zamir2020mirnet`, `zamir2022restormer`, `wang2022uformer`, `chen2022nafnet`,
  `liang2021swinir`: backbones (listed in 5.4).
- `chen2018sid` (CVPR 2018), `zhou2022lolblur` (ECCV 2022), `cai2018sice` (TIP 2018): the
  other paired datasets HVI-CIDNet reports on.

### 5.8 Also verified (comparators from the paper's tables, not in the survey)
- `wang2023fourllie` (ACM MM 2023): Fourier-frequency enhancement; plug-in host in Table 3.
- `feng2024difflight` (CVPRW 2024): the same group's diffusion enhancer; plug-in host in Table 3.

### 5.9 Still without a verified entry
- The five unpaired sets DICM, LIME, MEF, NPE, VV (dataset papers not in the survey); the
  third-party 24.7401 dB README row (no paper exists).
