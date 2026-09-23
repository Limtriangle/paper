# INBOX.md — human <-> agents

Agents append questions under **Open questions** (`- [ ]`). The author answers by editing
the line to `- [x] ... → <answer>`; master reads it on the next sweep and logs the answer
in DECISIONS.md with `[human]`. Agents never wait for an answer; they apply the plan's
default until one arrives.

## Open questions
- [ ] (plan §0) Is the thesis a controlled study of the HVI-CIDNet recipe, or does it propose a modification (prefilter / DySample) as the contribution? Default: controlled study.
- [ ] (plan §4 S1) GPU budget for the loss ablation: full 48 jobs, or the reduced default (W18 all variants × 3 seeds; W36 only FULL/RGB_ONLY/NO_PERC_HVI)? Default: reduced.
- [ ] (plan §4 S3) Run a third confirmation seed (45) for B0/I3 at 500 epochs? Default: no.
- [ ] Author name and affiliation for the non-anonymous build? Default: stays anonymous.
- [ ] Thesis submission deadline? Default: none set; gates fire as data lands.

## Answers / notes from the author
