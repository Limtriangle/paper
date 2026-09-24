# R6 — Red-team of T4 "Learned dual-space loss weighting" (HVI-CIDNet)

## Verdict

1. As framed ("learned weights give equal-or-better PSNR/SSIM/LPIPS with no hand tuning"), the claim cannot really be proven wrong. With 3 seeds on 15 near-duplicate test images, the smallest detectable effect is about 0.6–0.7 dB, and the 50-epoch fine-tune loop cannot test weighting at all. The likely result is a null that noise can make look like a win or a loss.
2. On these 16 terms, homoscedastic-uncertainty weighting reduces to "divide each term by its running magnitude" (w_i -> 1/L_i). It wipes out the hand-set x50/x0.01 scales, and its weight trajectories follow mechanically from that. "Which term dominates" needs gradient attribution, not learned weights.
3. Reframe it as a controlled, seeded study of CIDNet's dual-space loss: replicate the RGB/HVI ablation, test removing the HVI-VGG term, add gradient-share attribution, and compare learned vs. hand-tuned vs. equal-compute random search, all from scratch (about 420 GPU-h, which fits one week on 4x2080Ti). That can be defended as a B.Sc. thesis whatever the numbers say. The "method beats SOTA loss" framing cannot.

---

## Assumptions used for all numbers
- Full from-scratch run (1000 ep, LOL-v1) = 9 GPU-h. Nominal budget 4 GPUs x 7 d = 672 GPU-h; plan for ~75 % utilisation (~500 GPU-h).
- Seed-to-seed σ of LOL-v1 test PSNR is **assumed** to be 0.25–0.4 dB. This is based on the 23.5–24.0 third-party spread, plus the well-known epoch-to-epoch jitter on 15 images. **Measure it in Phase 0. Every power statement below depends on it.**
- MDE for a two-arm, 3-vs-3 seed comparison (α=0.05 two-sided, 80 % power) ≈ 2.8·σ·√(2/3) ≈ 0.57–0.91 dB.

---

## 1. Falsifiability and triviality

**Attack.** "Equal-or-better" is satisfied by any point estimate within noise, so there is no outcome that counts against it. Learned weights also tend to end up in one of two places. Either they settle near a magnitude-balancing ratio, which is not the same as the hand ratio but is equally unremarkable, or they collapse one term (uncertainty weighting sends s_i -> -inf on a term whose loss goes to ~0). "Dual-space" is also not multi-task learning. HVI = HVIT(RGB) is a deterministic, differentiable, near-invertible function of the same prediction against the same target. The task-conflict premise behind Kendall and GradNorm mostly does not hold. Reweighting here re-shapes a per-pixel error metric; it is not a way of arbitrating between tasks.

**Consequence.** With 3 seeds the likely outcomes are "+0.1 dB, n.s." or "−0.1 dB, n.s.". Neither supports a method claim. A "trajectory analysis" of weights that simply track 1/L_i says nothing about the model.

**Fix.** Pre-register the outcomes and what each one means:

| Outcome | Informative? | Claim allowed |
|---|---|---|
| O1: learned − hand within ±0.2 dB on scene-disjoint val, and σ_seed small enough that the 90 % CI of the difference fits within ±0.3 dB | Yes (equivalence) | "Undocumented hand weights are replaceable at no cost" |
| O2: learned > hand by ≥ MDE on val **and** LOL-v1 test **and** GT-mean PSNR | Yes (positive) | Method claim |
| O3: learned < hand by ≥ MDE | Yes (negative; matches GradNorm-in-restoration reports) | "Hand weights encode real prior; MTL weighting fails on redundant objectives" |
| O4: collapse or blow-up of a weight (clamp hit, s_i at bound) | Yes (diagnostic) | Pathology of MTL weighting on correlated same-target losses |
| Point estimate better, CIs overlap, weights ≈ 1/L_i | **Trivial** | Nothing beyond "no difference detected" |

Replace the "equal-or-better" wording with a formal equivalence test (TOST, margin 0.3 dB) plus a superiority test. Name the primary learned method in advance.

## 2. Scale confounds and interpretability of "dominance"

**Attack.** Kendall: L = Σ exp(−s_i)·L_i + s_i. At the stationary point exp(−s_i) = 1/L_i, so every weighted term contributes ≈1 whatever its hand multiplier was. Placing learned weights on top of the hand weights (w_i·L_i) means the hand weight is absorbed at equilibrium. So "learned" ≈ "EMA loss-magnitude normalisation", a deterministic, parameter-free rule. It also pushes weight toward whichever term has the smallest loss (1−SSIM ≈ 0.1, the small Laplacian residuals), which is the opposite of "importance". Kendall's likelihood derivation only applies to L1/L2 (Laplace/Gaussian). It has no meaning for SSIM, edge, or VGG terms. Adam is invariant to the overall scale of the loss, so only relative weights matter, and those follow magnitudes. GradNorm balances gradient norms at one chosen layer and has α. DWA has a temperature T. Both are tuned hyperparameters, so "no hand tuning" is rhetoric.

