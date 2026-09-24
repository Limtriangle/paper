# M1 novelty check: exposure-conditioned HVI

Search date: 2026-09-24. Method: targeted web searches only (arXiv abstract and HTML pages, CVF, GitHub README). I did not read the full PDFs of every paper, so each claim below is only as reliable as the page it came from.

## Verdict

**INCREMENTAL.** The general idea of conditioning on or normalising exposure is already taken. Closest works: MILL (arXiv 2511.15496, intensity-prediction and scene-invariance losses on a multi-intensity benchmark), ENC (CVPR 2022, exposure normalisation plus compensation), and CLE-RWKV (arXiv 2603.25296, an HVI-based network with FiLM on a brightness scalar).
I found no paper that predicts the HVI transform's own parameters (k, gain, gamma) per image from input statistics, or that wraps HVIT and PHVIT in an exposure normalise/invert step. BC-IHV and HVI-CIDNet+ keep the intensity law global.
The contribution is defensible only as "input-adaptive HVI plus measured robustness under exposure shift", and it has to beat plain random-gamma augmentation (already in the upstream repo) and MILL's losses.

## Closest works

| Paper | Venue, year | What they condition or adapt | Evaluated on brightness shift? | How M1 differs | Link |
|---|---|---|---|---|---|
| MILL: Evaluating LLIE Across Multiple Intensity Levels | arXiv 2025-11 (v2 2026-04) | Latent channel 0 is supervised to predict normalised scene lux (intensity-prediction loss); a triplet "scene content" loss makes the remaining channels illumination-invariant | **Yes**: 11 lux levels per scene, the LOL-v1 GT-blend study, CIDNet included; reports up to +10 dB (DSLR) | M1 changes the colour transform itself (HVI k, gain, gamma) or normalises the input. MILL shapes the features through losses and is not HVI-specific. This is the conceptual overlap to address head-on | https://arxiv.org/abs/2511.15496 |
| ENC: Exposure Normalization and Compensation | CVPR 2022 | Feature-level exposure normalisation to an exposure-invariant representation, plus a compensation branch | Yes: multi-exposure correction (MSEC/SICE-style under and over exposure) | ENC normalises features. M1 normalises input intensity before HVIT and inverts after PHVIT. This is the closest prior work for the "canonical exposure" idea | https://openaccess.thecvf.com/content/CVPR2022/html/Huang_Exposure_Normalization_and_Compensation_for_Multiple-Exposure_Correction_CVPR_2022_paper.html |
| CLE-RWKV + Light100 (controllable LLIE) | arXiv 2026-03 | Target-brightness scalar beta goes through an embedding and MLP into FiLM on features. Supervision in HVI space. The HVI transform itself is not conditioned | Dataset has 100 illumination levels per scene. No reported input-exposure robustness comparison with CIDNet | Their condition is the output target brightness, supplied by the user. M1's condition is an estimate of the input exposure, and M1 adapts HVI's k | https://arxiv.org/abs/2603.25296 |
| BC-IHV: Box-Cox learnable polar colour space | arXiv 2026-08 | A single global learnable Box-Cox exponent (not per image). The "HybridAda" bottleneck applies global exposure modulation via AdaLN on features | No: only LOL splits and DICM/LIME | M1 makes the intensity law itself input-conditioned. BC-IHV's AdaLN exposure modulation is a close cousin and must be cited | https://arxiv.org/abs/2608.21847 |
| HVI-CIDNet+ | arXiv 2025-07 | Adds VLM priors. k remains global | No | M1 predicts k (and gain) per image | https://arxiv.org/abs/2507.06814 |
| HVI-CIDNet repo: random-gamma mode | GitHub 2025 (CVPR 2025 code) | Random-gamma training augmentation. The README reports 7 metrics improve for LOLv2-syn "generalization.pth" | Cross-dataset only, not multi-intensity | Augmentation only, with no conditioning. **This is the baseline M1 must beat** | https://github.com/Fediory/HVI-CIDNet |
| IllumFlow | arXiv 2025-11 | Conditional rectified flow over illumination (Retinex), with adjustable brightness | Claims adaptation across lighting conditions. Protocol unclear | Heavy generative model. M1 is a small plug-in to HVI | https://arxiv.org/abs/2511.02411 |
| InterLight | IJCAI 2026 | Adaptive prompts conditioned on latent illumination state, plus a self-supervised illumination-invariance consistency loss | Not explicitly reported | Similar "illumination-aware modulation" idea at the feature and prompt level. Not HVI | https://arxiv.org/abs/2605.19982 |
| ControlLight (Light100K) | arXiv 2026-05 | Enhancement strength s scales LoRA on FLUX.2 | No: consistency is across s, not across input exposures | Target control rather than input-exposure robustness | https://arxiv.org/abs/2605.25569 |
| BP-Net / ACT-Net (Brightness Perceiving Recursive LLIE) | IEEE TAI 2023 (arXiv 2025) | A brightness-perception net predicts the number of recursive enhancement iterations from the input brightness distribution | Implicitly (wide dynamic range) | Brightness estimate sets iteration count, not the colour-space parameters | https://arxiv.org/abs/2504.02362 |
| AutoLumNet | arXiv 2026-08 | Predicts a per-image global monotone tone curve plus a local residual. Handles under and over exposure | Yes: MSEC, SICE, LCDP, and LOL zero-shot | A per-image global curve is essentially M1's "gain+gamma" component. M1 adds HVI k and a CIDNet backbone | https://arxiv.org/abs/2608.19860 |
| CAGE (AdaLAB / AdaCCT) | ACM MM 2026 | Image-specific cylindrical colour space. Adaptive chroma shift and scale with lightness compensation | No | Adapts the colour-space basis per image from chroma statistics. This is the closest "image-adaptive colour space" precedent, but it is not exposure-driven | https://arxiv.org/abs/2608.10512 |

