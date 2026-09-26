"""s4_oracle_decomp — S4 / T3 GT-oracle decomposition of HVI-CIDNet's brightness-shift failure
(HVI-PLAN §4 S4; ralph/related/redteam/R4_T3_design_redteam.md, revised design, "O-gain / O-all oracles").
Zero training. CPU only (run under nice 19). Released LOL-v1 w_perc weights. VALIDATION images only.

    python3 auto-research/s4_oracle_decomp.py --preflight          # 1 image, 1 shift, tiny grids; writes nothing under ralph/
    nice -n 19 python3 auto-research/s4_oracle_decomp.py --run oracle_decomp_v1 --threads 4
    python3 auto-research/s4_oracle_decomp.py --aggregate --run oracle_decomp_v1   # -> ralph/results/s4__oracle_decomp_v1.json

Shifts applied to each low input x (40 scene_v1 validation images; scene clusters = replication unit):
  none; GT-blend a in {0.1, 0.2, 0.35, 0.5}: x' = (1-a) x + a GT (MILL-style, injects GT);
  linear gain g in {0.5, 2, 4}: x' = sRGB(clip(g * lin(x))) (R4 protocol (i), no GT in the input).
Knobs (released model): pre-gain p (x -> clip(p x)), input gamma y (x -> x**y, eval.py), density k,
alpha_s (gated saturation gain, PHVIT), alpha_i (gated2 output intensity gain).
Arms per (image, shift):
  ID     output = shifted input (no network)
  F0     frozen, official LOL-v1 knobs (eval.py --lol: gated alpha_s 1.3; p=y=alpha_i=1; k = released 1.1255)
  F0i    frozen, identity knobs (alpha_s off)
  G0     closed-form mean-match pre-gain p0 = mean(train low) / mean(x'), official knobs
  O-gain GT-oracle over p only (other knobs official)
  O-all  GT-oracle over (p, y, k, alpha_s, alpha_i): coordinate descent from O-gain's optimum, 2 sweeps
Each oracle is run twice: objective P1 = raw PSNR, objective P2 = GT-mean PSNR (one scalar luminance gain).
Metrics per output: raw / GT-mean PSNR, SSIM, CIEDE2000 total, its lightness part (pred L*, GT a*b*) and its
chroma/hue part (GT L*, pred a*b*), clipped-pixel fraction. Oracle = uses GT: an UPPER BOUND, not a method.
Caveat recorded in the JSON: the validation images are part of the released model's training data.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

STUDY = "s4"
WEIGHTS = H.ROOT / "weights" / "LOLv1_wperc" / "model.safetensors"
BLENDS = (0.1, 0.2, 0.35, 0.5)
GAINS = (0.5, 2.0, 4.0)
OFFICIAL = {"p": 1.0, "y": 1.0, "k": None, "a_s": 1.3, "a_i": 1.0}     # k filled with the released value
GRID = {"p": [round(2 ** (e / 4), 4) for e in range(-8, 9)],          # 0.25 .. 4, 17 log-spaced
        "y": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.4, 1.6, 1.8, 2.0],
        "k": [0.0, 0.25, 0.5, 0.75, 1.1255, 1.5, 2.0, 3.0],
        "a_s": [round(0.8 + 0.1 * i, 2) for i in range(11)],             # 0.8 .. 1.8
        "a_i": [round(0.6 + 0.05 * i, 2) for i in range(21)]}            # 0.6 .. 1.6
FULL = ("p", "y", "k")          # need a network forward
CHEAP = ("a_s", "a_i")          # decoder-side only


# ------------------------------------------------------------------ colour helpers
def srgb_to_lin(x):
    import torch
    return torch.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(x):
    import torch
    x = x.clamp(0, 1)
    return torch.where(x <= 0.0031308, 12.92 * x, 1.055 * x.clamp_min(1e-12) ** (1 / 2.4) - 0.055).clamp(0, 1)


def shifts(low, gt):
    out = {"none": low}
    for a in BLENDS:
        out[f"blend{a}"] = ((1 - a) * low + a * gt).clamp(0, 1)
    for g in GAINS:
        out[f"gain{g}"] = lin_to_srgb(srgb_to_lin(low) * g)
    return out


def full_metrics(pred, gt, gt_u8, lp=None):
    import numpy as np
    import c1_metrics as M
    from skimage.color import rgb2lab, deltaE_ciede2000
    m = M.image_metrics(pred, gt, lp)
    pl, gl = M._lab(pred), M._lab(gt)
    light = np.concatenate([pl[..., :1], gl[..., 1:]], -1)
    chrom = np.concatenate([gl[..., :1], pl[..., 1:]], -1)
    m["delta_e00_lightness"] = float(deltaE_ciede2000(gl, light).mean())
    m["delta_e00_chroma_hue"] = float(deltaE_ciede2000(gl, chrom).mean())
    m["clip_frac"] = float((pred >= 254.5 / 255).any(0).float().mean())
    return m


class Model:
    """Released CIDNet with test-time knobs; caches the network part per (p, y, k)."""

    def __init__(self, threads):
        import torch
        import safetensors.torch as sf
        import c1_arms as C
        torch.set_num_threads(threads)
        self.net = C.build_arm("L0", 0)
        self.info = self.net.load_pretrained(sf.load_file(str(WEIGHTS)))
        self.net.eval()
        self.k_released = self.info["released_k"]
        self.cache = {}

    def hvi_out(self, x, p, y, k):
        import torch
        key = (p, y, k)
        if key not in self.cache:
            xin = (x * p).clamp(0, 1) ** y
            with torch.no_grad():
                self.net.trans.density_k.data.fill_(k)
                xe, i = self.net.encode(xin.unsqueeze(0))
                hv0, i0 = self.net.body(xe, i)
                self.cache[key] = torch.cat([hv0, i0], 1) + xe      # output_hvi (net/CIDNet.py:119)
                self.cache[key + ("this_k",)] = self.net.trans.this_k
        return self.cache[key], self.cache[key + ("this_k",)]

    def decode(self, out_hvi, this_k, a_s, a_i):
        import torch
        t = self.net.trans
        t.this_k = this_k
        t.gated, t.alpha_s = (a_s != 1.0), a_s
        t.gated2, t.alpha = (a_i != 1.0), a_i
        try:
            with torch.no_grad():
                return t.PHVIT(out_hvi).clamp(0, 1)[0]
        finally:
            t.gated = t.gated2 = False
            t.alpha_s, t.alpha = 1.3, 1.0

    def run(self, x, kn):
        o, tk = self.hvi_out(x, kn["p"], kn["y"], kn["k"])
        return self.decode(o, tk, kn["a_s"], kn["a_i"])


def objective(pred, gt, gt_u8, which):
    import c1_metrics as M
    if which == "P1":
        return float(H.calculate_psnr(H.to_uint8_hwc(pred), gt_u8))
    _, pg = M.scalar_gain(pred, gt)
    return float(H.calculate_psnr(H.to_uint8_hwc(pg), gt_u8))


def oracle(model, x, gt, gt_u8, which, start, knobs, sweeps=2):
    best = dict(start)
    best_v = objective(model.run(x, best), gt, gt_u8, which)
    evals = 1
    for _ in range(sweeps):
        improved = False
        for name in knobs:
            for v in GRID[name]:
                if v == best[name]:
                    continue
                cand = dict(best, **{name: v})
                val = objective(model.run(x, cand), gt, gt_u8, which)
                evals += 1
                if val > best_v + 1e-9:
                    best, best_v, improved = cand, val, True
        if not improved:
            break
    return best, best_v, evals


def process_image(model, name, mu_train, lp, grids_small=False):
    x0, gt, gt_u8 = H.load_val_pair(name)
    recs = []
    off = dict(OFFICIAL, k=model.k_released)
    for sname, x in shifts(x0, gt).items():
        model.cache.clear()
        t0 = time.time()
        mu_in = float(x.mean())
        arms = {"ID": (x, None), "F0": (model.run(x, off), off), "F0i": (model.run(x, dict(off, a_s=1.0)), dict(off, a_s=1.0))}
        p0 = mu_train / max(mu_in, 1e-6)
        g0 = dict(off, p=p0)
        arms["G0"] = (model.run(x, g0), g0)
        for which in ("P1", "P2"):
            kg, _, _ = oracle(model, x, gt, gt_u8, which, off, ("p",), sweeps=1)
            arms[f"O-gain-{which}"] = (model.run(x, kg), kg)
            ka, _, n = oracle(model, x, gt, gt_u8, which, kg, ("p", "y", "k", "a_s", "a_i"))
            arms[f"O-all-{which}"] = (model.run(x, ka), ka)
        rec = {"image": name, "shift": sname, "mu_in": mu_in, "p0": p0, "seconds": None, "forwards": len([k for k in model.cache if len(k) == 3]), "arms": {}}
        for arm, (pred, kn) in arms.items():
            rec["arms"][arm] = {"knobs": kn, **full_metrics(pred, gt, gt_u8, lp)}
        rec["seconds"] = time.time() - t0
        recs.append(rec)
    return recs


def val_scenes(names):
    """Scene clusters of the validation images (same DINOv2 + pHash rule as scene_split.py). Val = union of whole
    clusters, so components computed on the val images alone equal the global ones."""
    import numpy as np
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    import scene_split as S
    imgs = [H.open_rgb(H.TRAIN_DIR / "high" / n) for n in names]
    hashes = np.stack([S.phash(im) for im in imgs])
    emb, model_name = S.embed(imgs, "cpu")
    cos = (emb @ emb.T).numpy()
    ham = (hashes[:, None, :] != hashes[None, :, :]).sum(-1)
    adj = ((cos >= S.COS_EDGE) | (ham <= S.HASH_EDGE)) & ~np.eye(len(names), dtype=bool)
    ii, jj = np.nonzero(adj)
    n, lab = connected_components(coo_matrix((np.ones(len(ii)), (ii, jj)), shape=(len(names),) * 2), directed=False)
    return {nm: int(l) for nm, l in zip(names, lab)}, int(n), model_name


def mean_train_low(names):
    from torchvision.transforms.functional import to_tensor
    return statistics.mean(float(to_tensor(H.open_rgb(H.TRAIN_DIR / "low" / n)).mean()) for n in names)


def run(args):
    import torch
    H.import_repo()
    H.set_determinism(args.threads)
    split = H.load_split("scene_v1")
    out = H.OUTPUTS / STUDY / args.run
    out.mkdir(parents=True, exist_ok=False)
    names = split["val"][:1] if args.preflight else split["val"]
    scenes, n_sc, emb_model = val_scenes(split["val"])
    H.require(n_sc == len(split["val_clusters"]), f"scene count {n_sc} != split's {len(split['val_clusters'])}")
    mu = mean_train_low(split["train"])
    lp = H.LPIPSMetric("cpu")
    model = Model(args.threads)
    if args.preflight:
        for k in GRID:
            GRID[k] = GRID[k][::4] if len(GRID[k]) > 4 else GRID[k]
        global BLENDS, GAINS
        BLENDS, GAINS = (0.35,), (2.0,)
    manifest = {"study": STUDY, "run": args.run, "created_at": time.time(), "script_sha256": H.sha256_file(Path(__file__)),
                "lib_sha256": H.sha256_file(HERE / "hvilib.py"), "metrics_sha256": H.sha256_file(HERE / "c1_metrics.py"),
                "weights": str(WEIGHTS), "weights_sha256": H.sha256_file(WEIGHTS), "k_released": model.k_released,
                "split_sha256": split["sha256"], "images": names, "scenes": scenes, "n_scenes": n_sc, "scene_embedding": emb_model,
                "mu_train_low": mu, "blends": BLENDS, "gains": GAINS, "grid": GRID, "official_knobs": dict(OFFICIAL, k=model.k_released),
                "threads": args.threads, "device": "cpu", "nice": os.nice(0), "preflight": bool(args.preflight),
                "test15": "NEVER READ", "caveat": "validation images are part of the released model's training data"}
    H.json_save(out / "manifest.json", manifest)
    rec_f = out / "records.jsonl"
    H.json_save(out / "status.json", {"state": "running", "pid": os.getpid(), "done": 0, "total": len(names)})
    try:
        for i, n in enumerate(names):
            recs = process_image(model, n, mu, lp)
            with rec_f.open("a") as f:
                for r in recs:
                    r["scene"] = scenes[n]
                    f.write(json.dumps(r) + "\n")
            H.json_save(out / "status.json", {"state": "running", "pid": os.getpid(), "done": i + 1, "total": len(names),
                                              "last_image_seconds": sum(r["seconds"] for r in recs), "updated_at": time.time()})
            print(f"{i+1}/{len(names)} {n}: {sum(r['seconds'] for r in recs):.0f}s", flush=True)
        H.json_save(out / "status.json", {"state": "complete", "pid": os.getpid(), "done": len(names), "total": len(names)})
    except Exception:
        import traceback
        (out / "error.txt").write_text(traceback.format_exc())
        H.json_save(out / "status.json", {"state": "failed", "pid": os.getpid()})
        raise
    if args.preflight:
        r = [json.loads(l) for l in rec_f.read_text().splitlines()]
        print("PREFLIGHT", {x["shift"]: {a: round(v["psnr"], 2) for a, v in x["arms"].items()} for x in r})


# ------------------------------------------------------------------ extra arm: O-gain+gamma (master approval 2026-09-26)
def run_gain_gamma(args):
    """Attribution pass inside S4: oracle over (pre-gain p, input gamma y) only, other knobs official, coordinate
    descent from the O-gain optimum (2 sweeps), both objectives. Appends to records_gg.jsonl in the same run dir
    (records.jsonl is not modified). Same images, shifts, grids and metrics as the main pass."""
    H.import_repo()
    H.set_determinism(args.threads)
    out = H.OUTPUTS / STUDY / args.run
    man = H.json_load(out / "manifest.json")
    H.require(H.json_load(out / "status.json")["state"] == "complete", "main pass not complete")
    gg = out / "records_gg.jsonl"
    H.require(not gg.exists(), f"{gg} exists; no overwrite")
    main_recs = [json.loads(l) for l in (out / "records.jsonl").read_text().splitlines()]
    start = {(r["image"], r["shift"], w): r["arms"][f"O-gain-{w}"]["knobs"] for r in main_recs for w in ("P1", "P2")}
    lp = H.LPIPSMetric("cpu")
    model = Model(args.threads)
    H.json_save(out / "status_gg.json", {"state": "running", "pid": os.getpid(), "done": 0, "total": len(man["images"])})
    for i, name in enumerate(man["images"]):
        x0, gt, gt_u8 = H.load_val_pair(name)
        with gg.open("a") as fh:
            for sname, x in shifts(x0, gt).items():
                model.cache.clear()
                rec = {"image": name, "shift": sname, "scene": man["scenes"][name], "arms": {}}
                for w in ("P1", "P2"):
                    k0 = dict(start[(name, sname, w)])
                    kn, _, _ = oracle(model, x, gt, gt_u8, w, k0, ("p", "y"))
                    rec["arms"][f"O-gg-{w}"] = {"knobs": kn, **full_metrics(model.run(x, kn), gt, gt_u8, lp)}
                fh.write(json.dumps(rec) + "\n")
        H.json_save(out / "status_gg.json", {"state": "running", "pid": os.getpid(), "done": i + 1, "total": len(man["images"])})
        print(f"gg {i+1}/{len(man['images'])} {name}", flush=True)
    H.json_save(out / "status_gg.json", {"state": "complete", "pid": os.getpid(), "done": len(man["images"]), "total": len(man["images"])})


# ------------------------------------------------------------------ aggregation
def boot_ci(vals, n=10000, seed=0):
    rng = random.Random(seed)
    if len(vals) < 2:
        return [None, None]
    ms = sorted(statistics.mean(rng.choices(vals, k=len(vals))) for _ in range(n))
    return [ms[int(0.025 * n)], ms[int(0.975 * n) - 1]]


def aggregate(args):
    from scipy import stats
    out = H.OUTPUTS / STUDY / args.run
    man = H.json_load(out / "manifest.json")
    H.require(H.json_load(out / "status.json")["state"] == "complete", "run not complete")
    recs = [json.loads(l) for l in (out / "records.jsonl").read_text().splitlines()]
    gg_f = out / "records_gg.jsonl"
    has_gg = gg_f.is_file() and (out / "status_gg.json").is_file() and H.json_load(out / "status_gg.json")["state"] == "complete"
    if has_gg:
        extra = {(r["image"], r["shift"]): r["arms"] for r in (json.loads(l) for l in gg_f.read_text().splitlines())}
        for r in recs:
            r["arms"].update(extra[(r["image"], r["shift"])])
    metrics = ("psnr", "psnr_gtmean", "delta_e00", "delta_e00_gtmean", "delta_e00_lightness", "delta_e00_chroma_hue", "clip_frac", "ssim")
    arms = sorted(recs[0]["arms"])
    groups = {"none": ["none"], "blend_20_50": ["blend0.2", "blend0.35", "blend0.5"], "blend_all": [f"blend{a}" for a in man["blends"]],
              "gain_all": [f"gain{g}" for g in man["gains"]], "shifted_all": [f"blend{a}" for a in man["blends"]] + [f"gain{g}" for g in man["gains"]]}
    groups.update({s: [s] for s in {r["shift"] for r in recs}})

    def scene_means(shift_set, arm, metric):
        per = {}
        for r in recs:
            if r["shift"] in shift_set:
                per.setdefault(r["scene"], []).append(r["arms"][arm][metric])
        return {s: statistics.mean(v) for s, v in per.items()}

    summary = {}
    for g, ss in groups.items():
        summary[g] = {}
        for arm in arms:
            summary[g][arm] = {}
            for m in metrics:
                sm = list(scene_means(ss, arm, m).values())
                summary[g][arm][m] = {"mean": statistics.mean(sm), "ci95_scene_bootstrap": boot_ci(sm), "n_scenes": len(sm)}

    def contrast(ss, a, b, metric):
        A_, B_ = scene_means(ss, a, metric), scene_means(ss, b, metric)
        d = [A_[s] - B_[s] for s in sorted(A_)]
        w = stats.wilcoxon(d) if any(abs(x) > 0 for x in d) else None
        return {"mean": statistics.mean(d), "ci95_scene_bootstrap": boot_ci(d), "n_scenes": len(d),
                "wilcoxon_p": (float(w.pvalue) if w else 1.0)}

    d1 = {}
    for g in ("blend_20_50", "gain_all", "shifted_all", "none"):
        d1[g] = {"P1_raw_psnr__O_all_minus_O_gain": contrast(groups[g], "O-all-P1", "O-gain-P1", "psnr"),
                 "P2_gtmean_psnr__O_all_minus_O_gain": contrast(groups[g], "O-all-P2", "O-gain-P2", "psnr_gtmean"),
                 "P2_dE00_chroma_hue__O_all_minus_O_gain": contrast(groups[g], "O-all-P2", "O-gain-P2", "delta_e00_chroma_hue"),
                 "P2_dE00__O_all_minus_O_gain": contrast(groups[g], "O-all-P2", "O-gain-P2", "delta_e00"),
                 "G0_minus_F0_raw_psnr": contrast(groups[g], "G0", "F0", "psnr"),
                 "O_gain_minus_F0_raw_psnr": contrast(groups[g], "O-gain-P1", "F0", "psnr"),
                 "O_all_minus_F0_raw_psnr": contrast(groups[g], "O-all-P1", "F0", "psnr")}
        og, oa, g0 = (d1[g]["O_gain_minus_F0_raw_psnr"]["mean"], d1[g]["O_all_minus_F0_raw_psnr"]["mean"],
                      d1[g]["G0_minus_F0_raw_psnr"]["mean"])
        d1[g]["share_of_oracle_recovery_by_gain_only"] = (og / oa) if oa > 1e-9 else None
        d1[g]["share_of_oracle_recovery_by_G0"] = (g0 / oa) if oa > 1e-9 else None
        if has_gg:
            d1[g]["D1_split"] = {
                "P1_raw_psnr__O_gg_minus_O_gain": contrast(groups[g], "O-gg-P1", "O-gain-P1", "psnr"),
                "P1_raw_psnr__O_all_minus_O_gg": contrast(groups[g], "O-all-P1", "O-gg-P1", "psnr"),
                "P2_gtmean_psnr__O_gg_minus_O_gain": contrast(groups[g], "O-gg-P2", "O-gain-P2", "psnr_gtmean"),
                "P2_gtmean_psnr__O_all_minus_O_gg": contrast(groups[g], "O-all-P2", "O-gg-P2", "psnr_gtmean"),
                "P2_dE00_chroma_hue__O_all_minus_O_gg": contrast(groups[g], "O-all-P2", "O-gg-P2", "delta_e00_chroma_hue"),
                "note": "O-gg = oracle over pre-gain + input gamma only; O-all adds k, alpha_s, alpha_i on top"}
        d1[g]["D1_rule"] = {"O_all_minus_O_gain_P1_lt_0.3dB": d1[g]["P1_raw_psnr__O_all_minus_O_gain"]["mean"] < 0.3,
                            "O_all_minus_O_gain_dE00_lt_1": abs(d1[g]["P2_dE00__O_all_minus_O_gain"]["mean"]) < 1.0}
    traj = {}
    sh = [r for r in recs if r["shift"] != "none"]
    for kn in ("p", "y", "k", "a_s", "a_i"):
        for which in ("P1", "P2"):
            v = [r["arms"][f"O-all-{which}"]["knobs"][kn] for r in sh]
            rho = stats.spearmanr([r["mu_in"] for r in sh], v)
            traj[f"{kn}__{which}"] = {"spearman_rho_vs_mu_in": float(rho.statistic), "p": float(rho.pvalue),
                                      "median": statistics.median(v), "n_image_shifts": len(v),
                                      "note": "image-level (pseudo-replicated); descriptive only"}
    res = {"run_id": "s4__oracle_decomp_v1", "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "design": "HVI-PLAN §4 S4 / R4 revised design: GT-oracle decomposition, zero training, CPU, released w_perc",
           "protocol": {k: man[k] for k in ("blends", "gains", "grid", "official_knobs", "mu_train_low", "n_scenes", "k_released", "threads", "device")},
           "replication_unit": "scene (validation scene clusters); images averaged within scene per shift group",
           "caveats": ["validation images are part of the released model's training data (memorised); scenes are disjoint from eval15",
                       "oracle arms select knobs with the GT: upper bounds, not methods",
                       "blend shifts inject GT into the input; gain shifts do not"],
           "summary": summary, "decomposition": d1, "knob_trajectories": traj, "n_records": len(recs), "n_images": len(man["images"]),
           "gain_gamma_arm": ("included (O-gg-P1/P2; D1_split under decomposition.<group>)" if has_gg else "not run"),
           "sources": {"manifest.json": H.sha256_file(out / "manifest.json"), "records.jsonl": H.sha256_file(out / "records.jsonl"),
                       **({"records_gg.jsonl": H.sha256_file(gg_f)} if has_gg else {}),
                       "script": man["script_sha256"], "weights": man["weights_sha256"], "split": man["split_sha256"]},
           "test15": "NEVER READ"}
    H.json_save(H.PAPER / "ralph" / "results" / "s4__oracle_decomp_v1.json", res)
    print("wrote ralph/results/s4__oracle_decomp_v1.json")
    for g in ("blend_20_50", "gain_all"):
        print(g, {k: (round(v["mean"], 3) if isinstance(v, dict) else v) for k, v in d1[g].items() if isinstance(v, dict) and "mean" in v})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="oracle_decomp_v1")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--gain-gamma", action="store_true", help="extra O-gain+gamma attribution arm (after the main pass)")
    a = ap.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    if a.preflight:
        a.run = f"_preflight_{int(time.time())}"
    if a.aggregate:
        aggregate(a)
    elif a.gain_gamma:
        run_gain_gamma(a)
    else:
        run(a)


if __name__ == "__main__":
    main()