**Consequence.** A plot of learned weights over time is a plot of 1/L_i(t). "Edge dominates" or "HVI dominates" can't be read from it. A win for Kendall is also indistinguishable from a win for plain magnitude normalisation.

**Fix.**
- Add arm **EMA-norm**: w_i(t) = 1/EMA(L_i). This is the deterministic twin of Kendall. If Kendall ≈ EMA-norm (weight correlation > 0.95, ΔPSNR n.s.), report that Kendall reduces to it.
- Define dominance by **gradient share**, not weight. Every K=500 steps, compute per-term gradients g_i of w_i·L_i on the shared parameters (a full backward per term, 16 extra backwards every 500 steps, <3 % overhead). Report share_i = ⟨g_i, g⟩/‖g‖², which sums to 1. Also report the pairwise cosine matrix cos(g_i, g_j) and the RGB-vs-HVI block cosine. Repeat with the Adam-preconditioned direction g_i/(√v̂+ε), because that is what actually moves the weights.
- Run this logging on **every** arm, including hand-tuned. The measurement chapter then does not depend on the learned-weight method working.
- Clamp s_i ∈ [−5, 5] and log how often the clamp is hit; clamp hits count as outcome O4.

## 3. Fine-tuning from converged weights

**Attack.** Near a converged minimum all terms are small and jointly near-stationary. Fifty epochs of re-weighting move the solution very little. Any change mostly comes from (a) extra training and a learning-rate restart, and (b) the start checkpoint. The released checkpoint was very likely picked as the best test epoch, so every fine-tune starts from a test-selected point. Uncertainty and DWA weights also need warm-up. They are initialised from converged losses and so start in their equilibrium regime, with no trajectory to analyse.

**Consequence.** The fine-tune loop cannot show that weighting matters. A positive fine-tune delta will most likely be "trained 50 more epochs with a fresh LR".

**Fix.** Use fine-tuning **only** as a smoke test of the code, with a matched control: continue with hand weights for 50 ep, same LR schedule, 3 seeds each (≈2.5 GPU-h total). All claims come from **from-scratch** runs. Short proxy schedules (300 ep with the LR schedule *compressed*, not truncated, ≈2.7 h) are allowed only for screening random-search configs, and only after checking that proxy ranking matches full-schedule ranking on the Phase-0/1 arms (kill criterion K6). Budget: see the revised design, ≈420 GPU-h, which fits.

## 4. The VGG-on-HVI term

**Attack.** (H, V, I) shifted to [0,1] and fed to an ImageNet VGG as if it were RGB gives features with no semantic grounding. The term still acts as a generic multi-scale nonlinear feature-matching loss, and such losses work to some degree even with random networks. It is also redundant with RGB-VGG through the invertible transform. If T4 bundles "learned weights" with "drop HVI-VGG", any gain is confounded.

**Consequence.** Dropping the term may explain all of an observed gain, or none of it. Either way you can't attribute it without a factorial design. On its own it is the cheapest and clearest finding in the proposal: one arm, 27 GPU-h, and it saves a VGG forward/backward per step. Measure the wall-clock saving; do not assume it.

**Fix.** Use a 2x2 factorial: {hand, primary-learned} x {with, without HVI-VGG}. If "hand − HVI-VGG" matches or beats hand-tuned within noise, report "a conceptually unjustified term can be removed at no cost, saving X % time". That is a clean negative-control result. Do not "replace" the term with anything new; that would add an untested degree of freedom.

## 5. Baselines

**Attack.** "No hand tuning" only competes against the *cost* of hand tuning. The real competitor is a tuning procedure given equal compute, not the upstream weights. Also, "uniform = all 1" on raw terms makes the Laplacian term vanish and lets raw VGG dominate. That is a straw man.

**Fix.** The minimum set is:
- **Hand (upstream)**: the reference.
- **RGB-only (λ_hvi = 0)**: 3-seed replication of the paper's single-run ablation (23.22 vs 24.11). Worth reporting whatever the outcome.
- **Raw-uniform**: 1 seed, sanity lower bound only.
- **EMA-norm (equal contribution)**: the proper "uniform" and the Kendall twin.
- **λ_hvi 1-D sweep** {0.25, 0.5, 2, 4}: the cheapest honest hand tuning (4 runs). Tells you whether λ=1 is on a plateau.
- **Random search, equal compute**: 8 configs sampled log-uniformly around the hand weights (±1 decade per term group) on the 300-ep proxy, chosen on scene-disjoint val, then the winner retrained 3 seeds full. The honest head-to-head: learned methods cost 1 run plus their own defaults; random search costs about 3 full-run equivalents.
- **Fine-tune continuation control** (from §3).

