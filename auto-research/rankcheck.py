"""rankcheck — does the 50-epoch fine-tune loop preserve the ranking of the 1000-epoch from-scratch
protocol on one pair (A0 = HVI learned k vs A2 = k=0)?

    python3 auto-research/rankcheck.py [--finetune finetune__rankcheck_v2.json] [--scratch baseline__rankcheck_v2.json]

Reads the two exports under ralph/results/, computes the validation-split deltas A0 - A2 per
metric for both loops (best and last checkpoints), and writes
ralph/results/phase0_finetune_rankcheck.json with sign/magnitude agreement. Never touches eval15.
"""
import argparse, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H

METRICS = ("psnr", "psnr_gtmean", "ssim", "lpips", "delta_e00", "edge_delta_e00")
HIGHER = {"psnr", "psnr_gtmean", "ssim"}   # else lower is better
PAIR = ("A0_seed42", "A2_seed42")


def deltas(export):
    out = {}
    jobs = export["jobs"]
    for ck in ("best", "last"):
        if not all(j in jobs and ck in jobs[j] for j in PAIR):
            continue
        a, b = jobs[PAIR[0]][ck], jobs[PAIR[1]][ck]
        out[ck] = {m: {"A0": a[m], "A2": b[m], "A0_minus_A2": a[m] - b[m],
                       "A0_better": (a[m] > b[m]) if m in HIGHER else (a[m] < b[m])}
                   for m in METRICS if m in a and m in b}
        out[ck]["epochs"] = {j: jobs[j][ck].get("epoch") for j in PAIR}
    out["status"] = {j: jobs.get(j, {}).get("status") for j in PAIR}
    out["curve"] = {j: jobs.get(j, {}).get("curve") for j in PAIR}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finetune", default="finetune__rankcheck_v2.json")
    ap.add_argument("--scratch", default="baseline__rankcheck_v2.json")
    a = ap.parse_args()
    R = H.PAPER / "ralph" / "results"
    res = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "pair": PAIR, "split": "scene_v1 validation (40 images)",
           "test15": "NEVER READ", "sources": {}, "loops": {}}
    for name, fn in (("finetune", a.finetune), ("scratch", a.scratch)):
        p = R / fn
        if not p.is_file():
            res["loops"][name] = {"status": "export missing"}
            continue
        res["sources"][fn] = H.sha256_file(p)
        res["loops"][name] = deltas(H.json_load(p))
    agree = {}
    for ck in ("best", "last"):
        f, s = res["loops"].get("finetune", {}).get(ck), res["loops"].get("scratch", {}).get(ck)
        if f and s:
            agree[ck] = {}
            for m in METRICS:
                if m in f and m in s:
                    df, ds = f[m]["A0_minus_A2"], s[m]["A0_minus_A2"]
                    ratio = (df / ds) if ds else None
                    agree[ck][m] = {"finetune_delta": df, "scratch_delta": ds, "same_sign": (df > 0) == (ds > 0),
                                    "ratio_finetune_over_scratch": ratio,
                                    "rough_magnitude_agree": (ratio is not None and 0.33 <= ratio <= 3.0)}
    res["agreement"] = agree
    res["summary"] = ("both loops complete" if all(res["loops"].get(k, {}).get("status", {}) and
                      all(v == "complete" for v in res["loops"][k]["status"].values()) for k in ("finetune", "scratch"))
                      else "partial: see loops.*.status")
    res["caveat"] = ("one seed per arm; a sign agreement here is a necessary condition for the fast loop, not evidence "
                     "about the arms themselves; the frozen protocol's seed spread is unknown until the 5-seed A0 gate")
    dest = R / "phase0_finetune_rankcheck.json"
    H.json_save(dest, res)
    print(res["summary"]); print({ck: {m: (round(v["finetune_delta"], 4), round(v["scratch_delta"], 4), v["same_sign"])
                                        for m, v in d.items()} for ck, d in agree.items()}); print("wrote", dest)


if __name__ == "__main__":
    main()
