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

## 2. What the paper claims (CVPR 2025, arXiv 2502.20272)

*(filled from the fetched paper; see §2.x below)*

## 3. What the paper ablates

*(filled from the fetched paper)*

## 4. What it leaves open

*(filled: paper's own limitations, then our observations)*

## 5. Closest related work (one line each; every entry verified in `custom.bib`)

*(filled after the citation-verification pass)*
