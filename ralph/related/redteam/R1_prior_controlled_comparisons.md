# R1 - Red team: has C1 (matched-network, multi-seed color-space comparison) already been done?

Checked 2026-09-24 with targeted web searches and full-text fetches of arXiv HTML. Numbers below are copied from the papers' HTML versions. Anything I did not open myself is marked "not verified".

## Verdict

**PARTIALLY DONE, not redundant.** The HVI authors already ran "same CIDNet, only the color space changes" twice: CVPR 2025 Table 4 (LOLv2-Real) and HVI-CIDNet+ Table V (LOLv1). Both are single runs with no seeds, no validation split and no YCbCr row.
Strongest evidence against redundancy: those two tables disagree with each other. HSV beats sRGB in PSNR on LOLv2-Real (21.35 vs 20.06) but loses on LOLv1 (25.86 vs 27.26). An independent same-backbone study (HVD-Net, Sci. Rep. 2026) ranks HVI below HSV, HSL and LCH. So the ranking is not settled, and a seed-spread test is exactly what is missing.
No paper found in any restoration task reports seed-level variance for a color-space ablation. The closest analysis is BC-IHV (arXiv, Aug 2026), which gives a gradient-conditioning theory but also uses single runs.

## Closest prior work

| Paper | Venue, year | Task | What was compared | Same network? | Seeds? | Conclusion | Link |
|---|---|---|---|---|---|---|---|
| Yan et al., HVI: A New Color Space for LLIE | CVPR 2025 | LLIE | sRGB / HSV / HVI (polarization only) / HVI (C_k only) / full HVI, Table 4, LOLv2-Real | Yes (CIDNet) | No. Single run, test set only. Protocol: "performed on LOLv2-Real for fast convergence and stable performance" | PSNR 20.06 / 21.35 / 21.56 / 21.54 / 24.11. Full HVI wins by about 2.5 dB over the best ablation | https://arxiv.org/abs/2502.20272 |
| Yan, Shi, Feng et al., HVI-CIDNet+ | arXiv 2507.06814 (journal extension of CVPR'25; the TCSVT acceptance is not stated on the arXiv page, not verified) | LLIE | sRGB / HSV / HVI (pol. only) / HVI (C_k only), Table V, LOLv1 | Yes (CIDNet) | No | PSNR 27.26 / 25.86 / 27.79 / 27.99. Text: HSV "significantly deteriorate[s]" | https://arxiv.org/abs/2507.06814 |
| Zhang et al., HVD-Net | Scientific Reports 2026 | LLIE | YUV / LAB / HVI / LCH / HSL / HSV (sin-cos hue), Table 4, LOLv2-Real | Yes ("same dual-branch backbone ... only the input layer adjusted") | No | PSNR 28.37 / 28.37 / **28.69** / 28.77 / 28.92 / 29.00. HVI ranks below HSV variants. The spread is about 0.6 dB | https://pmc.ncbi.nlm.nih.gov/articles/PMC13442834/ |
| Yan, Liu et al., Revisiting Lightweight LLIE: From a YUV Color Space Perspective | arXiv Jan 2026 (no venue stated) | LLIE | R-GB / G-RB / B-GR / Y-UV channel splits, Table 4, LOL | Yes | No | YUV beats the RGB splits by about 0.5 dB. Also gives a frequency analysis: Y loses low-frequency content, UV carries high-frequency noise | https://arxiv.org/abs/2601.17349 |
| Ai, Chen, Cai, Zhang, Yang, BC-IHV | arXiv Aug 2026 | LLIE (rectified flow) | HVI / Log-IHV / learnable Box-Cox IHV, Table 3, LOLv2-Real | Yes (SA-RF) | No (inference uses seed 0 only) | BC-IHV is 1.67 dB above HVI. Argues that the color space's inverse Jacobian sets the gradient dynamic range | https://arxiv.org/abs/2608.21847 |
| Guan et al., CST-Net (nighttime deraining) | NeurIPS 2025 | Deraining | RGB / HSV / HSL / YUV / YCbCr, fixed vs learnable converter, Table 4 | Yes | No | YCbCr fixed 39.60 vs RGB 38.75. Learnable YCbCr reaches 40.50 | https://arxiv.org/abs/2510.17440 |
| Dong et al., SRCNN (journal version) | TPAMI 2016 | Super-resolution | Y only / YCbCr / Y pre-train / CbCr pre-train / RGB, Table 5, Set5 x3 | Yes | No | Joint YCbCr training is worst. RGB is best, but the gain over Y-only is "marginal (0.07 dB)". This is the classic "color space barely matters for a linear transform" data point | https://arxiv.org/abs/1501.00092 |
| Li et al., Ucolor | TIP 2021 | Underwater | Multi-encoder: without HSV, without Lab, 3xRGB | Partly (encoder paths removed) | No | 3xRGB is about equal to removing HSV+Lab. Multi-space helps. This is not a single-space swap | https://arxiv.org/abs/2104.13015 |
| Gowda & Yuan, ColorNet | ACCV 2018 | Classification | 7 color spaces, same DenseNet | Yes | No (not verified) | Color space changes accuracy, and an ensemble helps | https://arxiv.org/abs/1902.00267 |
| Karargyris, Color Space Transformation Network | arXiv 2015 | Classification | Learnable 3x3 color transform as a 1x1 layer | n/a | n/a | A linear color transform is just a learnable 1x1 layer (basis for the triviality argument) | https://arxiv.org/abs/1511.01064 |
| Liao et al., GT-Mean Loss | ICCV 2025 | LLIE | Brightness-mismatch loss and evaluation | n/a | Search snippet says a sigma study used 3 seeds but reported only curves (not verified) | Relevant to how C1 handles GT-mean | https://arxiv.org/abs/2507.20148 |

No LLIE "reality check" or "reproducibility study" with multi-seed LOL numbers turned up. Seed-variance reports in restoration do exist in other tasks: a 2026 deblurring benchmark reports 0.2-0.4 dB PSNR std across seeds (iPhoneBlur, arXiv 2605.05990, not opened), and arXiv 2504.06629 (training dynamics of restoration transformers) shows large run-to-run PSNR discrepancy (venue not verified). I found no master's thesis on LLIE color spaces (KAIST, SNU, GIST, ETH, TUM); the search was shallow.

## The triviality argument

- **For triviality.** A fixed invertible linear transform such as RGB to YCbCr is exactly a 1x1 convolution plus bias. If the network's first and last layers are linear, the function class is identical in RGB and YCbCr (Karargyris 2015; the CST idea). SRCNN (TPAMI 2016) found the empirical difference between color strategies to be tiny, apart from a training-difficulty effect. Prediction under this view: **sRGB and YCbCr should be indistinguishable within seed noise.** If C1 finds that, the result is expected, not novel.
- **What breaks it, even for linear maps.** The same function class does not mean the same optimization. SGD and Adam are not invariant to input reparameterization, and input decorrelation or whitening changes conditioning (LeCun et al., "Efficient BackProp", 1998). Initialization, normalization layers and weight decay also interact with the basis. If the loss is computed in the transformed space, the loss geometry changes too: an L1 in YCbCr is a different metric from an L1 in RGB.
- **What breaks it for HSV and HVI (nonlinear).**
  - HSV hue has a 0/2π discontinuity at red and is undefined when S=0 or V=0 (the "red and black noise" in the HVI paper). HVD-Net (2026) fixes this with a sin-cos hue encoding.
  - HVI uses C_k to collapse chroma near black, making the map one-to-one, but the inverse map is then ill-conditioned near black.
  - BC-IHV (2026) formalizes this: dL/dI = dL/dv * dv/dI. The inverse derivative range is κ(λ) = ((1+ε)/ε)^(1-λ), so the color space sets the gradient dynamic range. In their Fig. 4, log-IHV has a 1001x range and learned BC-IHV a 12x range.
  - Consequently, HSV and HVI can matter, but they can also hurt through optimization rather than representation.
- **CIDNet-specific trap.** CIDNet's loss is computed in both HVI and sRGB spaces (CIDNet+ text), and the architecture has separate I and HV branches. So "swap only the color space, loss frozen" is not a clean single-variable change. C1 must say whether the HVI-space loss term is swapped to the new space or kept.

## What HVI-CIDNet's authors already did

- **CVPR 2025, main paper, Table 4 (LOLv2-Real)**, PSNR / SSIM / LPIPS:

  | Space | PSNR | SSIM | LPIPS |
  |---|---|---|---|
  | sRGB | 20.062 | 0.825 | 0.137 |
  | HSV | 21.349 | 0.801 | 0.167 |
  | HVI (polarization only) | 21.558 | 0.821 | 0.149 |
  | HVI (C_k only) | 21.536 | 0.825 | 0.179 |
  | Full HVI | 24.111 | 0.871 | 0.108 |

  - Single run, no seeds, no validation split described, and no YCbCr row despite the paper arguing against YCbCr in the text.
  - Supplementary Table 6 ablates the P_γ and T(·) extensions (train on LOLv1, test on LOLv2-Syn: 17.55 to 19.46 PSNR).
  - I could not open the CVF supplementary PDF (HTTP 403); I relied on the arXiv v2 HTML.
- **HVI-CIDNet+ (arXiv 2507.06814), Table V (LOLv1)**:

  | Space | PSNR | SSIM | LPIPS |
  |---|---|---|---|
  | sRGB | 27.259 | 0.874 | 0.0735 |
  | HSV | 25.857 | 0.862 | 0.1007 |
  | HVI (polarization only) | 27.788 | 0.878 | 0.0795 |
  | HVI (C_k only) | 27.989 | 0.883 | 0.0733 |

  - The same table also has "HVI Only" 28.102 and "sRGB Only" 28.316 (probably loss-space or branch ablations; the meaning is unclear from the fetch), plus the CIDNet baseline at 28.075.
  - No seeds or std, and no statement on checkpoint selection.
- **GitHub README:**
  - Test-time `--use_GT_mean` is optional ("Following LLFlow, KinD, and Retinexformer").
  - No seed control.
  - No released code for the sRGB or HSV variants.
  - Nothing about which epoch is reported. The common LLIE practice is picking the best epoch on the test set; this was not verified for this repo.
- **Inconsistency to exploit:**
  - sRGB vs HSV flips sign between the two tables (+1.29 dB for HSV on LOLv2-Real, -1.40 dB on LOLv1).
  - Full HVI's margin in CVPR Table 4 (+2.55 dB over the best ablation) is far larger than the ablation-to-ablation gaps in CIDNet+ Table V (about 0.2 to 0.7 dB).
  - Without seeds, it cannot be told which differences exceed noise.

## What remains genuinely open

1. Whether any color-space gap in the same CIDNet exceeds seed-to-seed spread, with validation-based checkpoint selection. Nobody reports this in LLIE or in any restoration task.
2. A YCbCr row in CIDNet: never run by the authors. It is the linear control that separates "decoupling luminance" from "HVI's nonlinearity".
3. HVI minus C_k (the density term) under a controlled protocol, beyond the single-run LOLv2-Real row.
4. Whether the HVI and HSV rankings are stable across datasets. The published single runs already flip.
5. Whether gaps survive with and without the GT-mean correction. Brightness mismatch may dominate the PSNR differences.

## What would make C1 trivial

- If all five spaces fall within seed spread, the result matches the linear-reparameterization expectation (SRCNN's 0.07 dB). It stays publishable only as a negative or robustness result, not as a new finding.
- If the loss is kept in HVI+sRGB for every variant, differences may reflect a loss-space mismatch rather than the color space. Reviewers would call that confounded.
- If only LOL-v1 is used (15 test images), a gap could be dismissed as test-set noise. Report per-image paired differences or a bootstrap too.
