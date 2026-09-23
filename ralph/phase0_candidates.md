# phase0_candidates.md — thesis question candidates (master, 2026-09-23)

Status: **v3** — hours reconciled against the measured smoke cost (`ralph/results/phase0_codebase.json`) and the
literature facts corrected against `ralph/phase0_related.md` (2026-09-23 19:55 UTC). Ranking unchanged.

## Shared facts that constrain every candidate
- **Baseline protocol = the code, not the paper text**: 1000 epochs, batch 8, crop 256, Adam 1e-4 with 3-epoch warmup
  (epoch 1 at lr 0) then cosine, no effective gradient clipping, 485 LOLv1 train pairs. The paper text says 1500 epochs
  and 400² crops; those do not fit the released code or an 11 GB GPU at batch 8, and the code is what anyone can run. One full-protocol
  run on one RTX 2080 Ti = **R ≈ 9.1 h** measured (26.2 s/epoch train + 50-image validation each epoch; 7.3 h
  train-only; peak 9.8 GiB of 11; key `cost.projected_hours_full_schedule` in phase0_codebase.json). Validating
  every 5 epochs instead of every epoch brings R to ≈ 7.7 h. 4 GPUs → ≈ 10–12 runs/day; ≈ 70 runs/week.
  Same-seed run-to-run noise (non-deterministic CUDA kernels) is measurable (0.04 dB val PSNR after 2 epochs) and
  will be reported as a floor under the seed spread; bitwise-strict mode costs 1.5× and is not the default.
- Upstream reports **single runs with a random, unlogged seed**, and its training loop **scores every 10th
  checkpoint on the test split** (eval15); the released `best_PSNR`/`best_SSIM` weights imply selection on those scores. Our frozen protocol will hold out a validation subset of the 485 training pairs and select on it. So
  every candidate below produces, as a by-product, the first seeded reproduction of HVI-CIDNet on LOLv1.
- Three seeds per condition is the floor (plan §1). A difference smaller than the seed SD is "no measurable
  difference" — and that is a publishable thesis result here.
- Only LOLv1 is on disk. Anything else costs a download + checksum log, not GPU time.

---

## C1 — What in the HVI representation matters, under an identical CIDNet, a frozen loss, and matched seeds?  *(v4: rewritten as the nested ladder of `ralph/related/redteam/R2_design_redteam.md`, at the author's request)*

**Why the old C1 was wrong (R2 §1–§3).** "Swap the colour space" changed four things at once (branch split,
auxiliary-loss space, learnable k, residual space); a split-less sRGB arm is a different architecture; HSV-polar is a
strawman the authors already ran (R1: CVPR'25 Table 4 on LOL-v2-Real and CIDNet+ Table V on LOL-v1 — single runs, and
the sRGB-vs-HSV sign flips between them); and with n = 3 seeds no paired test can reach p < 0.05, so "within seed
spread" would have been a guaranteed non-finding. R1's verdict: partially done, not redundant — no seeded, validation-
selected, YCbCr-inclusive comparison exists in any restoration task.

**Question.** Along a nested ladder of single-factor steps inside the same two-branch CIDNet, with the same loss in
every arm and five matched seeds, which step moves LOL-v1 quality by more than the paired seed spread — and is the
C_k effect located where its mechanism predicts (dark pixels)?

**Common to all arms.** Same network and parameter count; residual taken in the working space; **frozen loss**
L = L_rgb (L1 + 0.5·SSIM + 50·edge + 0.01·VGG) + L_hvi at a constant k0 (L1 + 0.5·SSIM + 50·edge, **no VGG**), with
no gradient reaching k through the loss (upstream does not detach k; diagnostic arm U measures the drift that causes).
Val split scene-disjoint (§Protocol). Five matched seeds per arm (seed s fixes data order, crops, flips, and the init of
every shape-identical layer). Test-time inverse-transform knobs (gated, alpha, gamma) fixed to identity in every arm.

