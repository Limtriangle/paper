"""final_eval_test — the ONLY script that reads the LOLv1 test split (eval15).

Run once per reported configuration, after the plan's final gate opens, on checkpoints that
were selected by validation only. Each invocation is logged in the output JSON with the
checkpoint sha256, so a second read of the test split for the same configuration is visible.

    python3 auto-research/final_eval_test.py --preflight --ckpt <run_dir>/<job>/best.pt --gpu 0
        # validation split only: proves the checkpoint loads and the metric path runs; eval15 untouched
    python3 auto-research/final_eval_test.py --ckpt <run_dir>/<job>/best.pt --label <config> --gpu 0
        # reads eval15 (15 pairs), writes outputs/final_eval/test_v1/<label>/ and appends to
        # ralph/results/final_eval__test.json

Never launched by any study script. Never used for selection.
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

OUT_JSON = H.PAPER / "ralph" / "results" / "final_eval__test.json"
OUT_DIR = H.OUTPUTS / "final_eval"


def load_checkpoint(path, device):
    import torch
    state = torch.load(path, map_location="cpu", weights_only=False)
    cfg = state.get("config", {})
    model = H.build_model(cfg.get("channels"), cfg.get("heads"))
    model.load_state_dict(state["model"])
    return model.to(device).eval(), cfg, state.get("epoch")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--label", help="configuration label for the JSON key (required unless --preflight)")
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--run", default="test_v1")
    ap.add_argument("--preflight", action="store_true", help="validation images only; never reads eval15")
    a = ap.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(a.gpu)
    import torch
    H.import_repo()
    H.set_determinism(3)
    ckpt = Path(a.ckpt).resolve()
    H.require(ckpt.is_file(), f"missing checkpoint {ckpt}")
    model, cfg, epoch = load_checkpoint(ckpt, "cuda")
    H.require(cfg.get("test15") == "NEVER READ", "checkpoint config does not certify test isolation")
    if a.preflight:
        names = H.make_split()["val"][:5]
        folder = H.OUTPUTS / "final_eval" / "_preflight" / f"{int(time.time())}"
        folder.mkdir(parents=True, exist_ok=False)
        H.Job.save(type("J", (), {"dir": folder})(), {"model": model.state_dict(), "epoch": epoch,
                                                       "config": cfg}, "best.pt")
        summary = H.detailed_evaluation(model, names, folder, checkpoints=("best",),
                                        split_label="preflight_validation")
        print("FINAL_EVAL_PREFLIGHT_PASSED (validation images only; eval15 untouched)")
        print(summary[0]["psnr"], summary[0]["ssim"], summary[0]["lpips"])
        return
    H.require(a.label, "--label is required for a test-split evaluation")
    permit = H.allow_test_split(f"final evaluation of {a.label} from {ckpt}")
    names = [n for n in H.list_dir(H.TEST_DIR / "low") if H.is_image(n)]
    H.require(len(names) == 15, f"eval15 has {len(names)} images")
    folder = OUT_DIR / a.run / a.label
    folder.mkdir(parents=True, exist_ok=False)
    H.Job.save(type("J", (), {"dir": folder})(), {"model": model.state_dict(), "epoch": epoch,
                                                   "config": cfg}, "best.pt")
    summary = H.detailed_evaluation(model, names, folder, checkpoints=("best",), n_images=15,
                                    data_dir=H.TEST_DIR, split_label="test")
    row = {k: v for k, v in summary[0].items() if not k.endswith("_n")}
    entry = {"label": a.label, "checkpoint": str(ckpt), "checkpoint_sha256": H.sha256_file(ckpt),
             "checkpoint_epoch": epoch, "config": {k: cfg.get(k) for k in
                 ("variant", "condition", "seed", "channels", "parameters", "split_sha256",
                  "script_sha256", "commit", "selection")},
             "split": "eval15 (15 pairs)", "test_split_read": permit, "evaluated_at": time.time(),
             "metrics": row, "per_image_csv": str(folder / "best_per_image.csv"),
             "sources": {"best_per_image.csv": H.sha256_file(folder / "best_per_image.csv")}}
    data = H.json_load(OUT_JSON) if OUT_JSON.is_file() else {"run_id": "final_eval__test",
                                                             "note": "TEST SPLIT (eval15) read once per label by final_eval_test.py",
                                                             "entries": {}}
    H.require(a.label not in data["entries"], f"{a.label} already evaluated on the test split; refusing a second read")
    data["entries"][a.label] = entry
    data["exported_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    H.json_save(OUT_JSON, data)
    print(f"TEST SPLIT READ for {a.label}: {row}")
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
