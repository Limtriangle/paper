# M2 — Spatially adaptive / noise-aware HVI density: novelty check (2026-09-24)

## Verdict
**INCREMENTAL** (not taken, but not conceptually new). No HVI derivative found (CIDNet+, BC-IHV, RHVI-FDD, TCA-Net, VCR, InterLight, CAGE, UCAMNet, HAIMNet, DLFE-Net) makes k / C_k per-pixel or noise-aware; all keep ONE global k.
Closest works: **RHVI-FDD (arXiv 2604.05781)**, which feeds a per-pixel denoised intensity I' into the unchanged C_k, so the collapse is already implicitly spatial; **BC-IHV (arXiv 2608.21847)**, which uses a global Box-Cox λ with closed-form inverse conditioning; and **CAGE/AdaLAB (ACM MM 2026)**, which applies lightness-conditioned chroma scaling predicted once per image.
The idea itself, per-pixel chroma attenuation driven by luminance plus a noise/high-frequency proxy, is standard ISP "chroma suppression" (US 9142012 family). For novelty, the contribution has to be the invertible-encoding and conditioning angle plus the dark-bin colour evidence, not "adaptive desaturation of dark pixels."

## Closest works

| Paper | Venue, year | What is adaptive, and how | Dark bins evaluated? | How M2 differs | Link |
|---|---|---|---|---|---|
| HVI / CIDNet (Yan et al.) | CVPR 2025 | One learnable scalar k in C_k=(sin(πI/2)+ε)^k, shared by all pixels and images | No (global PSNR/SSIM/LPIPS) | Makes k a per-pixel field k(x) conditioned on I, S and σ; adds a conditioning bound | https://arxiv.org/abs/2502.20272 |
| HVI-CIDNet+ | arXiv 2507.06814 (2025) | k stays global and C_k is unchanged. Adaptivity is only in features (VLM-prior attention PAB, region-refinement RRB for info-scarce areas) | No | M2 moves adaptivity into the colour transform itself, where CIDNet+ keeps it in the network | https://arxiv.org/abs/2507.06814 |
| RHVI-FDD | arXiv 2604.05781 (2026) | Per-pixel Illumination Refinement Module (1x1 conv + 5x5 DW conv) replaces the noisy Max-RGB I. C_k and k unchanged, so the collapse becomes spatially smoothed only through I' | No (global metrics only) | **Closest.** M2 adapts the exponent/shape, not just the input intensity, and conditions on saturation and noise. Needs an ablation "I-refinement only vs k(x)" | https://arxiv.org/abs/2604.05781 |
| BC-IHV | arXiv 2608.21847 (Aug 2026) | Learnable global Box-Cox λ∈[0.05,1] on intensity; closed-form inverse-gradient dynamic range κ_I(λ). k inherited from HVI | Partly: brightness-bin mass and derivative histograms, but no hue or ΔE per bin | Shares M2's "keep the inverse well-conditioned" story, but globally and on I, not on chroma. M2 = per-pixel and on chroma collapse | https://arxiv.org/abs/2608.21847 |
| CAGE (AdaLAB + AdaCCT), Yang et al. | ACM MM 2026 (arXiv 2608.10512) | Image-adaptive cylindrical LAB: hue shift and chroma scaling predicted from a 128x128 thumbnail, piecewise over lightness intervals ("lightness sensitivity vertices"). Invertible. Built on CIDNet (+1.22 dB LOLv1) | No hue/ΔE; PSNR/SSIM/LPIPS only | Lightness-conditioned chroma gain already exists here, but it is **global per image** and not noise-aware. M2 = per-pixel, noise-conditioned, HVI-native | https://arxiv.org/abs/2608.10512 |
| TCA-Net | arXiv 2607.13925 (2026) | Confidence threshold on HVI cross-stream attention (I and HV fusion); no change to C_k | No | Confidence is on attention, not on chroma encoding | https://arxiv.org/abs/2607.13925 |
| VCR | arXiv 2603.10975 (2026) | Variance-driven **channel** masking between I and HV features; C_k global | No | Channel-level vs M2's pixel-level colour-space adaptivity | https://arxiv.org/abs/2603.10975 |
| InterLight | arXiv 2605.19982 (2026) | Illumination priors in network; HVI k global (Eq. 1 unchanged) | No | No colour-space change | https://arxiv.org/abs/2605.19982 |
| Log-domain ICD ("Rethinking LLIE…") | arXiv 2605.02627 (2026) | Replaces HVI with log intensity + log-ratio chromaticity to cut chromatic noise amplification at the representation level; no per-pixel parameter | No | Alternative representation (a baseline for "representation-level chroma-noise control"); not adaptive | https://arxiv.org/abs/2605.02627 |
| UCAMNet | Springer LNCS chapter, 2025 | Unsupervised HVI; variance/uncertainty constrains the **I** branch; attention for colour | No | Uncertainty on intensity, not on chroma collapse | https://link.springer.com/chapter/10.1007/978-981-95-6957-1_22 |
| ISP chroma suppression / CNR (patent family) | US 9142012, US 9710896 (2015–2017) | Per-pixel Cb/Cr attenuation gain in [0,1] from a LUT indexed by luminance Y, times a second factor from luminance high-frequency (a noise/edge proxy); plus aggressive chroma NR in low light | N/A | **Conceptual precedent:** luminance- and HF-dependent per-pixel chroma attenuation. M2 differs only by being learned, inside an invertible polar encoding, and trained end-to-end | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9142012 |
| CST-Net (learnable CSC) | NeurIPS 2025 | Learnable colour-space converter (toward YCbCr-like Y) plus implicit illumination guidance, for night deraining; global learned matrix/1x1 conv | No | Linear, not per-pixel collapse, different task | https://arxiv.org/abs/2510.17440 |

