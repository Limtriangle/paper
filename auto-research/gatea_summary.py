"""gatea_summary — derived, citable aggregate keys for Gate A (master ruling 6, 2026-09-24).

    python3 auto-research/gatea_summary.py      # -> ralph/results/gateA__summary_v1.json

Keys: summary.gateA_L0.<final|gated|valsel>.<raw_psnr|gtmean_psnr|ssim|lpips>.{mean,sd,n} over the seeds
present in ralph/results/final_eval__test.json (labels gateA_L0_seed<s>[_gated|_valsel]);
summary.gateA_L0.k_final.{median,min,max,per_seed} from the runs' metrics.csv (last row) via the exports;
summary.gateA_L0.oracle.{max_over_ckpt_mean, max_over_seeds, per_seed} once final_eval__oracle.json has
oracle_gateA_L0_seed<s> entries. Every number is computed here from those files; sources carry sha256.
"""
from __future__ import annotations

import re
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

R = H.PAPER / "ralph" / "results"
METRIC = {"raw_psnr": "psnr", "gtmean_psnr": "psnr_gtmean", "ssim": "ssim", "lpips": "lpips"}


def msd(vals):
    return {"mean": float(statistics.mean(vals)), "sd": (float(statistics.stdev(vals)) if len(vals) > 1 else None), "n": len(vals)}


def main():
    sources = {}
    test = R / "final_eval__test.json"
    E = H.json_load(test)["entries"]
    sources[test.name] = H.sha256_file(test)
    out = {"final": {}, "gated": {}, "valsel": {}}
    seeds = {}
    for label, e in E.items():
        m = re.match(r"^gateA_L0_seed(\d+)(?:_(gated|valsel))?$", label)
        if not m:
            continue
        kind = m.group(2) or "final"
        seeds.setdefault(kind, {})[int(m.group(1))] = e["metrics"]
    for kind, per in seeds.items():
        out[kind] = {k: msd([per[s][v] for s in sorted(per)]) for k, v in METRIC.items()}
        out[kind]["seeds"] = sorted(per)
    # final k per seed from the run exports (metrics.csv last row is not exported; read the raw file, hash it)
    ks = {}
    for exp in sorted(R.glob("gateA__a0_l0_v*.json")):
        d = H.json_load(exp)
        sources[exp.name] = H.sha256_file(exp)
        for job, jd in d["jobs"].items():
            if jd.get("status") != "complete" or not job.startswith("L0_seed"):
                continue
            mcsv = Path(d["root"]) / job / "metrics.csv"
            rows = H.csv_rows(mcsv)
            sources[f"{d['run']}/{job}/metrics.csv"] = H.sha256_file(mcsv)
            ks[int(job.split("seed")[1])] = float(rows[-1]["k"])
    if ks:
        out["k_final"] = {"median": float(statistics.median(ks.values())), "min": min(ks.values()), "max": max(ks.values()),
                          "per_seed": {str(s): ks[s] for s in sorted(ks)}, "n": len(ks)}
    oracle = R / "final_eval__oracle.json"
    if oracle.is_file():
        O = H.json_load(oracle)["entries"]
        sources[oracle.name] = H.sha256_file(oracle)
        per = {int(l.split("seed")[1]): e for l, e in O.items() if re.match(r"^oracle_gateA_L0_seed\d+$", l)}
        if per:
            maxes = {s: max(c["psnr"] for c in per[s]["curve"]) for s in per}
            maxes_gm = {s: per[s]["max_psnr_gtmean"] for s in per}
            out["oracle"] = {"max_over_ckpt_mean": {"raw_psnr": msd(list(maxes.values())), "gtmean_psnr": msd(list(maxes_gm.values()))},
                             "max_over_seeds": {"raw_psnr": max(maxes.values()), "gtmean_psnr": max(maxes_gm.values())},
                             "per_seed": {str(s): {"raw_psnr": maxes[s], "gtmean_psnr": maxes_gm[s], "n_checkpoints": per[s]["n_checkpoints"]} for s in sorted(per)},
                             "notes": "paper-style numbers: max over saved checkpoints on the test split; NEVER used for selection"}
    # decomposition (master 2026-09-24): per-seed differences, then aggregated; raw PSNR unless named gtmean
    fin, gat, vs = seeds.get("final", {}), seeds.get("gated", {}), seeds.get("valsel", {})
    dec = {}
    if fin:
        dec["gtmean_minus_raw"] = msd([fin[s]["psnr_gtmean"] - fin[s]["psnr"] for s in sorted(fin)])
    both = sorted(set(fin) & set(gat))
    if both:
        dec["gated_minus_ungated"] = msd([gat[s]["psnr"] - fin[s]["psnr"] for s in both])
        dec["gated_minus_ungated_gtmean"] = msd([gat[s]["psnr_gtmean"] - fin[s]["psnr_gtmean"] for s in both])
    both = sorted(set(fin) & set(vs))
    if both:
        dec["valsel_minus_final"] = msd([vs[s]["psnr"] - fin[s]["psnr"] for s in both])
        dec["valsel_minus_final_gtmean"] = msd([vs[s]["psnr_gtmean"] - fin[s]["psnr_gtmean"] for s in both])
    if "oracle" in out:
        per = out["oracle"]["per_seed"]
        both = sorted(s for s in fin if str(s) in per)
        if both:
            dec["oracle_minus_final"] = msd([per[str(s)]["raw_psnr"] - fin[s]["psnr"] for s in both])
            dec["oracle_minus_final_gtmean"] = msd([per[str(s)]["gtmean_psnr"] - fin[s]["psnr_gtmean"] for s in both])
    dec["notes"] = "per-seed differences on eval15 (raw PSNR unless suffixed _gtmean), aggregated over seeds; decomposition only, never selection"
    out["decomposition"] = dec
    # Gate A window (HVI-PLAN.md §5 constants, recorded for provenance) and the gap of the final raw mean to its lower edge
    if out.get("final", {}).get("raw_psnr"):
        out["window"] = {"lower": 23.3, "upper": 24.3, "source": "HVI-PLAN.md §5 Gate A",
                         "final_raw_mean_minus_lower": out["final"]["raw_psnr"]["mean"] - 23.3,
                         "final_raw_mean_inside": 23.3 <= out["final"]["raw_psnr"]["mean"] <= 24.3,
                         "gated_raw_mean_minus_lower": (out["gated"]["raw_psnr"]["mean"] - 23.3) if out.get("gated", {}).get("raw_psnr") else None}
    res = {"run_id": "gateA__summary_v1", "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "script_sha256": H.sha256_file(Path(__file__)), "summary": {"gateA_L0": out}, "sources": sources,
           "status": "complete" if len(seeds.get("final", {})) >= 5 else "partial",
           "notes": "derived by script from final_eval__test.json / gateA exports / final_eval__oracle.json; gated, valsel and oracle are Gate A decomposition columns, not selection"}
    dest = R / "gateA__summary_v1.json"
    H.json_save(dest, res)
    f = out.get("final", {})
    print("wrote", dest, "| final raw", f.get("raw_psnr"), "| k_final", out.get("k_final", {}).get("median"), "| oracle", "yes" if "oracle" in out else "no")


if __name__ == "__main__":
    main()
