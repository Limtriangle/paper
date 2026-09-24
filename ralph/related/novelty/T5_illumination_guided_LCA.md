# T5 — Illumination/SNR-guided LCA cross-attention in HVI-CIDNet

## Verdict: INCREMENTAL
Closest work: **CMIG-Net** (arXiv 2608.01886, "Beyond Illumination: A Conditional Mutual Information-Guided Network for LLIE"). Its CMIC module already computes a per-pixel "reliability of chrominance given intensity" map and uses it to rescale HV features and steer inter-branch attention in D2IR — the same causal slot the proposal wants an illumination/SNR map to fill.
No paper found explicitly multiplies CIDNet's LCA queries/values by a Retinexformer-style illumination map or an SNR-Aware-style SNR map; CMIG-Net uses conditional mutual information instead, and TCA-Net/WIRNet gate attention by confidence/learned gates, not by an explicit darkness/SNR prior. So the exact IG-MSA-style mechanism is unclaimed, but the darkness-conditioned-fusion idea itself is already occupied.

## Closest works

| Paper | Venue/Year | What it does | Link |
|---|---|---|---|
| CMIG-Net | arXiv 2026 (2608.01886) | CMIC computes a conditional-mutual-information map Mcmi(u) quantifying chrominance reliability given intensity; rescales HV input (HV'=HV⊙s) and D2IR uses the CMI prior to guide inter-branch attention | https://arxiv.org/abs/2608.01886 |
| TCA-Net | arXiv 2026 (2607.13925) | Thresholded Cross-Attention prunes cross-stream (I/HV) attention by a fixed confidence threshold (post-softmax), input/layer-adaptive; DDSGM subtracts chromaticity-correlated component from I-feature at reconstruction stage, not inside attention | https://arxiv.org/abs/2607.13925 |
| HAIMNet | IEEE TIP 2026 | Inter-branch attention-modulation block (IAMB) with bidirectional attention + adaptive modulation across scales between luminance/chromaticity branches in HVI space | https://doi.org/10.1109/tip.2026.3714857 |
| WIRNet | NTIRE 2026 challenge report | Gated LCA: a learned gate reweights LCA's attention-branch features (denoising focus); gate is not explicitly an illumination/SNR map | https://arxiv.org/pdf/2605.02212 |
| ICLR (Inter-Chrominance/Luminance Interaction) | arXiv 2025 (2511.13607) | DIEM fuses I/HV via channel-spatial-pixel attention (MAFM) + dynamic weighting (CDEM); adds a Covariance Correction Loss instead of an illumination-gated attention term | https://arxiv.org/abs/2511.13607 |
| LCCNet | Multimedia Systems 2026 | Luminance-chroma collaborative cross-attention for LLIE (abstract only reachable; mechanism not confirmed as illumination/SNR-gated) | https://link.springer.com/article/10.1007/s00530-026-02618-x |
| HVI-CIDNet+ | arXiv 2025 (2507.06814) | Extends original LCA/HVI pipeline for extreme darkness, but no confirmed illumination-map-conditioned attention | https://arxiv.org/abs/2507.06814 |
| Retinexformer (IG-MSA) | ICCV 2023 | Illumination representation from ORF directly modulates self-attention (the mechanism being transplanted) | (prior art, outside HVI) |
| SNR-Aware | CVPR 2022 | SNR map gates spatial-varying attention/convolution selection | (prior art, outside HVI) |

## Baseline to beat
CIDNet's plain LCA (Restormer-style channel cross-attention, no darkness conditioning) **and** CMIG-Net's CMIC/D2IR (conditional-information-guided fusion) on the same LOLv1/v2, Sony-Total-Dark, and NTIRE-2026 splits CMIG-Net/TCA-Net/WIRNet already report on.

## Cheapest deciding experiment
Take released CIDNet code, replace each LCA's attention (or just its HV-branch query projection) with `Attn = softmax(QK^T/√d ⊙ σ(W·I_map))` where `I_map` is the existing I-branch feature (zero new learned parameters beyond a 1×1 gate), train/eval on LOLv1 + Sony-Total-Dark, and report ΔPSNR/ΔΔE in the darkest-decile pixels (by I_map value) plus overall PSNR/SSIM, directly against reported CIDNet and CMIG-Net numbers — this isolates whether explicit I/SNR-gated attention beats CMIG-Net's mutual-information-gated version at near-zero param cost.

## Locus where it should help
Darkest regions / lowest local-SNR patches specifically in the HV (chroma) branch's cross-attention step inside each of the six LCA blocks — i.e., color accuracy (ΔE) and chroma-texture fidelity conditioned on per-pixel darkness, not global PSNR.
