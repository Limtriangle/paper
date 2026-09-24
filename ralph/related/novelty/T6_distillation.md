## Verdict: NOVEL-IN-HVI (thin margin)
Distillation-for-LLIE is a populated niche (DLIENet, "LLIE with KD" 2022, MirrorDistill 2026) and luma/chroma-split *architectures* exist (LYT-Net, Bustaaa, Xie_Liu HE-Net in NTIRE'26), but **no found work distills specifically in HVI space with separate intensity/chroma distillation losses**, and NTIRE-2026 E-LLIE explicitly reports **no team used knowledge distillation**. Closest work: **MirrorDistill** (illumination-weighted latent distillation, LOL-v1/2, 4.38 GMACs) — same problem/datasets, no HVI, no color-space-split loss, no HVI-CIDNet+ teacher.

## Closest works
| Paper | Venue/Year | What | Link |
|---|---|---|---|
| MirrorDistill | arXiv 2026 (Sep) | EMA teacher (clean-ref decoder) → student (low-light decoder) latent distillation, illumination-weighted; LOL-v1/v2; 4.38 GMACs, SOTA PSNR | arxiv.org/html/2609.25331 |
| DLIENet | Pattern Recognition 2025 | Pretrained teacher → lightweight student; distills bottleneck features + content-attention maps; no color-space split | doi.org/10.1016/j.patcog.2025.111777 |
| "Low-Light Image Enhancement with Knowledge Distillation" (Li/Wang) | Neurocomputing 2022 | Early teacher-student LLIE KD baseline | sciencedirect.com/science/article/abs/pii/S0925231222013674 |
| HVI-CIDNet+ | arXiv Jul 2025 (venue on arXiv page not confirmed as TCSVT 2026) | Adds VLM priors (Prior-guided Attention Block) + Region Refinement Block to CIDNet; candidate teacher | arxiv.org/abs/2507.06814 |
| HVI-CIDNet | CVPR/NTIRE 2025 | ~1.9M param base network in HVI space; distillation target/student backbone | github.com/Fediory/HVI-CIDNet |
| sysu_701 (NTIRE'26 E-LLIE) | NTIRE 2026 workshop | Lightweight HVI-CIDNet variant, dual HV/I branch + cross-attn, reduced U-Net depth, 965K params, no distillation reported | arxiv.org/html/2605.02212v1 |
| Cidaut AI (NTIRE'26 E-LLIE) | NTIRE 2026 workshop | CIDNet w/ NAFBlock-inspired NIEL block, HVI space, 797K params, no distillation | arxiv.org/html/2605.02212v1 |
| NCHU-CVLab "Efficient-HVI" (NTIRE'26 E-LLIE) | NTIRE 2026 workshop | HVI-based dual branch, cross-branch interaction, 957K params, no distillation | arxiv.org/html/2605.02212v1 |
| Bustaaa (NTIRE'26 E-LLIE) | NTIRE 2026 workshop | LYT-Net-style YUV dual-branch (luma/chroma separate), MHSA, 205K params | arxiv.org/html/2605.02212v1 |
| Xie_Liu HE-Net (NTIRE'26 E-LLIE) | NTIRE 2026 workshop | LAB space, refines L channel, lightweight residual chroma reconstruction, 913K params | arxiv.org/html/2605.02212v1 |

## Baseline to beat
Small HVI-CIDNet (or width-reduced variant) trained without distillation, at matched param budget (<1M, per NTIRE'26 E-LLIE track) on LOL-v1/v2; also compare against MirrorDistill's reported numbers (LOL-v2-Real: 24.08 dB PSNR / 0.864 SSIM at 4.38 GMACs) as the strongest distillation baseline in the space, and against sysu_701/Cidaut/Efficient-HVI (non-distilled HVI variants, ~0.8-1M params) from the NTIRE'26 factsheets.

## Cheapest deciding experiment
Precompute HVI-CIDNet+ (or CIDNet+Retinexformer ensemble) teacher outputs once on LOL-v1/v2 train sets (intensity map I and chroma map HV separately). Fine-tune a width-reduced CIDNet student for a few minutes with three loss variants: (a) intensity-only distillation, (b) chroma-only distillation, (c) both. Compare PSNR/SSIM/ΔE deltas on LOL-v1/v2 test vs the no-distillation baseline — this alone answers "does intensity or chroma knowledge transfer" and whether the split beats a single combined sRGB distillation loss (the ablation no cited work reports).

## Locus where it should help
Chroma distillation should matter most on **extremely dark / near-zero-intensity pixels** (the regime HVI's learnable-intensity compression and HVI-CIDNet+'s "Beyond Extreme Darkness" framing target) where the student's own chroma branch has the least signal to learn from directly — i.e., dark-region color-artifact suppression on LOL-v2-Real and any extreme-low-light subset, not overall PSNR.