| Arm | Representation (I-branch / HV-branch) | Isolates (vs neighbour) | Runs |
|---|---|---|---|
| A0 | HVI, learned k | reference: upstream model under the fixed loss | 5 |
| A1 | HVI, k frozen at A0's median converged k | learned vs fixed k — **dropped if A0's k moves < 0.05** (then A1 := A0) | 5 (0) |
| A2 | HVI with k = 0 (Cartesian HSV: I = max, S·cos h, S·sin h) | **the C_k intensity collapse — primary contrast A0 − A2** | 5 |
| A3 | I = max / linear opponent chroma (Cb, Cr) | saturation-polar vs linear chroma (A2 − A3) | 5 |
| A4 | YCbCr (I = Y / Cb, Cr) | intensity definition max vs luma (A3 − A4); expect mainly an exposure effect | 5 |
| L1 | HVI learned k, L_rgb only | contribution of the auxiliary HVI loss (A0 − L1), secondary family | 5 |
| R (opt.) | split-less RGB reference (I = Y; HV-branch emits a 3-ch RGB residual) | sanity anchor only; **not** a point on the colour-space axis | 3 |
| U (diag.) | A0 with upstream's coupled-k loss | k loss-hacking check (k trajectory + PSNR) | 1 |

Dropped: HSV-polar (predictable, published) and split-less sRGB *as a colour-space arm*.

**Read-outs per run (R2 §4b).** Primary: the **final epoch-1000 checkpoint** (cosine ends at lr ≈ 0; selection-free).
Secondary: best-val-PSNR checkpoint. Oracle: test PSNR of every 10th checkpoint — **computed post hoc, once, by the
frozen `final_eval_test.py` in a dedicated pass after all arms finish**, from checkpoints saved every 10 epochs
(~0.8 GB/run), so training and selection never touch eval15 (integrity floor rule 4 kept literally); its JSON is
labelled `oracle`, never used to rank arms. Selection bias (old C2) = oracle − final and oracle − val-selected;
max-over-seeds of the oracle is the "paper-style" number.

**Metrics (R2 §4c).** Primary: **GT-mean PSNR with one scalar luminance gain** (never per-channel), mean over the 15
test images, per run. Secondary: raw PSNR, SSIM, LPIPS, ΔE00 (raw and after scalar gain), log-exposure error
log(mean_out/mean_gt), and the decomposition raw MSE ≈ gain error + GT-mean residual. Zero-run analyses on saved
outputs: per-GT-intensity-decile RGB MSE, ΔE00 and chroma-weighted circular hue error |Δh|·S_gt per arm and seed with
seed-level CIs; darkness stress test (inputs × 0.5, × 0.25 + Poisson–Gaussian noise) giving a dose–response curve of
Δ(A0 − A2) hue error; LOL-v2-Real evaluation only after deduplication against the LOL-v1 train set.

**Pre-registered decision rules (R2, verbatim in substance).**
1. Primary metric/read-out: GT-mean PSNR (scalar gain) at the final checkpoint, per run.
2. Primary contrasts: A0−A1, A0−A2, A2−A3, A3−A4, paired by seed (n = 5), Holm-corrected across the four.
   A0−L1 is a separate secondary family.
3. **Difference claimed** only if (a) the paired 95 % t-CI (df = 4) excludes 0 after Holm; (b) |mean Δ| ≥ 0.3 dB and
   |mean Δ| > 2·SD(Δ_s); (c) the sign of Δ_s agrees in ≥ 4 of 5 seeds; (d) a mixed model
   PSNR ~ arm + (1|image) + (1|seed) agrees in direction. Per-image Wilcoxon tests are descriptive only.
4. **Equivalence claimed** only if TOST with margin ± 0.3 dB rejects at α = 0.05; otherwise "inconclusive". The
   phrase "less than the seed spread" is never used as a claim.
5. **Mechanism claim for C_k** (A0 vs A2): the hue-error or ΔE00 difference in the bottom 3 intensity deciles has a
   seed-level CI excluding 0, while the top-5-decile difference includes 0 or is ≥ 3× smaller; the darkness stress
   test shows |Δ| increasing monotonically across × 1, × 0.5, × 0.25.
6. **Pipeline gate:** A0 mean raw PSNR ∈ [23.3, 24.3] dB and seed SD ≤ 0.5 dB before any other arm launches.
   If SD > 0.4 dB, raise seeds to 8 on A0, A2, A3 only.
7. Selection bias reported as (oracle − final) and (oracle − val-selected), mean ± SD over seeds, plus the
   paper-style max; never used to rank arms.
