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
- Gate A (2026-09-24): PASS-with-P-A. *(n = 5 raw final 23.25 ± 0.47, 0.05 below the window; under upstream's
  reporting conditions 23.79 raw / 27.74 GT-mean, matching the README; pooled n = 8 to be stated here.)*
- S3 selection-bias decomposition: *(to fill)*
- Gate B — loss ladder: *(pending, ETA 2026-09-26)*
- Gate C — representation ladder: *(pending, ETA 2026-09-28)*
- S4 oracle decomposition (bonus): *(pending)*

## 4. What changed versus the plan
*(to fill; each item cross-references a DECISIONS.md line)*

## 5. Open questions for the author
- Gate A reporting n (ruled by master on 2026-09-25: gate at n = 5, reference arm pooled n = 8; reversible).
- *(more as they arise)*

## 6. Every decision taken while the author was away
*(list of DECISIONS.md lines from 2026-09-25 20:30 UTC onward; filled at the end)*
