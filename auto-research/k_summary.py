"""k_summary — per-arm final-k statistics for the S1 loss ladder (master request 2026-09-25).

    python3 auto-research/k_summary.py      # -> outputs/s1/loss_ladder_v1/analysis_k/decision.json, then
                                            #    tooling/export_results.py --run s1/loss_ladder_v1 merges it as
                                            #    analysis.analysis_k.decision in ralph/results/s1__loss_ladder_v1.json
Keys: summary.<arm>.k_final.{median,min,max,n,per_seed} over COMPLETE runs (L0 from the gateA v1+v2 runs,
L1..L4 from s1/loss_ladder_v1; A-arms from s2 when present), constants.{k_init: 0.2 (net/HVI_transform.py:9),
k_released: 1.1255 (phase0_weights.json), k0_loss: 1.1255 (HVI-PLAN §3)}, sources = sha256 of every metrics.csv read.
"""
import re, statistics, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H

RUNS = [H.OUTPUTS / "gateA" / "a0_l0_v1", H.OUTPUTS / "gateA" / "a0_l0_v2", H.OUTPUTS / "s1" / "loss_ladder_v1",
        H.OUTPUTS / "s2" / "rep_ladder_v1"]
OUT = H.OUTPUTS / "s1" / "loss_ladder_v1" / "analysis_k" / "decision.json"


def main():
    ks, sources = {}, {}
    for run in RUNS:
        if not run.is_dir():
            continue
        for job in sorted(run.iterdir()):
            m = re.match(r"^([A-Z]\d)_seed(\d+)$", job.name)
            st = job / "status.json"
            if not m or not st.is_file() or H.json_load(st).get("state") != "complete":
                continue
            rows = H.csv_rows(job / "metrics.csv")
            if not rows or "k" not in rows[-1]:
                continue
            ks.setdefault(m.group(1), {})[int(m.group(2))] = float(rows[-1]["k"])
            sources[f"{run.parent.name}/{run.name}/{job.name}/metrics.csv"] = H.sha256_file(job / "metrics.csv")
    summary = {}
    for arm, per in sorted(ks.items()):
        v = list(per.values())
        summary[arm] = {"k_final": {"median": float(statistics.median(v)), "min": min(v), "max": max(v), "n": len(v),
                                    "sd": (float(statistics.stdev(v)) if len(v) > 1 else None),
                                    "per_seed": {str(s): per[s] for s in sorted(per)}},
                        "k_learnable": arm not in ("A1", "A2")}
    dec = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "script_sha256": H.sha256_file(Path(__file__)),
           "constants": {"k_init": 0.2, "k_released": 1.1255, "k0_loss": 1.1255,
                         "provenance": "k_init net/HVI_transform.py:9; k_released ralph/results/phase0_weights.json; k0_loss HVI-PLAN.md §3"},
           "summary": summary, "sources": sources,
           "note": "final epoch value of the model's density_k per run (metrics.csv last row); A1/A2 hold k fixed"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    H.json_save(OUT, dec)
    print("wrote", OUT, {a: (round(s["k_final"]["median"], 4), s["k_final"]["n"]) for a, s in summary.items()})


if __name__ == "__main__":
    main()
