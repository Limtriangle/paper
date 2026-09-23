# paper — writing-driven autoresearch for the HVI-CIDNet thesis

Three Claude Code agents (master / experiment / writing) produce an ICML-format thesis paper
from the HVI-CIDNet studies in `/home/work/research`, following the
[writing-driven-autoresearch](https://github.com/happyhappy-jun/writing-driven-autoresearch)
method: write the finished paper first with `\ph{}` placeholders, run the experiments that
fill them, and make untruth expensive with key-level verification.

Start here: [`CLAUDE.md`](CLAUDE.md) (roles, contract, commands) → [`HVI-PLAN.md`](HVI-PLAN.md)
(the spec) → `harness/*.md` (personas, guides).

## Layout

```
CLAUDE.md            orchestration root — read first
HVI-PLAN.md          research spec: question, claims, gates, pivots, provisional values
bootstrap.sh env.sh  restore the ephemeral home after a session reset; shell env
harness/             master.md experiment.md writing.md + writing-guidelines/style-guide
harness/upstream/    the original hackathon personas + tooling, reference only
tooling/             build, audit, verify-phm, gen-table, unwrap-phm, export_results, status
ralph/               shared state: STATUS, DECISIONS, RESULTS, INBOX, PH-LEDGER, phm-spec, results/*.json
writing/             ICML LaTeX (icml2024/main.tex, section/, tables/, figures/)
auto-research/       new experiment + plot scripts (existing studies stay in /home/work/research)
herdr/               start-team.sh, herdr_sync.py, permission-policy.md, topology.json
writing-main.pdf     the current build
```

## Daily use

```bash
ssh gist-hvi
bash /home/work/research/paper/bootstrap.sh    # only after a compute-session reset
cd /home/work/paper
bash herdr/start-team.sh                       # launch/revive the three agents
herdr --session ralph                          # watch them (ctrl+b q to detach)
bash tooling/status.sh                         # dashboard
```

Answer the agents' questions in `ralph/INBOX.md`; read what they decided in `ralph/DECISIONS.md`.
