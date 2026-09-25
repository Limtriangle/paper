# AUTHOR_BRIEF.md — hand-over for the author (maintained by master while the author is away, 2026-09-25 → 2026-10-01)

Status line: **skeleton, filled as gates close.** Nothing here is submission-ready; the paper is NOT marked complete.

## 1. The question (HVI-PLAN.md §0)
Under a frozen protocol with five matched seeds, which steps of HVI-CIDNet's representation ladder (learned k → fixed k
→ no collapse → linear chroma → luma intensity) and of its heuristic dual-space loss ladder (full → no VGG on HVI →
k detached → RGB-only → C_k-weighted chroma) change LOL-v1 quality by more than the seed spread, by how much, and
where in the intensity range? Advisor's framing: confirm under which conditions and by how much the effect reproduces.

## 2. Design (HVI-PLAN.md §3–§4)
Frozen upstream code protocol; scene-disjoint val (40) / train (445); final-checkpoint read-out; GT-mean PSNR (scalar
gain) primary; eval15 read once per arm; oracle post hoc; 5 matched seeds; paired-by-seed tests with Holm, TOST ± 0.3 dB,
decile mechanism rule; vocabulary contributes / removable / inconclusive.

## 3. Key results (filled at each gate; every number below is also a key in ralph/results/)
- **Gate A (2026-09-24, PASS-with-P-A).** A0 under the full upstream loss, from scratch, final checkpoint, eval15,
  raw PSNR: n = 5 (pre-registered gate) 23.25 ± 0.47 dB, 0.05 dB below the window [23.3, 24.3]; pooled n = 8
  (pre-registered extra seeds) 23.26 ± 0.41 dB, 0.04 dB below. Under upstream's own reporting conditions the same
  runs give 23.79 raw with the saturation gate and 27.74 GT-mean (README: 23.81 / 27.71): the pipeline reproduces
  upstream's reporting conditions; the shortfall is protocol (final checkpoint, ungated, 445 training images).
  Keys: gateA__summary_n5_v1.json, gateA__summary_v1.json.
- **S3 selection-bias decomposition (A0-L0, n = 5).** GT-mean rescaling +3.39 dB; saturation gate +1.09 dB (GT-mean);
  test-set selection (oracle max over checkpoints − final) +0.41 dB raw but only +0.06 dB GT-mean; seed SD 0.16 GT-mean
  / 0.47 raw; val-selected checkpoint −0.71 dB GT-mean vs final (val picks early checkpoints for some seeds).
  Reading: the published spread is mostly rescaling and gating; selection matters for raw PSNR, not for GT-mean.
- **k drift (S1 side result).** Final k median 0.85 when k is coupled through the loss (L0), 0.29 when detached (L2),
  from init 0.2; released weights 1.13. Most of upstream's k drift is loss-side coupling. Key: analysis_k in
  s1__loss_ladder_v1.json.
- Gate B — loss ladder: *(pending, ETA 2026-09-26)*
- Gate C — representation ladder: *(pending, ETA 2026-09-28)*
- S4 oracle decomposition (bonus): *(pending)*

## 4. What changed versus the plan
- Gate A raw mean fell 0.05 dB below the pre-registered window; pivot P-A applied (DECISIONS 2026-09-24 20:30): the
  paper leads with the measured reproduction and its decomposition; absolute numbers labelled "under our protocol".
- Extra seeds 47–49 added to A0-L0, A2, A3 by the pre-registered SD rule (0.4 < SD ≤ 0.5).
- The fast fine-tune loop built for the earlier method candidates was found valid only for release-compatible
  components and is not used for the ladders (all from scratch).
- Literature numbers bound through literature_v1.json (DECISIONS 2026-09-25 20:3x).

## 5. Open questions for the author
- Gate A reporting n (ruled by master on 2026-09-25: gate at n = 5, reference arm pooled n = 8; reversible).
- *(more as they arise)*

## 6. Every decision taken while the author was away
*(list of DECISIONS.md lines from 2026-09-25 20:30 UTC onward; filled at the end)*