Also checked, not closer: HAIMNet, DLFE-Net (Sensors 2025), HVD-Net (Sci. Rep. 2026, HSV sin/cos hue + chroma-denoise branch), UCSC (arXiv 2508.04176, entropy uncertainty in features), and Multinex (CVPR 2026, analytic priors). None changes k spatially. Per-pixel learned curves exist in RGB (Zero-DCE, CVPR 2020) and spatial-aware 3D LUTs exist (ICCV 2021), so "per-pixel learned transform parameter" alone is not novel.

## The strongest baseline M2 must beat
1. **RHVI-style intensity refinement with global k.** A per-pixel denoised I' fed into the original C_k already gives a spatially varying collapse. M2 must beat CIDNet+IRM at equal parameters on dark-decile hue error and ΔE00.
2. **Post-hoc luminance/HF chroma-suppression LUT.** This is the ISP baseline: gain(Y, |∇Y|) applied to HV before decoding, with 2–3 learned scalars. If it matches M2 in the dark deciles, M2 has no case.
Also report CAGE (global lightness-conditioned chroma scaling) if its code is available.

## A version of M2 that would be clearly novel
Frame k(x) as a **per-pixel, noise-calibrated collapse with a provable condition-number bound**. Predict k(x) from I, S and a physically calibrated noise estimate σ(I) (Poisson-Gaussian, or the LOLv2 noise statistics). Constrain C_{k(x)}(I) ≥ c·σ(I)/I, so that inverse amplification of chroma noise is bounded per pixel; this extends BC-IHV's global κ analysis to a spatial field.
Show that this yields a Wiener-like chroma shrinkage inside an exactly invertible encoding, and introduce a **dark-decile hue/ΔE00 protocol** (currently reported by no HVI paper) as a secondary contribution.

## Cheapest experiment that decides it
On LOLv2-Real with a fixed CIDNet backbone and seed, train 4 variants for about 100 epochs: (a) global k; (b) global k + RHVI-style IRM on I; (c) global k + luminance/HF chroma-gain LUT; (d) M2 k(x) with bound. Report PSNR plus hue error and ΔE00 per intensity decile (use GT-intensity bins).
M2 is worth pursuing only if (d) beats both (b) and (c) by a clear margin (for example ≥0.5 ΔE00 or ≥2° hue) in deciles 1–2 at equal global PSNR (±0.1 dB) across 3 seeds. Otherwise drop it or fold it in as an ablation.
