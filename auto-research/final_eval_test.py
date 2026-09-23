"""final_eval_test — the ONLY script that evaluates on the LOL-v1 test split (eval15). Frozen
before launch (sha256 in every JSON it writes). Never used for selection.

Modes
  --preflight --ckpt C [--gpu N|-1]           validation images only (5); prints; writes nothing under ralph/
  --ckpt C --label L                          FINAL read-out: one pass over eval15 for the checkpoint C:
                                              per-image metrics (raw + GT-mean with ONE scalar luminance gain),
                                              GT-intensity deciles, darkness stress test (x1, x0.5, x0.25 +
                                              Poisson-Gaussian noise). Appends entry L to
                                              ralph/results/final_eval__test.json; refuses a second read of L.
  --oracle --job J --label L                  ORACLE (R2 §4b): scores every snapshots/epoch_*.pt (+ last.pt)
                                              of job dir J on eval15 (raw/GT-mean PSNR, SSIM, LPIPS) in ONE
                                              dedicated pass after all arms finish; appends to
                                              ralph/results/final_eval__oracle.json, labelled oracle: never
                                              used to select or rank anything.
  --oracle --preflight --job J                the same on validation images; writes nothing under ralph/

Label convention: <arm>_seed<s> for the final (last.pt) checkpoint, <arm>_seed<s>_valbest for best.pt.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

OUT_TEST = H.PAPER / "ralph" / "results" / "final_eval__test.json"
OUT_ORACLE = H.PAPER / "ralph" / "results" / "final_eval__oracle.json"
OUT_DIR = H.OUTPUTS / "final_eval"
SCRIPT = Path(__file__).resolve()


def load_checkpoint(path, device):
    import torch
    import c1_arms as C
    state = torch.load(path, map_location="cpu", weights_only=False)
    cfg = state.get("config", {})
    H.require(cfg.get("test15") == "NEVER READ", "checkpoint config does not certify test isolation")
    arm = cfg.get("arm", "U")
    model = C.build_arm(arm, cfg.get("seed", 0), cfg.get("channels"), cfg.get("heads"))
    model.load_state_dict(state["model"]) if "net.trans.density_k" in state["model"] else model.net.load_state_dict(state["model"])
    return model.to(device).eval(), cfg, state.get("epoch")


def measure(model, names, data_dir, device, lp, full=True):
    """Per-image rows (+ deciles and stress if full)."""
    import torch
    import c1_metrics as M
    rows = []
    for name in names:
        x, gt, _ = H.load_val_pair(name, data_dir)
        x, gt = x.to(device), gt.to(device)
        pred = H.infer(model, x.unsqueeze(0), gated=False)[0]
        row = {"image": name, **M.image_metrics(pred, gt, lp)}
        if full:
            row["deciles"] = M.decile_table(pred, gt)
            row["stress"] = {}
            for f in M.STRESS_FACTORS:
                xs = M.poisson_gaussian(x, f, M.stress_seed(name, f))
                ps = H.infer(model, xs.unsqueeze(0), gated=False)[0]
                dec = M.decile_table(ps, gt)
                b3 = [d for d in dec[:3] if d["n"]]
                row["stress"][str(f)] = {**{k: v for k, v in M.image_metrics(ps, gt).items()
                                            if k in ("psnr_gtmean", "delta_e00", "delta_e00_gtmean")},
                                         "hue_err_all": sum(d["hue_err"] * d["n"] for d in dec if d["n"]) / sum(d["n"] for d in dec if d["n"]),
                                         "hue_err_bottom3": (sum(d["hue_err"] * d["n"] for d in b3) / sum(d["n"] for d in b3)) if b3 else None}
        rows.append(row)
    return rows


def means(rows, keys):
    return {k: sum(r[k] for r in rows) / len(rows) for k in keys if all(k in r for r in rows)}


SUMMARY_KEYS = ("psnr", "psnr_gtmean", "ssim", "ssim_gtmean", "lpips", "lpips_gtmean", "delta_e00",
                "delta_e00_gtmean", "log_exposure", "mse_raw", "mse_gtmean", "gain_error")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ckpt")
    ap.add_argument("--job", help="job dir with snapshots/ (oracle mode)")
    ap.add_argument("--label")
    ap.add_argument("--gpu", type=int, default=0, help="-1 = CPU")
    ap.add_argument("--run", default="test_v1")
    ap.add_argument("--preflight", action="store_true", help="validation images only; never reads eval15")
    ap.add_argument("--oracle", action="store_true")
    a = ap.parse_args()
    if a.gpu >= 0:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(a.gpu)
    import torch
    device = "cuda" if a.gpu >= 0 and torch.cuda.is_available() else "cpu"
    H.import_repo()
    H.set_determinism(3)
    import c1_metrics as M
    lp = H.LPIPSMetric(device)
    script_sha = H.sha256_file(SCRIPT)
    metrics_sha = H.sha256_file(HERE / "c1_metrics.py")
    if a.preflight:
        names, data_dir, permit = H.load_split("scene_v1")["val"][:5], H.TRAIN_DIR, None
        split_label = "validation (preflight; eval15 untouched)"
    else:
        H.require(a.label, "--label is required for a test-split pass")
        permit = H.allow_test_split(f"{'oracle' if a.oracle else 'final'} evaluation of {a.label}")
        names = [n for n in H.list_dir(H.TEST_DIR / "low") if H.is_image(n)]
        H.require(len(names) == 15, f"eval15 has {len(names)} images")
        data_dir, split_label = H.TEST_DIR, "eval15 (15 pairs)"
    if a.oracle:
        job = Path(a.job).resolve()
        ckpts = sorted((job / "snapshots").glob("epoch_*.pt")) + ([job / "last.pt"] if (job / "last.pt").is_file() else [])
        H.require(ckpts, f"no snapshots under {job}")
        curve = []
        for ck in ckpts:
            model, cfg, epoch = load_checkpoint(ck, device)
            rows = measure(model, names, data_dir, device, lp, full=False)
            curve.append({"checkpoint": ck.name, "epoch": epoch, "sha256": H.sha256_file(ck),
                          **means(rows, ("psnr", "psnr_gtmean", "ssim", "lpips"))})
            print(ck.name, epoch, round(curve[-1]["psnr"], 4), round(curve[-1]["psnr_gtmean"], 4), flush=True)
        entry = {"kind": "oracle", "label": a.label, "job": str(job), "split": split_label,
                 "config": {k: cfg.get(k) for k in ("arm", "seed", "split_sha256", "script_sha256", "commit")},
                 "test_split_access": permit, "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "curve": curve, "n_checkpoints": len(curve),
                 "max_psnr_gtmean": max(c["psnr_gtmean"] for c in curve),
                 "warning": "ORACLE: test-split scores of every saved checkpoint; NEVER used for selection or ranking"}
        if a.preflight:
            print("ORACLE_PREFLIGHT_PASSED (validation images only)", entry["n_checkpoints"], "checkpoints")
            return
        data = H.json_load(OUT_ORACLE) if OUT_ORACLE.is_file() else {"run_id": "final_eval__oracle", "kind": "oracle", "entries": {}}
        H.require(a.label not in data["entries"], f"{a.label}: oracle already computed; refusing a second read")
        data["entries"][a.label] = entry
        data.update(exported_at=time.strftime("%Y-%m-%dT%H:%M:%S"), script_sha256=script_sha, metrics_sha256=metrics_sha)
        H.json_save(OUT_ORACLE, data)
        print(f"wrote {OUT_ORACLE}")
        return
    ckpt = Path(a.ckpt).resolve()
    model, cfg, epoch = load_checkpoint(ckpt, device)
    rows = measure(model, names, data_dir, device, lp, full=True)
    summary = means(rows, SUMMARY_KEYS)
    if a.preflight:
        print("FINAL_EVAL_PREFLIGHT_PASSED (validation images only; eval15 untouched)")
        print({k: round(v, 4) for k, v in summary.items()})
        print("stress keys", sorted(rows[0]["stress"]), "deciles", len(rows[0]["deciles"]))
        return
    folder = OUT_DIR / a.run / a.label
    folder.mkdir(parents=True, exist_ok=False)
    entry = {"kind": "final", "label": a.label, "checkpoint": str(ckpt), "checkpoint_sha256": H.sha256_file(ckpt),
             "checkpoint_epoch": epoch, "config": {k: cfg.get(k) for k in
                 ("arm", "representation", "loss", "k0", "seed", "channels", "parameters", "split", "split_sha256",
                  "script_sha256", "commit", "selection")},
             "split": split_label, "test_split_access": permit, "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "gt_mean": "ONE scalar luminance gain mean(Y_gt)/mean(Y_pred), BT.601, all channels; never per-channel",
             "stress_noise": {"photons_full_scale": M.PHOTONS, "read_sigma": M.READ_SIGMA, "factors": M.STRESS_FACTORS},
             "metrics": summary, "per_image": rows}
    data = H.json_load(OUT_TEST) if OUT_TEST.is_file() else {"run_id": "final_eval__test",
                                                               "note": "TEST SPLIT (eval15) read once per label by final_eval_test.py", "entries": {}}
    H.require(a.label not in data["entries"], f"{a.label} already evaluated on the test split; refusing a second read")
    data["entries"][a.label] = entry
    data.update(exported_at=time.strftime("%Y-%m-%dT%H:%M:%S"), script_sha256=script_sha, metrics_sha256=metrics_sha)
    H.json_save(OUT_TEST, data)
    H.json_save(folder / "entry.json", entry)
    print(f"TEST SPLIT READ for {a.label}: {summary}")
    print(f"wrote {OUT_TEST}")


if __name__ == "__main__":
    main()
