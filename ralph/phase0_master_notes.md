# phase0_master_notes.md — master's scouting notes (subagent reads of the upstream code; NOT ground truth — experiment's phase0_codebase.json is)

Upstream HEAD eb43d7d. Facts to cross-check against ralph/results/phase0_codebase.json before use.

## HVI transform (net/HVI_transform.py)
- H,S standard HSV; I = max(R,G,B). k is a learnable nn.Parameter(0.2) (reciprocal of paper's k).
- C = (sin(πV/2)+1e-8)^k; H = C·S·cos(2πh), V = C·S·sin(2πh).
- Inverse divides by C using a stored float (no grad to k through inverse). Near black C≈(1e-8)^0.2≈0.025 → H/V errors amplified ~40× then hidden by clamp; atan2(eps,eps) → arbitrary 45° hue. **Candidate: near-black failure mode.**
- Hidden test-time knobs: `gated` (S×1.3, on for LOLv1 eval), `gated2`/alpha (RGB×0.8–0.84 for LOLv2-real), user gamma for unpaired sets.

## Network (net/CIDNet.py, net/LCA.py)
- Two 3-level U-Nets (HV branch 3→2 ch, I branch 1→1), residual + inverse. 6 HV_LCA + 6 I_LCA (transposed channel cross-attention + gated FFN). channels=[36,36,72,144], heads=[1,2,4,8].
- Wiring oddities: LCA2 outputs only reach skips (L94-95); I_LCA5 output overwritten (L109) → dead compute.

## Loss (train.py, losses.py, options.py)
- Same four terms in RGB and HVI: L1 (1.0), 1−SSIM (0.5), edge/Laplacian (50), VGG perceptual (0.01). total = rgb + 1.0·hvi. **Corrected by phase0_codebase.json:** the perceptual loss applies range_norm x→(x+1)/2 before ImageNet normalisation, so the RGB branch is fed in [0.5,1] (shifted) while HVI lands in [0,1]; the oddity is on the RGB side.
- No per-dataset configs; README admits some training params lost.
- Learnable k receives gradient through HVIT(gt) too → model can shrink HVI loss by collapsing chroma. **Candidate: k dynamics / fixed vs learned k.**

## Protocol (options.py, train.py)
- 1000 epochs, batch 8, crop 256, flips, Adam 1e-4, 3-epoch warmup then cosine to 1e-7. Grad clipping is a no-op (runs before backward).
- Seed is random.randint, never logged; single run, no error bars.
- **Every 10 epochs the code evaluates the checkpoint on the TEST split (eval15) with gated=True (1.3× saturation).** The code does not pick a checkpoint itself; the released names best_PSNR/best_SSIM imply manual selection on those test scores. Our protocol carves a 50-image val split from our485 (seeded shuffle, sha256-pinned) and never opens eval15 outside final_eval_test.py (integrity rule 4).
- Epoch 1 trains at lr=0 (warmup bug); the paper's protocol (1500 epochs, 400² crops) differs from the code's (1000, 256). Measured params 1,975,569 incl. the dead I_LCA5 (70,960 never receive a gradient).
- GT-mean rescaling moves LOLv1 23.8→27.7 dB. Test-set finetuning reported in README.

## Data on disk
- Only LOLv1 (485 train / 15 eval). No checkpoints on disk. Others (LOLv2 real/syn, SICE, SID, LOL-Blur, unpaired DICM/LIME/MEF/NPE/VV) need download + checksum log.

## Literature scout (subagent with web access, 2026-09-23; every citation must be re-verified by writing before it enters custom.bib)
- Paper: Yan et al., CVPR 2025, arXiv 2502.20272 (earlier 2402.05809). Claims HVI fixes HSV red-discontinuity + black-plane noise; CIDNet 1.88M params / 7.57 GFLOPs; paper protocol 1500 epochs, batch 8, 400² crops.
- Ablations: LOLv2-Real only, single numbers: sRGB 20.06 / HSV 21.35 / polarization-only 21.56 / C_k-only 21.54 / full 24.11; loss space HVI 23.22 / sRGB 23.32 / both 24.11. No k sweep, no loss-weight sensitivity, no seeds/variance anywhere.
- GT-mean gap on LOLv1: 23.81 normal vs 27.71 GT-mean (GT-Mean Loss, Liao et al. ICCV 2025, arXiv 2507.20148; critique arXiv 2603.25296).
- Follow-ups: HVI-CIDNet+ (arXiv 2507.06814); RHVI-FDD (arXiv 2604.05781: max-RGB intensity is noise-sensitive); BC-IHV (arXiv 2608.21847: learnable Box-Cox exponent replaces fixed intensity law); DLFE-Net (Sensors 2025, doi 10.3390/s25175353: hue flips near black). None ablates the color space with seeds.
- GitHub issues: #160 LOLv1 not reproducible (closed unanswered), #162 LOLv2-Real 23.89 vs 24.11, #163 how loss weights were chosen. No independent seeded reproduction found.
- Prior color-space LLIE: Bread (YCbCr, IJCV 2023), LYT-Net (YUV, SPL 2025, arXiv 2401.15204), "Revisiting lightweight LLIE: YUV" (arXiv 2601.17349, YUV vs RGB only), DCC-Net (CVPR 2022, multi-space). Every paper compares its own space in its own network; no neutral comparison under one fixed network with seeds.
- Scout's feasibility ranking: (1) controlled color-space comparison ≥3 seeds; (2) seed variance + test-selection bias; (3) k sweep + near-black; (4) loss ablation with seeds; (5) noise/JPEG robustness per space.