## 6. Locus, acceptability, honest best case

**Attack.** The locus is the training objective, specifically the balance between RGB and HVI supervision. It is not an architectural place. Applying Kendall, GradNorm, or DWA (all 2018) to one backbone has little novelty, and a professor expecting "method + where it improves" may call it thin. The strongest non-trivial claim, "no tuning needed on a *new* dataset or backbone", is not tested by LOL-v1, where the hand weights are already given.

**Consequence.** A method-framed thesis with a null result reads as a failure. A study-framed thesis with the same null reads as a finding.

**Fix / framing.** Title it as a study ("How much does CIDNet's dual-space loss design matter? A seeded, controlled analysis"). The contributions:
- (C1) seeded replication of the RGB/HVI ablation;
- (C2) the HVI-VGG removal test;
- (C3) gradient-share attribution: which term drives updates, when, and where. Stratify by pixel luminance. The hypothesis is that HVI-L1 matters mainly in dark, low-intensity pixels, where HVI's collapsible intensity term C_k changes how chroma errors are weighted. That is the "specific place" story;
- (C4) grouped leave-one-term-out;
- (C5) learned vs hand vs random-search weighting.

Honest best case: learned weighting (probably EMA-norm or Kendall, which end up the same) matches hand-tuned within ±0.2 dB with no tuning. HVI-VGG is removable and saves compute. The attribution shows 1–2 terms carry most of the update, with HVI terms concentrated in dark regions. That is accepted as a B.Sc. contribution if the stats are clean. "+0.5 dB from learned weights" should not be planned for. Stretch goal, only if budget remains: transfer the learned weighting without re-tuning to a second dataset (e.g. LOLv2-Syn), with hand weights as-is. That is the only setting where "no tuning" is a real advantage.

## 7. Statistics, overlap, GT-mean, test selection

**Attack.**
- (a) 3 seeds give MDE ≈ 0.6–0.9 dB (see Assumptions).
- (b) 14/15 test images have near-duplicate training scenes, so the test set rewards fitting the scene. A weighting that up-weights pixel L1 can win on test for that reason alone.
- (c) Raw PSNR on LOL is dominated by global brightness error. A loss change that shifts the brightness bias (the HVI I-channel L1 directly affects brightness) can move raw PSNR by tenths of a dB with no real gain in restoration. The shift disappears under GT-mean.
- (d) Upstream code evaluates on test during training and keeps the best epoch, which is test-set selection. It inflates every arm by an arm-dependent amount.
- (e) Per-image tests over 15 images do not address seed variance, which is the dominant variance.

**Fix.**
- Checkpoint = **last epoch** (primary) and **val-selected** (secondary). Never select on test; turn off test-best saving.
- **Scene-disjoint val**: cluster the LOL-v1 training images by scene (perceptual hash plus a manual check). Hold out ~10 % of scenes (~45–50 images) that also do not overlap eval15 scenes. Use the same split for all arms. The primary endpoint is val PSNR, because it is not scene-leaked. LOL-v1 eval15 is secondary and reported for comparability.
- Cross-dataset check: evaluate all final checkpoints on LOLv2-Real test (100 images) with no retraining. **First check it for overlap with LOL-v1 train by hashing**; the sets are related captures. Drop overlapping images.
- Report raw PSNR, GT-mean PSNR, SSIM (one fixed implementation, stated), and LPIPS (alex, stated). If more than 70 % of a raw gain disappears under GT-mean, call it brightness bias.
- Inference: the unit of replication is the seed. Report mean ± sd over seeds of per-run means. Add a hierarchical bootstrap CI (resample seeds, then images) for the paired difference, and use Holm correction across learned arms vs hand. TOST for equivalence claims. State σ_seed and the achieved MDE in the thesis.

---

## Revised design

Costs are from scratch at 9 GPU-h/run unless marked. P = 300-ep compressed proxy ≈ 2.7 GPU-h.

