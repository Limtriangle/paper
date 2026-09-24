# T4: Learned Multi-Task Loss Weighting for HVI-CIDNet — Novelty Check

## Verdict: NOVEL-IN-HVI
No paper found applies uncertainty weighting, GradNorm, or dynamic weight averaging to HVI-CIDNet's dual-space loss, nor to any LLIE loss (hand-tuned weights are the norm; HVI-CIDNet+ keeps the same fixed λ scheme). Closest work is generic: Kendall/Gal/Cipolla (uncertainty weighting) and GradNorm (2018) are the source techniques being transplanted, not prior art in this domain; "Uncertainty-Driven Loss for SISR" (NeurIPS 2021) is the nearest in-domain analog but weights *pixels*, not loss *terms*, and targets super-resolution, not LLIE.
The idea sits at the intersection of two established techniques (MTL loss weighting) and one specific under-justified system (HVI-CIDNet's λ + fixed 1/0.5/50/0.01 weights) — an application/transplant novelty, not a new algorithm, and evidence from other domains (e.g., an image-restoration report that GradNorm underperformed hand-tuned weights) tempers the "faster convergence, better PSNR" claim.

## Closest Works

| Paper | Venue/Year | What it does | Link |
|---|---|---|---|
| Kendall, Gal & Cipolla, "Multi-Task Learning Using Uncertainty to Weigh Losses..." | CVPR 2018 | Homoscedastic uncertainty weighting — learns per-task σ_k, source technique T4 proposes to transplant | arxiv.org/abs/1705.07115 |
| Chen et al., "GradNorm: Gradient Normalization for Adaptive Loss Balancing" | ICML 2018 | Balances multi-task loss via gradient-norm equalization | arxiv.org/abs/1711.02257 |
| Liu et al. (MTAN), Dynamic Weight Averaging | CVPR 2019 | Weights tasks by rate of loss decrease (forward-pass only, no gradients) | proceedings CVPR 2019 |
| Groenendijk et al., "Multi-Loss Weighting with Coefficient of Variations" | WACV 2021 | Alternative learned weighting scheme, applied broadly (not LLIE) | arxiv.org/abs/2009.01717 |
| Ning et al., "Uncertainty-Driven Loss for Single Image Super-Resolution" | NeurIPS 2021 | Per-pixel uncertainty-weighted loss for SISR — closest in-domain (restoration) uncertainty-weighting use, but weights pixels not loss terms, and task is SR not LLIE | proceedings.neurips.cc/paper/2021/.../88a199... |
| Zhou et al., "Random Weights Networks Work as Loss Prior Constraint for Image Restoration" | 2023 (arXiv) | Different adaptive-loss idea (plug-in random-weight network as a loss prior); evaluated on denoising, LLIE, guided SR | arxiv.org/abs/2303.16438 |
| Yan et al., "HVI: A New Color Space for Low-light Image Enhancement" (HVI-CIDNet) | CVPR 2025 | Candidate baseline: fixed λ scalar between HVI-space and sRGB-space losses, each = L1+0.5·SSIM+50·edge+0.01·VGG, hand-tuned, unexplained per GitHub issue #163 | arxiv.org/abs/2502.20272; github.com/Fediory/HVI-CIDNet |
| "HVI-CIDNet+: Beyond Extreme Darkness for Low-Light Image Enhancement" | 2025 (arXiv) | Follow-up to HVI-CIDNet adding VLM-guided attention + region refinement; keeps the same fixed dual-space λ loss structure (no evidence of learned/adaptive weighting or VGG-term change found) | arxiv.org/abs/2507.06814 |
| Toledo-Marín et al./others, AHU-MultiNet | 2022, ScienceDirect | Homoscedastic-uncertainty adaptive loss balancing, but for multi-task *medical segmentation*, not restoration/enhancement | sciencedirect.com S0010482522008654 |

No hits for: GradNorm/DWA/uncertainty-weighting specifically inside any LLIE paper; any paper altering HVI-CIDNet's dual-space weight or dropping/replacing its HVI-space VGG term; a published loss-weight sensitivity/ablation study in LLIE beyond routine single-value ablations (e.g., trying {0.5,1,2,10,15}) that don't examine learned weighting.

## Baseline to Beat
HVI-CIDNet (CVPR 2025) official config: L = L_rgb + 1.0·L_hvi, each L = L1 + 0.5·SSIM + 50·edge + 0.01·VGG (VGG applied to non-RGB HVI tensor), fixed hand-set weights, reported PSNR/LPIPS on LOLv1/v2/etc. as published.

## Cheapest Deciding Experiment
Swap only the loss-weighting mechanism (keep architecture, data, schedule fixed): train HVI-CIDNet with (a) homoscedastic uncertainty weighting over the 2 spaces (or 8 terms) and (b) same but drop/replace the HVI-space VGG term with an HVI-appropriate term (or remove it). Compare PSNR/LPIPS/SSIM and convergence-epoch-to-target-PSNR against the fixed-weight baseline on LOLv1/LOLv2-real/-synthetic. This isolates the claimed gain (equal/better metrics, faster convergence) from the architecture, and is cheap since it reuses the released codebase and only touches the loss function (~1 file).

## Locus Where It Should Help
The dual-space balance term λ (currently fixed at 1.0) and the within-space term weights (0.5/50/0.01) — particularly the HVI-space VGG term, which is applied to a non-photometric tensor and is the most conceptually suspect fixed choice (flagged in GitHub issue #163). A time-resolved log of the learned weights would let the "which space dominates training over time" study fall out directly as a byproduct of the uncertainty/GradNorm weights themselves.