## The strongest baseline M1 must beat

The strongest baseline is CIDNet trained with the upstream random-gamma (and brightness-jitter) augmentation, using the same augmentation budget as M1 and no conditioning. If augmentation alone closes most of the multi-intensity gap, M1's module adds nothing.
The second baseline is CIDNet plus MILL's intensity-prediction and triplet losses, since these are the published fix for exactly this failure.
A zero-parameter wrapper should also be reported: scale the input so that mean(I) matches the LOL-v1 training mean, run frozen CIDNet, then invert.

## A version of M1 that would be clearly novel

The novel version is a per-image HVI transform. A tiny network reads intensity histogram statistics and outputs k(x), plus a gain and gamma applied inside HVIT, with an exact inverse in PHVIT. It is trained with a consistency loss: the same scene at different input exposures should map to the same HVI chroma and the same output.
It should come with an analysis showing why a fixed global k collapses when the input is brighter (C_k saturates, so the chroma scale changes), and how conditioning k removes that collapse.
Evaluation should use MILL's 11 levels, LOL-v1 GT-blends and SICE, reporting both the worst-level and the mean PSNR.

## Cheapest experiment that decides it

Train four CIDNet variants on LOL-v1 for about 300 epochs: (a) vanilla, (b) random-gamma/gain augmentation, (c) augmentation plus the fixed mean-intensity normalise/invert wrapper, (d) augmentation plus predicted k/gain/gamma (M1).
Test all four on LOL-v1 blended toward GT at alpha in {0, 0.1, 0.2, 0.35, 0.5}, plus gain-scaled inputs in {0.5x, 2x, 4x}, and zero-shot on SICE and LOL-v2-real.
M1 is worth pursuing only if (d) beats (b) and (c) by at least 1 dB at the worst brightness level while staying within 0.3 dB on standard LOL-v1. If (c) is already as good, M1 reduces to a preprocessing trick.
