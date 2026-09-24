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


def curve_summary(export, res, every=5):
    """Per-epoch validation curve (ungated PSNR + gated if present) read from each job's metrics.csv
    (sha256 recorded in sources); rows at epochs 1, every k-th, best and last; A0 - A2 at shared epochs."""
    import csv
    out = {}
    for j in PAIR:
        p = Path(export["root"]) / j / "metrics.csv"
        if not p.is_file():
            continue
        res["sources"][f"{export['run_id']}/{j}/metrics.csv"] = H.sha256_file(p)
        rows = [r for r in csv.DictReader(open(p)) if r.get("val_psnr") not in ("", None)]
        curve = {int(r["epoch"]): float(r["val_psnr"]) for r in rows}
        best = max(curve, key=curve.get) if curve else None
        keep = sorted({e for e in curve if e == 1 or e % every == 0 or e == best or e == max(curve)})
        out[j] = {"val_psnr_by_epoch": {str(e): curve[e] for e in keep}, "best_epoch": best,
                  "best_val_psnr": curve.get(best), "last_epoch": max(curve) if curve else None,
                  "last_val_psnr": curve.get(max(curve)) if curve else None, "n_validated_epochs": len(curve)}
    if all(j in out for j in PAIR):
        a, b = out[PAIR[0]]["val_psnr_by_epoch"], out[PAIR[1]]["val_psnr_by_epoch"]
        out["A0_minus_A2_by_epoch"] = {e: a[e] - b[e] for e in a if e in b}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finetune", default="finetune__rankcheck_v2.json")
    ap.add_argument("--scratch", default="baseline__rankcheck_v2.json")
    a = ap.parse_args()
    R = H.PAPER / "ralph" / "results"
    res = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "pair": PAIR, "split": "scene_v1 validation (40 images)",
           "test15": "NEVER READ", "sources": {}, "loops": {},
           "labels": {"finetune": "50-epoch fine-tune from released w_perc (lr 3e-5), one seed",
                      "scratch": "LADDER SEED 1: from-scratch 1000-epoch frozen protocol, the true A0 - A2 gap (one seed, not citable)"},
           "notes": ["DATA (2026-09-24): the released w_perc weights were trained with k = 1.1255; arm A2 replaces the "
                     "transform by k = 0, so its fine-tune starts from a representation mismatch: A0 - A2 = +15.8 dB "
                     "after epoch 1, +7.7 dB after epoch 50, A2 peaking at epoch 7 then declining. The fine-tune loop "
                     "therefore does not test the arms; it measures recovery from the mismatch.",
                     "RULE (DECISIONS 2026-09-24, master): the fast loop is valid only for components whose init "
                     "reproduces the released output; hvi_baseline.py --preflight-release enforces it (tol 1e-5).",
                     "The 'sign_and_magnitude_comparison' block below is descriptive only; it is NOT a loop-validity "
                     "verdict for this pair because of the mismatch above."]}
    for name, fn in (("finetune", a.finetune), ("scratch", a.scratch)):
        p = R / fn
        if not p.is_file():
            res["loops"][name] = {"status": "export missing"}
            continue
        res["sources"][fn] = H.sha256_file(p)
        export = H.json_load(p)
        res["loops"][name] = deltas(export)
        res["loops"][name]["curve_summary"] = curve_summary(export, res)
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
    res["sign_and_magnitude_comparison"] = agree
    # HVI-PLAN §3: on-disk runs may be reused as seed 42 of an arm only if their manifest hashes equal the frozen ones
    frozen = H.OUTPUTS / "gateA" / "a0_l0_v1" / "manifest.json"
    rc = H.OUTPUTS / "baseline" / "rankcheck_v2" / "manifest.json"
    if frozen.is_file() and rc.is_file():
        fm, rm = H.json_load(frozen), H.json_load(rc)
        cmp = {k: {"frozen": fm.get(k), "rankcheck_v2": rm.get(k), "equal": fm.get(k) == rm.get(k)}
               for k in ("script_sha256", "lib_sha256", "arms_sha256", "split_sha256")}
        cmp["k0"] = {"frozen": fm["protocol"]["k0"], "rankcheck_v2": rm["protocol"]["k0"],
                     "equal": fm["protocol"]["k0"] == rm["protocol"]["k0"]}
        reusable = all(v["equal"] for v in cmp.values())
        res["frozen_hash_check"] = {"comparison": cmp, "reusable_as_L2_seed42": reusable,
                                    "verdict": ("rankcheck_v2 may be reused as L2-A0/L2-A2 seed 42" if reusable else
                                                "NOT reusable: code hashes and/or k0 differ from the frozen protocol "
                                                "(rankcheck_v2 used k0 = 0.2; frozen k0 = 1.1255) -> S2 seed 42 must be re-run")}
        res["notes"].append(res["frozen_hash_check"]["verdict"])
    res["summary"] = ("both loops complete" if all(res["loops"].get(k, {}).get("status", {}) and
                      all(v == "complete" for v in res["loops"][k]["status"].values()) for k in ("finetune", "scratch"))
                      else "partial: see loops.*.status")
    res["caveat"] = ("one seed per arm; the frozen protocol's seed spread is unknown until the 5-seed A0 gate; "
                     "the scratch pair is ladder seed 1 of the A0 vs A2 contrast, not a loop test")
    dest = R / "phase0_finetune_rankcheck.json"
    H.json_save(dest, res)
    print(res["summary"]); print({ck: {m: (round(v["finetune_delta"], 4), round(v["scratch_delta"], 4), v["same_sign"])
                                        for m, v in d.items()} for ck, d in agree.items()}); print("wrote", dest)


if __name__ == "__main__":
    main()
