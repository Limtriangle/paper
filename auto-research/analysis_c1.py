"""analysis_c1 — the pre-registered C1 analysis (candidates v5 C1, decision rules 1-7). Frozen before
launch: its sha256 is written into every output.

    python3 auto-research/analysis_c1.py                 # reads ralph/results/final_eval__test.json (+ oracle if present)
                                                         # -> ralph/results/c1__analysis.json
    python3 auto-research/analysis_c1.py --selftest      # synthetic data with a planted effect and a planted null
                                                         # -> ralph/results/phase0_analysis_selftest.json

Inputs: entries "<arm>_seed<s>" (final checkpoint) with per_image rows from final_eval_test.py.
Primary metric: psnr_gtmean (ONE scalar luminance gain). Contrasts A0-A1, A0-A2, A2-A3, A3-A4 paired by
seed: one-sample t (df = n-1), Holm across the four, exact sign-flip permutation (2^n patterns), TOST at
+-0.3 dB, and a mixed model psnr ~ arm + (1|image) + (1|seed) (statsmodels variance components).
Mechanism (A0 vs A2): per-decile paired deltas of hue_err and delta_e00 with seed-level t-CIs, bottom-3 vs
top-5 rule; darkness stress dose-response of the hue-error delta at x1, x0.5, x0.25.
Decomposition per arm: mse_raw = gain_error + mse_gtmean, log-exposure error.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

SCRIPT = Path(__file__).resolve()
LADDERS = {  # HVI-PLAN.md §4; verdict vocabulary: contributes | removable | inconclusive
    "s1": {"contrasts": (("L0", "L1"), ("L1", "L2"), ("L2", "L3"), ("L2", "L4")), "arms": ("L0", "L1", "L2", "L3", "L4"),
           "alias": {}, "src": "s1__loss_ladder_v1.json", "mechanism": None},
    "s2": {"contrasts": (("A0", "A1"), ("A0", "A2"), ("A2", "A3"), ("A3", "A4")), "arms": ("A0", "A1", "A2", "A3", "A4"),
           "alias": {"A0": "L2"}, "src": "s2__rep_ladder_v1.json", "mechanism": ("A0", "A2")},   # A0 under L2 == S1's L2 runs
}
CONTRASTS = LADDERS["s2"]["contrasts"]
MARGIN, SESOI, ALPHA = 0.3, 0.3, 0.05
LABEL_RE = re.compile(r"^(?:gate[A-D]_)?(?P<arm>[A-Z]\d?|R|U)_seed(?P<seed>\d+)$")


def load_entries(path):
    data = H.json_load(path)
    runs = {}
    for label, e in data["entries"].items():
        m = LABEL_RE.match(label)
        if m and e.get("kind", "final") == "final":
            runs.setdefault(m["arm"], {})[int(m["seed"])] = e
    return runs, data


def paired(delta):
    d = np.asarray(delta, float)
    n = len(d)
    mean, sd = float(d.mean()), float(d.std(ddof=1)) if n > 1 else float("nan")
    t = stats.ttest_1samp(d, 0.0)
    tcrit = stats.t.ppf(0.975, n - 1)
    ci = [mean - tcrit * sd / math.sqrt(n), mean + tcrit * sd / math.sqrt(n)]
    signs = [math.prod(s) for s in itertools.product([1, -1], repeat=n)]
    perm_means = [abs((d * np.array(s)).mean()) for s in itertools.product([1, -1], repeat=n)]
    perm_p = sum(1 for pm in perm_means if pm >= abs(mean) - 1e-12) / len(perm_means)
    se = sd / math.sqrt(n)
    p_lower = 1 - stats.t.cdf((mean + MARGIN) / se, n - 1)     # H0: mean <= -margin
    p_upper = stats.t.cdf((mean - MARGIN) / se, n - 1)         # H0: mean >= +margin
    return {"n": n, "delta_per_seed": d.tolist(), "mean": mean, "sd": sd, "ci95": ci,
            "t": float(t.statistic), "p": float(t.pvalue), "perm_p_two_sided": perm_p,
            "sign_agreement": int(max((d > 0).sum(), (d < 0).sum())),
            "tost": {"margin": MARGIN, "p_lower": float(p_lower), "p_upper": float(p_upper),
                     "equivalent": bool(max(p_lower, p_upper) < ALPHA)},
            "n_perm_patterns": len(signs)}


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, running = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(pvals) - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def mixed_model(rows_a, rows_b, arm_a, arm_b):
    """psnr ~ arm + (1|image) + (1|seed); rows = (seed, image, psnr)."""
    import pandas as pd
    import statsmodels.formula.api as smf
    df = pd.DataFrame([{"arm": arm_a, "seed": s, "image": i, "y": y} for s, i, y in rows_a] +
                      [{"arm": arm_b, "seed": s, "image": i, "y": y} for s, i, y in rows_b])
    df["g"] = 1
    df["arm"] = pd.Categorical(df["arm"], categories=[arm_b, arm_a])   # coefficient = a - b
    try:
        fit = smf.mixedlm("y ~ arm", df, groups="g", re_formula="0",
                          vc_formula={"image": "0 + C(image)", "seed": "0 + C(seed)"}).fit(reml=True)
        name = [c for c in fit.params.index if c.startswith("arm")][0]
        vc_names = list(getattr(fit.model, "exog_vc", None).names) if getattr(fit.model, "exog_vc", None) is not None else []
        return {"coef": float(fit.params[name]), "p": float(fit.pvalues[name]),
                "vc": dict(zip(vc_names, [float(v) for v in np.asarray(fit.vcomp).ravel()])),
                "residual_var": float(fit.scale), "converged": bool(fit.converged)}
    except Exception as ex:  # noqa: BLE001
        return {"error": str(ex)[:200]}


def seed_means(runs, arm, key="psnr_gtmean"):
    return {s: float(np.mean([r[key] for r in e["per_image"]])) for s, e in runs[arm].items()}


def decile_seed_means(entry, key):
    per = [[d[key] for d in r["deciles"]] for r in entry["per_image"]]
    w = [[d["n"] for d in r["deciles"]] for r in entry["per_image"]]
    out = []
    for k in range(10):
        num = sum(p[k] * n[k] for p, n in zip(per, w) if p[k] is not None)
        den = sum(n[k] for p, n in zip(per, w) if p[k] is not None)
        out.append(num / den if den else float("nan"))
    return out


def arm_summary(runs, metrics=("psnr", "psnr_gtmean", "ssim", "lpips", "delta_e00", "delta_e00_gtmean", "log_exposure")):
    """Per arm: mean and SD over seeds of the per-run image means (final-checkpoint test reads)."""
    out = {}
    for arm, seeds in runs.items():
        out[arm] = {"n_seeds": len(seeds), "seeds": sorted(seeds)}
        for m in metrics:
            vals = [float(np.mean([r[m] for r in e["per_image"]])) for e in seeds.values() if all(m in r for r in e["per_image"])]
            if vals:
                out[arm][m] = {"mean": float(np.mean(vals)), "sd": float(np.std(vals, ddof=1)) if len(vals) > 1 else None,
                               "per_seed": vals}
    return out


def mde(sd, n=5, alpha=ALPHA, power=0.8):
    """Paired minimum detectable effect (dB) for a one-sample t with df=n-1 at the given SD of the seed deltas."""
    if sd is None or not math.isfinite(sd):
        return None
    return float((stats.t.ppf(1 - alpha / 2, n - 1) + stats.t.ppf(power, n - 1)) * sd / math.sqrt(n))


def analyse(runs, ladder="s2"):
    L = LADDERS[ladder]
    runs = dict(runs)
    for arm, src in L["alias"].items():          # e.g. S2's A0 = S1's L2 runs
        if arm not in runs and src in runs:
            runs[arm] = runs[src]
    contrasts = L["contrasts"]
    res = {"ladder": ladder, "n_runs": {a: len(v) for a, v in runs.items()}, "contrasts": {}, "decision_rules": {},
           "arm_summary": arm_summary({a: runs[a] for a in L["arms"] if a in runs})}
    pvals, keys = [], []
    for a, b in contrasts:
        if a not in runs or b not in runs:
            res["contrasts"][f"{a}-{b}"] = {"status": "missing arm"}
            continue
        seeds = sorted(set(runs[a]) & set(runs[b]))
        ma, mb = seed_means(runs, a), seed_means(runs, b)
        c = paired([ma[s] - mb[s] for s in seeds])
        c["seeds"] = seeds
        c["mixed_model"] = mixed_model([(s, r["image"], r["psnr_gtmean"]) for s in seeds for r in runs[a][s]["per_image"]],
                                       [(s, r["image"], r["psnr_gtmean"]) for s in seeds for r in runs[b][s]["per_image"]], a, b)
        c["mde_db"] = mde(c["sd"], c["n"])
        ra, rb = seed_means(runs, a, "psnr"), seed_means(runs, b, "psnr")
        c["raw_psnr"] = paired([ra[s] - rb[s] for s in seeds])          # secondary: raw-PSNR contrast (exposure)
        res["contrasts"][f"{a}-{b}"] = c
        pvals.append(c["p"]); keys.append(f"{a}-{b}")
    for k, p_adj in zip(keys, holm(pvals)):
        c = res["contrasts"][k]
        c["p_holm"] = p_adj
        n = c["n"]
        # Holm-adjusted CI: widen to the level implied by the adjusted alpha
        sd, mean = c["sd"], c["mean"]
        alpha_k = ALPHA * c["p"] / c["p_holm"] if c["p_holm"] > 0 else ALPHA
        tcrit = stats.t.ppf(1 - alpha_k / 2, n - 1)
        c["ci_holm"] = [mean - tcrit * sd / math.sqrt(n), mean + tcrit * sd / math.sqrt(n)]
        excl0 = c["ci_holm"][0] > 0 or c["ci_holm"][1] < 0
        mm = c["mixed_model"]
        mm_agrees = ("coef" in mm) and (np.sign(mm["coef"]) == np.sign(mean))
        c["rule3_difference"] = {"a_ci_excludes_0_after_holm": bool(excl0),
                                 "b_effect_ge_sesoi_and_gt_2sd": bool(abs(mean) >= SESOI and abs(mean) > 2 * sd),
                                 "c_sign_agreement_ge_4of5": bool(c["sign_agreement"] >= math.ceil(0.8 * n)),
                                 "d_mixed_model_agrees": bool(mm_agrees)}
        c["verdict"] = ("contributes" if all(c["rule3_difference"].values()) else
                        "removable" if c["tost"]["equivalent"] else "inconclusive")
    # mechanism: A0 vs A2 deciles and stress (S2 only)
    if L["mechanism"] and all(x in runs for x in L["mechanism"]):
        seeds = sorted(set(runs["A0"]) & set(runs["A2"]))
        mech = {}
        for key in ("hue_err", "delta_e00"):
            d = np.array([[x - y for x, y in zip(decile_seed_means(runs["A0"][s], key), decile_seed_means(runs["A2"][s], key))] for s in seeds])
            per_dec = [paired(d[:, k]) for k in range(10)]
            bottom = paired(d[:, :3].mean(1)); top = paired(d[:, 5:].mean(1))
            mech[key] = {"per_decile": [{"decile": k, "mean": p["mean"], "ci95": p["ci95"]} for k, p in enumerate(per_dec)],
                         "bottom3": bottom, "top5": top,
                         "rule5": bool((bottom["ci95"][0] > 0 or bottom["ci95"][1] < 0) and
                                       ((top["ci95"][0] <= 0 <= top["ci95"][1]) or abs(top["mean"]) * 3 <= abs(bottom["mean"])))}
        stress = {}
        factors = sorted(runs["A0"][seeds[0]]["per_image"][0]["stress"], key=float, reverse=True)
        for f in factors:
            d = [np.mean([r["stress"][f]["hue_err_all"] for r in runs["A0"][s]["per_image"]]) -
                 np.mean([r["stress"][f]["hue_err_all"] for r in runs["A2"][s]["per_image"]]) for s in seeds]
            stress[f] = paired(d)
        absd = [abs(stress[f]["mean"]) for f in factors]
        mech["stress"] = {"factors": factors, "delta_hue_err_A0_minus_A2": {f: stress[f]["mean"] for f in factors},
                          "ci95": {f: stress[f]["ci95"] for f in factors},
                          "monotone_increasing_with_darkening": bool(all(x <= y for x, y in zip(absd, absd[1:])))}
        res["mechanism_A0_vs_A2"] = mech
    res["decomposition"] = {a: {k: float(np.mean([np.mean([r[k] for r in e["per_image"]]) for e in v.values()]))
                                for k in ("mse_raw", "mse_gtmean", "gain_error", "log_exposure", "psnr", "psnr_gtmean")}
                            for a, v in runs.items()}
    return res


def selection_bias(runs, oracle_path):
    if not Path(oracle_path).is_file():
        return {"status": "no oracle file"}
    od = H.json_load(oracle_path)["entries"]
    out = {}
    for arm, seeds in runs.items():
        rows = []
        for s, e in seeds.items():
            o = od.get(f"{arm}_seed{s}")
            if not o:
                continue
            final = float(np.mean([r["psnr_gtmean"] for r in e["per_image"]]))
            rows.append({"seed": s, "oracle_max": o["max_psnr_gtmean"], "final": final, "oracle_minus_final": o["max_psnr_gtmean"] - final})
        if rows:
            d = [r["oracle_minus_final"] for r in rows]
            out[arm] = {"per_seed": rows, "oracle_minus_final_mean": float(np.mean(d)), "sd": float(np.std(d, ddof=1)) if len(d) > 1 else None,
                        "paper_style_max_over_seeds": max(r["oracle_max"] for r in rows),
                        "warning": "oracle numbers are never used to rank arms"}
    return out


# ---- synthetic self-test -------------------------------------------------------------------
def synthetic(effects, seed=0, n_seeds=5, n_images=15, sd_seed=0.15, sd_image=1.5, sd_eps=0.08):
    rng = np.random.default_rng(seed)
    arms = list(effects)
    u = rng.normal(0, sd_seed, n_seeds)
    v = rng.normal(0, sd_image, n_images)
    entries = {}
    for a in arms:
        for s in range(n_seeds):
            rows = []
            for i in range(n_images):
                y = effects[a]["psnr"] + u[s] + v[i] + rng.normal(0, sd_eps)
                dec = [{"decile": k, "n": 1000, "hue_err": effects[a]["hue_bottom"] if k < 3 else 0.02,
                        "delta_e00": (8.0 + effects[a]["de_bottom"]) if k < 3 else 6.0, "rgb_mse": 0.01} for k in range(10)]
                for d in dec:
                    d["hue_err"] += rng.normal(0, 0.002); d["delta_e00"] += rng.normal(0, 0.05)
                stress = {str(f): {"hue_err_all": 0.03 + effects[a]["stress_slope"] * (1 - f) + rng.normal(0, 0.002)} for f in (1.0, 0.5, 0.25)}
                rows.append({"image": f"img{i}", "psnr_gtmean": y, "psnr": y - 4, "mse_raw": 0.02, "mse_gtmean": 0.012,
                             "gain_error": 0.008, "log_exposure": -0.2, "deciles": dec, "stress": stress})
            entries[f"{a}_seed{s + 42}"] = {"kind": "final", "per_image": rows}
    return {"entries": entries}


def selftest():
    base = {"psnr": 27.7, "hue_bottom": 0.05, "de_bottom": 0.0, "stress_slope": 0.0}
    effects = {"A0": dict(base),
               "A1": dict(base),                                                    # planted NULL (A0-A1 = 0)
               "A2": dict(base, psnr=27.1, hue_bottom=0.07, de_bottom=1.0, stress_slope=0.04),  # planted EFFECT (+0.6 dB, dark-pixel hue)
               "A3": dict(base, psnr=27.1, hue_bottom=0.07, de_bottom=1.0),          # A2-A3 = 0 (null)
               "A4": dict(base, psnr=26.95, hue_bottom=0.07, de_bottom=1.0)}         # A3-A4 = +0.15 (below SESOI)
    data = synthetic(effects)
    runs = {}
    for label, e in data["entries"].items():
        m = LABEL_RE.match(label); runs.setdefault(m["arm"], {})[int(m["seed"])] = e
    res = analyse(runs, "s2")
    planted = {"A0-A1": 0.0, "A0-A2": 0.6, "A2-A3": 0.0, "A3-A4": 0.15}
    out = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "script_sha256": H.sha256_file(SCRIPT),
           "synthetic_model": "psnr = arm_mean + seed(0.15) + image(1.5) + eps(0.08); 5 seeds x 15 images; hue_err/dE00 planted in deciles 0-2 of A2/A3/A4; stress slope planted in A2",
           "planted_delta_db": planted,
           "outcomes": {k: {"planted": planted[k], "estimated": c["mean"], "ci_holm": c["ci_holm"], "p": c["p"], "p_holm": c["p_holm"],
                            "perm_p": c["perm_p_two_sided"], "tost_equivalent": c["tost"]["equivalent"],
                            "mixed_model": c["mixed_model"], "verdict": c["verdict"]}
                        for k, c in res["contrasts"].items()},
           "mechanism": {"hue_err_rule5": res["mechanism_A0_vs_A2"]["hue_err"]["rule5"],
                         "delta_e00_rule5": res["mechanism_A0_vs_A2"]["delta_e00"]["rule5"],
                         "stress_monotone": res["mechanism_A0_vs_A2"]["stress"]["monotone_increasing_with_darkening"],
                         "stress_delta": res["mechanism_A0_vs_A2"]["stress"]["delta_hue_err_A0_minus_A2"]}}
    exp = {"A0-A1": "removable", "A0-A2": "contributes", "A2-A3": "removable", "A3-A4": "removable"}
    out["expected_verdicts"] = exp
    out["expected_note"] = ("A3-A4 plants +0.15 dB: below the 0.3 dB SESOI (rule 3b fails) and inside the +-0.3 dB TOST "
                            "margin with the small synthetic seed SD, so 'removable' is the correct verdict; vocabulary = "
                            "HVI-PLAN §4 (contributes / removable / inconclusive)")
    out["arm_summary_keys_present"] = all(k in res["arm_summary"].get("A0", {}) for k in ("psnr", "psnr_gtmean"))
    out["mde_db_A0-A2"] = res["contrasts"]["A0-A2"]["mde_db"]
    out["all_as_expected"] = all(out["outcomes"][k]["verdict"] == v for k, v in exp.items()) and \
        out["mechanism"]["hue_err_rule5"] and out["mechanism"]["stress_monotone"]
    dest = H.PAPER / "ralph" / "results" / "phase0_analysis_selftest.json"
    H.json_save(dest, out)
    print(json.dumps({k: (v["verdict"], round(v["estimated"], 3), round(v["p_holm"], 4)) for k, v in out["outcomes"].items()}, indent=1))
    print("mechanism", out["mechanism"]); print("all_as_expected", out["all_as_expected"]); print("wrote", dest)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--input", default=str(H.PAPER / "ralph" / "results" / "final_eval__test.json"))
    ap.add_argument("--oracle", default=str(H.PAPER / "ralph" / "results" / "final_eval__oracle.json"))
    a = ap.parse_args()
    if a.selftest:
        selftest(); return
    runs, data = load_entries(a.input)
    R = H.PAPER / "ralph" / "results"
    sources = {Path(a.input).name: H.sha256_file(a.input)}
    if Path(a.oracle).is_file():
        sources[Path(a.oracle).name] = H.sha256_file(a.oracle)
    stamp = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "script_sha256": H.sha256_file(SCRIPT), "sources": sources,
             "status": "complete", "test15": "read once per label by final_eval_test.py; these are those reads"}
    # writing's contract (DECISIONS 2026-09-24 06:10): <src>.analysis.analysis_s{1,2,3}.decision.*
    RUN_DIRS = {"s1": H.OUTPUTS / "s1" / "loss_ladder_v1", "s2": H.OUTPUTS / "s2" / "rep_ladder_v1"}
    for ladder in ("s1", "s2"):
        dec = analyse(runs, ladder)
        dec.update(stamp)
        rd = RUN_DIRS[ladder]
        if rd.is_dir():   # export_results.py merges <run>/analysis_<ladder>/decision.json as analysis.analysis_<ladder>.decision
            (rd / f"analysis_{ladder}").mkdir(exist_ok=True)
            H.json_save(rd / f"analysis_{ladder}" / "decision.json", dec)
            print("wrote", rd / f"analysis_{ladder}" / "decision.json", "-> run export_results.py --run", f"{ladder}/{rd.name}")
        else:
            out = {"run_id": LADDERS[ladder]["src"][:-5], "analysis": {f"analysis_{ladder}": {"decision": dec}}, **stamp}
            H.json_save(R / LADDERS[ladder]["src"], out)
            print("wrote", R / LADDERS[ladder]["src"])
        print(ladder, {k: v.get("verdict") for k, v in dec["contrasts"].items()})
    s3 = {"run_id": "s3__selection_bias_v1", "analysis": {"analysis_s3": {"decision": selection_bias(runs, a.oracle)}}, **stamp}
    H.json_save(R / "s3__selection_bias_v1.json", s3)
    print("wrote", R / "s3__selection_bias_v1.json")


if __name__ == "__main__":
    main()