8. Frozen before launch, with hashes committed: loss weights, k0, the scene-cluster val split, the inverse-transform
   knobs, the metric code, the analysis script. eval15 is read only by the frozen final-eval script.
9. **Pivot trigger → C3:** the pipeline gate fails, or σ_seed > 0.6 dB even with 8 seeds.

**If it works.** "Step X of the ladder moves GT-mean PSNR by Δ = x ± s dB (paired, n = 5, Holm-corrected), and the
C_k gain sits in the darkest three deciles and grows as the input gets darker." **If it fails.** Every step is either
equivalent within ± 0.3 dB (TOST) — "inside CIDNet the HVI representation is not distinguishable from linear
luma/chroma at this power" — or inconclusive with the measured seed SD reported; the mechanism analysis and the
selection-bias numbers stand regardless. All three are a thesis.

**Cost (measured, `phase0_codebase.json`).** Validation every 5 epochs → ≈ 7.7 GPU-h per run (7.3 h train-only;
R2's 5–6 h estimate was optimistic). Core A0 + A2 + A3 + A4 + L1 = **25 runs ≈ 190 GPU-h ≈ 2.0 days on 4 GPUs**;
with A1 + R + U ≈ 34 runs ≈ 2.7 days. Order: the 5 A0 seeds first (pipeline gate + σ_seed + k trajectory ≈ 16 h
wall-clock), then the rest in waves of 4. One pilot pair (A0, A3) checks whether the ranking at 250/500/1000 epochs is
stable to 0.1 dB before any schedule shortening (R2 §4d); the schedule is re-annealed, never truncated.

**Protocol additions this candidate requires (instrument work, no training).** (i) Scene-disjoint val split: cluster
all 500 LOL-v1 images by scene (embedding + pHash on the GT), val ≈ 40 pairs from clusters containing no test image;
report how many test images have a train near-duplicate (cosine > 0.9). (ii) k0 constant and detached in the loss.
(iii) Checkpoints saved every 10 epochs. (iv) Transforms kept in FP32 (no AMP on atan2 / max / pow).
(v) Parameter counts asserted identical across arms.

**Risk of triviality.** R1 §Triviality: A3 vs A4 and R may land within noise (the linear-reparameterisation
expectation), and that is stated as a prediction; A0 vs A2 and A2 vs A3 are the informative contrasts. Limitation
stated up front: loss weights and lr were tuned upstream for HVI (conservative for a null, anti-conservative for a win);
a 3-point lr sweep on A0 and A3 (1 seed, 250 epochs) is optional if budget allows.

## C2 — Seed variance and test-set selection bias  *(folded into C1's read-outs; kept as a heading for the record)*
Answered at zero extra cost by C1's design: σ_seed from the five A0 seeds (pipeline gate), and selection bias from
(oracle − final) and (oracle − val-selected), with the oracle computed post hoc, once, by the frozen final-eval script.
LOL-v1 reference points: README 23.81 dB (raw) / 27.71 (GT-mean); paper table 28.20 (GT-mean, single run).

## C3 — The density term: does k matter, and what happens near black?
**Question.** Fixed k ∈ {0.1, 0.2, 0.5, 1.0, 2.0} (code convention; the code's k is the reciprocal of the paper's)
vs learnable k (upstream default, init 0.2): does k change LOLv1 quality,
and does the exact-black singularity (inverse divides by C_k ≈ 0.025 at I≡0; hue → arbitrary) show up as measurable
error in the darkest intensity bins? (Measured: for I<1/255 the inverse gain is 0.014 per unit chroma, so any effect
is confined to pixels at or within one code value of black, plus whatever k does to training.)
**Why open.** No k sweep in the paper; the learnable k also receives gradient through the target transform HVIT(gt),
so the model can shrink its own loss by collapsing chroma — unexamined. RHVI-FDD / BC-IHV (2026) replace the
intensity law with new modules but never sweep the original.
**If it works.** "k is a sensitive knob: Δ = x ± s dB across the sweep; learned k drifts to k*; error is concentrated
in the bottom-decile intensity bin." **If it fails.** "Quality is flat in k within seed spread; the density term's
claimed role is not measurable on LOLv1" — a thesis, and a direct comment on the paper's ablation.
**Minimal experiment.** 6 conditions × 3 seeds = **18 runs** (≈ 165 GPU-h, ≈ 1.7 days on 4 GPUs); plus a free per-pixel analysis (PSNR/hue error binned
by GT intensity) on saved outputs. **Risk of triviality.** Low–medium (flat curves are plausible and still a result).

## C4 — Dual-space objective: which loss terms matter, with seeds?
**Question.** {RGB+HVI loss (default), RGB only, HVI only} × {with, without VGG-perceptual}: which of the six
objectives differ by more than the seed spread on LOLv1?
**Why open.** Paper's loss ablation is single-run on LOLv2-Real (23.22 / 23.32 / 24.11); issue #163 asks how the
weights (edge 50, SSIM 0.5, VGG 0.01) were chosen; the perceptual loss shifts its RGB input to [0.5,1] before ImageNet
normalisation (range_norm), so the RGB-side perceptual term sees a systematically brightened image — worth measuring.
**Works / fails.** "Dual-space loss adds x ± s dB over RGB-only" / "the second loss space adds nothing measurable;
the perceptual term adds nothing measurable at weight 0.01." **Minimal experiment.** 6 × 3 = **18 runs**.
**Risk of triviality.** Medium: loss ablations are common; the seeded angle and the HVI-perceptual oddity are new.

## C5 — Robustness: do color-space models degrade differently under noise / JPEG / domain shift?
**Question.** Apply Gaussian noise (σ ∈ {5, 15, 25}/255), JPEG (q ∈ {90, 70, 50}) to LOLv1 test inputs, and
evaluate on LOLv2-Real test and unpaired sets (NIQE): does the color-space ranking from C1 hold?
**Why open.** RHVI-FDD argues max-RGB intensity is noise-sensitive but only tests its own fix.
**Minimal experiment.** **0 training runs** — reuses C1 checkpoints; eval-only, ~1 GPU-h. The darkness/noise
dose–response part is now inside C1 (decision rule 5); the LOL-v2-Real part needs a download and deduplication against
the LOL-v1 train set. **Risk of triviality.** Medium; works only as C1's follow-on, not stand-alone.

## C6 — Efficiency: is CIDNet over-parameterised for a consumer GPU?
**Question.** Width scale {0.5, 0.75, 1.0} × 3 seeds: PSNR vs latency / VRAM on a 2080 Ti.
**Works / fails.** "Half-width loses x ± s dB for 3× speed" / "half-width matches full within seed spread".
**Minimal experiment.** 9 runs (cheaper than R each). **Risk of triviality.** High: monotone curves are expected
and the finding is generic to any U-Net; weakest link to the HVI idea.

---

## Ranking  (decidability × size of gap × survives a negative result)

| # | Candidate | Runs | Decidable with our compute | Gap size | Negative result still a thesis | Score |
|---|---|---|---|---|---|---|
| 1 | **C1 nested HVI ladder (A0/A2/A3/A4 + L1), 5 matched seeds; C2 folded in** | 25 (+9 opt.) | yes, ≈ 2.0 (2.7) days on 4 GPUs | large (the paper's central claim, never seeded; k and YCbCr never run) | yes: TOST/inconclusive + mechanism + selection bias | ★★★★★ |
| 2 | C3 density k + near black | 18 | yes, ≈ 1.7 days | medium–large (untested knob, real artefact) | yes | ★★★★ |
| 3 | C4 dual-space loss + seeds | 18 | yes, ≈ 1.7 days | medium (issue #163, perceptual oddity) | yes | ★★★ |
| 4 | C5 robustness | 0 | yes, hours | medium | partly | ★★★ (as C1's follow-on) |
| 5 | C6 efficiency | 9 | yes, ~1 day | small | weak | ★★ |

**Recommendation: C1 (the R2 ladder) as the thesis, with C2 folded into its read-outs and C5's dose–response test
inside its mechanism rule. C3 (density-k sweep) is the pre-committed pivot** (rule 9) and a close second overall.
Budget: 25 core runs ≈ 2.0 days on 4 GPUs (≈ 2.7 days with the optional A1, R and U arms), inside a two-week window.

Rejected families and why: a targeted new module (needs a pre-registered improvement and competes with 2026
follow-ups we cannot beat in a bachelor's budget); more datasets before the LOLv1 question is settled (adds download
and protocol risk, not evidence).
