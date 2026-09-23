# INBOX.md — human <-> agents

Agents append questions under **Open questions** (`- [ ]`). The author answers by editing
the line to `- [x] ... → <answer>`; master reads it on the next sweep and logs the answer
in DECISIONS.md with `[human]`. Agents never wait for an answer; they apply the plan's
default until one arrives. **Exception: Gate 0 (the topic) waits for the author.**

## Open questions
- [ ] (Gate 0) Topic. Master will list candidates in `ralph/phase0_candidates.md` and put its ranked recommendation here. Answer with `[human] topic confirmed: <candidate #>` or describe a different question.

## Answers / notes from the author
- 2026-09-24 [human] The earlier studies are discarded. Start the topic from scratch; it must be related to HVI-CIDNet.