| Phase | Arm | Isolates | Seeds | Cost (GPU-h) |
|---|---|---|---|---|
| 0 (days 1–2) | A0 Hand (upstream) + gradient-share logging | Reference; σ_seed; attribution data (C3) | 3 | 27 |
| 0 | Throughput test: 2 jobs/GPU on 11 GB | Can the budget be doubled? | – | 1 |
| 0 | Fine-tune smoke: hand-continue vs Kendall-continue, 50 ep | Code works; shows fine-tune ≠ evidence | 3+3 | 2.5 |
| 1 | A1 Hand − HVI-VGG | Contribution of the questionable term (C2) | 3 | 27 |
| 1 | A2 RGB-only (λ_hvi = 0) | Replicates paper ablation (C1) | 3 | 27 |
| 1 | A3 Raw-uniform | Sanity lower bound | 1 | 9 |
| 1 | A4 EMA-norm (1/EMA(L_i)) | Deterministic twin of Kendall | 3 | 27 |
| 1 | A5 **Kendall, term-level (pre-registered primary)**, s_i clamp ±5 | Learned weighting | 3 | 27 |
| 1 | A6 Kendall, space-level (2 weights, hand ratios within space) | Is the gain in the space balance or the term balance? | 3 | 27 |
| 1 | A7 DWA (T=2, default, untuned) | Second learned family | 3 | 27 |
| 2 | A8 λ_hvi sweep {0.25, 0.5, 2, 4} | Is λ=1 on a plateau? (cheap hand tuning) | 1 each | 36 |
| 2 | A9 Random search: 8 configs on P, then best x3 full | Equal-compute tuning competitor | 8P + 3 | 22 + 27 = 49 |
| 2 | A10 Kendall − HVI-VGG | 2x2 factorial cell (with A0, A1, A5) | 3 | 27 |
| 3 | A11 Grouped LOTO: drop {L1, SSIM, edge, VGG} in both spaces | Measurement chapter (C4) | 2 each | 72 |
| 3 (cut first) | A12 GradNorm, space-level, α=1.5, ~1.3x overhead | Third learned family | 3 | 36 |
| – | Eval: val + eval15 + LOLv2-Real (dedup) for all final ckpts, raw/GT-mean/SSIM/LPIPS | – | – | ~5 |
| **Total** | | | | **≈ 425** (≈ 390 without A12) |

That fits the ~500 GPU-h realistic budget with ~75 GPU-h to spare for reruns. If the 2-jobs/GPU test gives ≥1.4x throughput, restore LOTO to 3 seeds and keep GradNorm.
**Cut order under time pressure:** A12, then A11 down to 1 seed, then A8 down to {0.5, 2}, then A3.

## Kill criteria

- **K0 (pipeline):** if A0 from scratch, last-epoch LOL-v1 raw PSNR is < 23.3 (below the third-party range), stop and debug before any other arm.
- **K1 (power):** if the measured σ_seed on val PSNR is > 0.4 dB, drop every superiority claim. The thesis becomes the study (C1–C4) plus "no detectable difference; MDE = X dB".
- **K2 (method track):** if no learned arm (A5–A7) is within 0.2 dB of A0 on val after Phase 1, stop investing in learned weighting (skip A10 and A12) and move the budget to LOTO seeds and the attribution analysis.
- **K3 (equivalence to trivial rule):** if Kendall weights correlate > 0.95 with the EMA-norm weights and A4 ≈ A5 (n.s.), report Kendall as magnitude normalisation. Do not present weight trajectories as insight.
- **K4 (brightness artefact):** if > 70 % of any raw-PSNR gain disappears under GT-mean PSNR, do not claim an improvement.
- **K5 (confound):** if A1 (hand − HVI-VGG) ≥ A10 (Kendall − HVI-VGG) − noise, the finding is the term removal, not the weighting.
- **K6 (proxy validity):** if the 300-ep proxy ranking of A0/A1/A2/A5 disagrees with the full-run ranking on more than one pair, do not use the proxy. Replace random search with the λ sweep only.
- **K7 (schedule):** if Phase 0 is not finished by end of day 2, cut A12 and cut A11 to 1 seed immediately.

## Probability

P(pre-registered learned weighting (Kendall, A5) beats hand-tuned by > 0.3 dB in raw PSNR on LOL-v1 eval15, mean of 3 from-scratch seeds, last-epoch checkpoint) ≈ **0.12**.

- This comes mostly from noise. With a true effect ≈ 0 and σ_seed ≈ 0.3 dB, the SD of the mean difference is ≈ 0.25 dB, so P(Δ > 0.3) ≈ 0.11 under the null. The prior on a real positive effect is weak: the objectives are redundant rather than conflicting, and GradNorm underperformed hand weights in other restoration work.
- If the thesis reports the best of three learned methods, this rises to ≈ 0.25 (multiple comparisons).
- P(the gain is > 0.3 dB **and** also holds on scene-disjoint val **and** under GT-mean) ≤ **0.05**.
