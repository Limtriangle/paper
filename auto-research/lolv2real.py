"""lolv2real — pre-registered cross-dataset check (HVI-PLAN §3): LOL-v2-Real test, deduplicated against LOL-v1 train.

    python3 auto-research/lolv2real.py --prepare                 # download (pinned), sha256 every file, dedup -> ralph/results/lolv2real_v1.json
    python3 auto-research/lolv2real.py --eval --ckpt C --label lolv2_<arm>_seed<s> [--gpu N|-1]
                                                                # one read per label on the kept test pairs, same metrics as final_eval_test.py

Source: Hugging Face dataset mirror okhater/lolv2-real (unofficial mirror of LOL-v2 Real_captured, Yang et al. TIP 2021;
the official releases are Baidu/OneDrive/Google-Drive links), pinned to revision REV; every file's sha256 is logged.
Dedup: a LOL-v2-Real test pair is DROPPED if its GT matches any LOL-v1 our485 GT (all 485, a superset of our train split)
by (a) identical decoded pixels, (b) pHash Hamming <= 10 (scene_split rule), or (c) DINOv2-small cosine > 0.9.
Never touches LOL-v1 eval15. No selection on these reads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

REPO, REV = "okhater/lolv2-real", "db2979107f7c22d372c6e4f1b06fd6203069af0a"
DEST = H.ROOT / "datasets" / "LOLv2_Real_hf"
OUT = H.PAPER / "ralph" / "results" / "lolv2real_v1.json"
COS_DUP = 0.90


def prepare(a):
    import numpy as np
    from huggingface_hub import snapshot_download
    import scene_split as S
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    H.import_repo()
    snapshot_download(repo_id=REPO, repo_type="dataset", revision=REV, local_dir=str(DEST), allow_patterns=["Test/*", "README.md", "LICENSE"])
    files = sorted(p for p in (DEST / "Test").rglob("*.png"))
    sums = {str(p.relative_to(DEST)): H.sha256_file(p) for p in files}
    names = sorted(p.name for p in (DEST / "Test" / "GT").glob("*.png"))
    H.require(len(names) == 100 and sorted(p.name for p in (DEST / "Test" / "Input").glob("*.png")) == names, "unexpected test layout")
    v2 = [H.open_rgb(DEST / "Test" / "GT" / n) for n in names]
    v1n = [n for n in H.list_dir(H.TRAIN_DIR / "high") if H.is_image(n)]
    v1 = [H.open_rgb(H.TRAIN_DIR / "high" / n) for n in v1n]
    pix = {hashlib.sha256(np.asarray(im).tobytes()).hexdigest(): n for im, n in zip(v1, v1n)}
    h2, h1 = np.stack([S.phash(im) for im in v2]), np.stack([S.phash(im) for im in v1])
    e2, model_name = S.embed(v2, "cpu")
    e1, _ = S.embed(v1, "cpu")
    cos = (e2 @ e1.T).numpy()
    ham = (h2[:, None, :] != h1[None, :, :]).sum(-1)
    per, keep = [], []
    for i, n in enumerate(names):
        j = int(cos[i].argmax())
        exact = pix.get(hashlib.sha256(np.asarray(v2[i]).tobytes()).hexdigest())
        drop = bool(exact) or int(ham[i].min()) <= S.HASH_EDGE or float(cos[i, j]) > COS_DUP
        per.append({"name": n, "nearest_lolv1": v1n[j], "cos": float(cos[i, j]), "min_hamming": int(ham[i].min()),
                    "exact_pixel_match": exact, "dropped": drop})
        if not drop:
            keep.append(n)
    res = {"run_id": "lolv2real_v1", "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "source": {"hf_dataset": f"https://huggingface.co/datasets/{REPO}", "revision": REV,
                      "note": "unofficial mirror of LOL-v2 Real_captured (Yang et al., TIP 2021); official links are Baidu/OneDrive/Google Drive",
                      "local_dir": str(DEST), "n_test_pairs": len(names), "files_sha256": sums,
                      "files_manifest_sha256": hashlib.sha256(json.dumps(sums, sort_keys=True).encode()).hexdigest()},
           "dedup": {"against": "LOL-v1 our485 GT (all 485 pairs; superset of the training split)", "embedding": model_name,
                     "rules": {"exact_pixels": True, "phash_hamming_le": S.HASH_EDGE, "dinov2_cos_gt": COS_DUP},
                     "n_dropped": len(names) - len(keep), "n_kept": len(keep), "kept": keep, "per_image": per,
                     "n_dropped_by": {"exact": sum(1 for p in per if p["exact_pixel_match"]),
                                      "phash": sum(1 for p in per if p["min_hamming"] <= S.HASH_EDGE),
                                      "cos": sum(1 for p in per if p["cos"] > COS_DUP)}},
           "entries": {}, "script_sha256": H.sha256_file(Path(__file__))}
    H.json_save(OUT, res)
    print("kept", len(keep), "dropped", len(names) - len(keep), res["dedup"]["n_dropped_by"])


def evaluate(a):
    if a.gpu >= 0:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(a.gpu)
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    import torch
    import final_eval_test as F
    device = "cuda" if a.gpu >= 0 and torch.cuda.is_available() else "cpu"
    H.import_repo()
    H.set_determinism(a.threads)
    d = H.json_load(OUT)
    H.require(a.label not in d["entries"], f"{a.label} already evaluated on LOL-v2-Real; refusing a second read")
    ck = Path(a.ckpt).resolve()
    model, cfg, epoch = F.load_checkpoint(ck, device)
    lp = H.LPIPSMetric(device)
    rows = F.measure(model, d["dedup"]["kept"], DEST / "Test_as_lol", device, lp, full=True)
    entry = {"label": a.label, "checkpoint": str(ck), "checkpoint_sha256": H.sha256_file(ck), "checkpoint_epoch": epoch,
             "config": {k: cfg.get(k) for k in ("arm", "seed", "split_sha256", "script_sha256")},
             "n_images": len(rows), "device": device, "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "metrics": F.means(rows, F.SUMMARY_KEYS), "per_image": rows,
             "eval_sha256": {"lolv2real.py": H.sha256_file(Path(__file__)), "final_eval_test.py": H.sha256_file(HERE / "final_eval_test.py")}}
    d = H.json_load(OUT)                       # re-read: another label may have been written meanwhile
    H.require(a.label not in d["entries"], f"{a.label} already evaluated")
    d["entries"][a.label] = entry
    H.json_save(OUT, d)
    print(a.label, {k: round(v, 3) for k, v in entry["metrics"].items() if k in ("psnr", "psnr_gtmean", "ssim", "lpips")})


def link_layout():
    """load_val_pair expects <dir>/low/<n> and <dir>/high/<n>: expose Test/Input and Test/GT under that layout."""
    t = DEST / "Test_as_lol"
    t.mkdir(exist_ok=True)
    for sub, src in (("low", "Input"), ("high", "GT")):
        p = t / sub
        if not p.exists():
            p.symlink_to(DEST / "Test" / src)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--ckpt")
    ap.add_argument("--label")
    ap.add_argument("--gpu", type=int, default=-1)
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    if a.prepare:
        prepare(a)
        link_layout()
    elif a.eval:
        H.require(a.ckpt and a.label and a.label.startswith("lolv2_"), "--eval needs --ckpt and --label lolv2_<arm>_seed<s>")
        link_layout()
        evaluate(a)


if __name__ == "__main__":
    main()
