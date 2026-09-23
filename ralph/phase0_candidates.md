# phase0_candidates.md — thesis question candidates (master, 2026-09-23)

Status: **v2** — hours reconciled against the measured smoke cost in `ralph/results/phase0_codebase.json`
(2026-09-23 19:40). Ranking unchanged from v1.

## Shared facts that constrain every candidate
- Upstream protocol: 1000 epochs, batch 8, crop 256, Adam 1e-4 cosine, 485 LOLv1 train pairs. One full-protocol
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

## C1 — Does the HVI color space itself buy anything, under an identical network and seeds?
**Question.** With the CIDNet architecture, loss, and protocol frozen, does training in HVI outperform training in
sRGB, HSV, and YCbCr by more than the seed-to-seed spread?
**Why open.** The paper's color-space ablation (sRGB 20.06 / HSV 21.35 / HVI 24.11 dB) is one dataset (LOLv2-Real),
one run, no variance, test-selected. Every prior color-space LLIE paper (Bread/YCbCr, LYT-Net/YUV, DCC-Net) compares
its own space inside its own network. No neutral comparison exists.
**If it works.** "HVI's gain over HSV/YCbCr/sRGB survives seeds and validation-based selection: Δ = x ± s dB on
LOLv1 across 3 seeds." Plus the decomposition: HVI-without-C_k vs full isolates the density term.
**If it fails.** "Under matched training, the choice of color space changes LOLv1 PSNR by less than the seed spread
(s dB); the reported 3–4 dB gaps are not reproducible under seeded, validation-selected training." A negative result
with three seeds is the thesis.
**Minimal experiment.** 5 conditions {sRGB, HSV, YCbCr, HVI w/o C_k, HVI} × 3 seeds = **15 runs** (≈ 135 GPU-h,
≈ 1.5 days on 4 GPUs). Selection on val; one final test eval per condition. Secondary, free analysis: seed SD per
condition, and the val-selected vs "upstream-style" checkpoint gap (see C2).
**Risk of triviality.** Low. Whichever way it comes out it answers something nobody measured. Implementation risk:
the HV branch is a 2-channel chroma branch; sRGB/HSV/YCbCr must be mapped to (intensity, 2-ch chroma) the same
way (V/HS, Y/CbCr, max/normalised-RG), documented in the protocol. That mapping choice is itself a stated assumption.

## C2 — How much of the reported gap is seed noise and test-set selection?
**Question.** For a fixed configuration, what is the seed-to-seed SD of LOLv1 PSNR/SSIM, and how much does
picking the best checkpoint on the test split (upstream practice) inflate the number over validation-based selection?
**Why open.** GitHub issues #160/#162 report non-reproducibility (23.89 vs 24.11); the README admits lost
hyper-parameters; no paper in this family reports variance.
**If it works.** "Seed SD is s dB; test-selection inflates by b dB; the reported margins over the runner-up are
within s + b." **If it fails** (SD tiny, bias tiny): "HVI-CIDNet is reproducible to ±s dB under a fixed seed and
val-selection; the published number is not an artefact." Either is a clean, useful thesis chapter.
**Minimal experiment.** 1 condition × 5 seeds = **5 runs**, entirely shared with C1's HVI arm (3 of the 5).
The selection-bias measurement evaluates every saved checkpoint on the test split *once, in a dedicated audit
script whose JSON says so* — it is a measurement of the practice, never used to pick anything we report.
**Risk of triviality.** Medium as a stand-alone thesis (it is a methodology finding); high value as C1's second
study. Recommended as **C1's companion, not a stand-alone**.

## C3 — The density term: does k matter, and what happens near black?
**Question.** Fixed k ∈ {0.1, 0.2, 0.5, 1.0, 2.0} vs learnable k (upstream default): does k change LOLv1 quality,
and does the near-black failure (inverse divides by C_k ≈ 0.025 at I≈0; hue → arbitrary) show up as measurable
error in the darkest intensity bins?
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
**Minimal experiment.** **0 training runs** — reuses C1 checkpoints; eval-only, ~1 GPU-h. Needs LOLv2-Real
(download). **Risk of triviality.** Medium; works only as C1's third study, not stand-alone.

## C6 — Efficiency: is CIDNet over-parameterised for a consumer GPU?
**Question.** Width scale {0.5, 0.75, 1.0} × 3 seeds: PSNR vs latency / VRAM on a 2080 Ti.
**Works / fails.** "Half-width loses x ± s dB for 3× speed" / "half-width matches full within seed spread".
**Minimal experiment.** 9 runs (cheaper than R each). **Risk of triviality.** High: monotone curves are expected
and the finding is generic to any U-Net; weakest link to the HVI idea.

---

## Ranking  (decidability × size of gap × survives a negative result)

| # | Candidate | Runs | Decidable with our compute | Gap size | Negative result still a thesis | Score |
|---|---|---|---|---|---|---|
| 1 | **C1 color space + C2 seeds/selection** | 15 (+2) | yes, ≈ 1.6 days on 4 GPUs | large (the paper's central claim, never seeded) | yes, strongly | ★★★★★ |
| 2 | C3 density k + near black | 18 | yes, ≈ 1.7 days | medium–large (untested knob, real artefact) | yes | ★★★★ |
| 3 | C4 dual-space loss + seeds | 18 | yes, ≈ 1.7 days | medium (issue #163, perceptual oddity) | yes | ★★★ |
| 4 | C5 robustness | 0 | yes, hours | medium | partly | ★★★ (as C1's follow-on) |
| 5 | C6 efficiency | 9 | yes, ~1 day | small | weak | ★★ |

**Recommendation: C1 as the primary study, C2 as its built-in second study, C5 as the zero-cost third study.
C3 is the pre-committed pivot** if C1's instrument shows the non-HVI spaces cannot be trained fairly in the
two-branch net (then the thesis narrows to "inside HVI, what does the density term do?"). Total budget ≈ 17 runs ≈ 155 GPU-h ≈ 1.6 days on 4 GPUs
(+ 18 runs ≈ 1.7 days if the pivot fires), well inside a two-week window.

Rejected families and why: a targeted new module (needs a pre-registered improvement and competes with 2026
follow-ups we cannot beat in a bachelor's budget); more datasets before the LOLv1 question is settled (adds download
and protocol risk, not evidence).
