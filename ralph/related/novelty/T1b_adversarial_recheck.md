# T1b Adversarial novelty recheck: hue-equivariant chroma branch for LLIE/restoration

Date: 2026-09-24. Method: ~16 targeted web searches (arXiv, CVF, OpenReview, Springer, Semantic Scholar API) covering queries (1) to (7) in the brief. Semantic Scholar cited-by for CEConv (arXiv 2310.19368) was only partly retrieved: 8 arXiv-indexed citers, then HTTP 429 on the full list.

## Verdict
CLAIM HOLDS (with the caveat that search coverage is incomplete, not exhaustive).
I found no work that uses hue/color-equivariant, steerable, or phase-equivariant complex convolutions in any LLIE, restoration, denoising, colorization, WB, or compression network on a polar or 2-D chroma representation, and none that does so in HVI-CIDNet.
Every color-equivariant network found is for classification, segmentation, or illuminant estimation. Every equivariant restoration network found is spatially (rotation/flip/crop) equivariant, not hue-equivariant.

## Everything found

| Paper | Venue, year | Task | Equivariant to what | Color representation | Link |
|---|---|---|---|---|---|
| Color Equivariant Convolutional Networks (CEConv) | NeurIPS 2023 | Classification | Discrete hue rotation (about RGB gray diagonal) | RGB | https://arxiv.org/abs/2310.19368 |
| Learning Color Equivariant Representations (earlier title "Color Equivariant Network") | ICLR 2025 | Classification, plus fg/bg segmentation (Caltech-101) | Hue (SO(2)), saturation and luminance shifts via a lifting layer | HSL | https://arxiv.org/abs/2406.09588 |
| A Hypertoroidal Covering for Perfect Color Equivariance | arXiv 2026 | Fine-grained classification, medical imaging | Exact hue cyclic group, plus saturation/luminance translation | HSL/hypertorus | https://arxiv.org/abs/2603.04256 |
| Co-domain Symmetry for Complex-Valued Deep Learning | CVPR 2022 | Classification (MSTAR, CIFAR, SVHN) | Complex scaling (phase), meaning hue shift in a complex color encoding | Complex-valued RGB encoding | https://arxiv.org/abs/2112.01525 |
| Illuminant Equivariant Networks for Computational Color Constancy | ECCV 2024 | Illuminant estimation (outputs a vector, not an image) | Illuminant (diagonal photometric) transforms | RGB / chromaticity | https://link.springer.com/chapter/10.1007/978-3-031-72845-7_18 |
| Long Scale Error Control in LL Image/Video Enhancement Using Equivariance | arXiv 2022 | LLIE | Spatial cropping/scale (not color) | RGB | https://arxiv.org/abs/2206.01334 |
| A Regularization-Guided Equivariant Approach for Image Restoration (EQ-Reg) | CVPR 2025 | Deraining, denoising, CT artifacts | Spatial rotation (the "cyclic channel shift" is the group-channel shift, not RGB) | RGB | https://arxiv.org/abs/2505.19799 |
| Equivariant Denoisers for Image Restoration / for PnP (ERED, EPnP) | 2024 / JMIV 2026 | PnP restoration | Spatial rotations/flips | RGB | https://arxiv.org/abs/2412.05343 |
| Aligning Network Equivariance with Data Symmetry (IR) | arXiv 2026 | Image restoration | Spatial (adaptive) | RGB | https://arxiv.org/abs/2605.13744 |
| Rotation-Equivariant Self-Supervised Image Denoising | arXiv 2025 | Denoising | Spatial rotation | RGB | https://arxiv.org/abs/2505.19618 |
| HVI / HVI-CIDNet, HVI-CIDNet+ | CVPR 2025 / arXiv 2025 | LLIE | None (HV polarization is a representation only) | HVI | https://arxiv.org/abs/2502.20272 |
| CAGE (color debiasing and saturation rectification) | arXiv 2026 | LLIE | None (adaptive, non-equivariant) | Adaptive color transform | https://arxiv.org/abs/2608.10512 |
| HVD-Net | Sci. Rep. 2026 | LLIE | None (continuous sin/cos hue encoding) | HSV cos/sin hue | https://www.nature.com/articles/s41598-026-47297-w |
| QMFINet (quaternion wavelet) | IEEE journal 2025 | Color denoising | None formal (quaternion phase consistency) | Quaternion RGB | https://ieeexplore.ieee.org/document/11122611/ |
| Other CEConv citers (CLIPSym, DaD, Transformation Laws, etc.) | 2025–2026 | Symmetry detection, keypoints, theory | Not about color restoration | – | via Semantic Scholar |

## Closest miss
Co-domain Symmetry (CVPR 2022) builds phase-equivariant complex layers where the complex phase encodes hue, which is the same mechanism the claim covers, but it is used only for classification. Learning Color Equivariant Representations (ICLR 2025) has an SO(2) hue-equivariant GCNN, but it is used only for classification and segmentation.
Both leave the claimed gap open: the claim still holds for dense image-to-image restoration/LLIE on a chroma-plane (HVI/HSV/Lab/CbCr) branch.
