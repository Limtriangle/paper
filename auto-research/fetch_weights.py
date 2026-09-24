"""fetch_weights — download the released LOL-v1 w_perc weights, fingerprint them, and check they
load and evaluate on the scene-disjoint VALIDATION split (eval15 untouched).

    python3 auto-research/fetch_weights.py --gpu 0
Writes /home/work/research/weights/LOLv1_wperc/{model.safetensors,config.json} and
ralph/results/phase0_weights.json (source URL, HF revision, sha256, k value, val-split metrics
ungated and gated). The README's 23.81/0.857/0.086 (gated, eval15) cannot be checked here because
eval15 is the test split; the validation images are part of the released model's TRAINING set.
"""
import argparse, json, os, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H

REPO, REV = "fediory/HVI-CIDNet-LOLv1-wperc", "1fa9b6993413a8fe7df1ba433682ccf525349c88"
DEST = H.ROOT / "weights" / "LOLv1_wperc"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--gpu", type=int, default=0); a = ap.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(a.gpu)
    from huggingface_hub import hf_hub_download
    import safetensors.torch as sf
    import torch
    H.import_repo(); H.set_determinism(3)
    DEST.mkdir(parents=True, exist_ok=True)
    files = {}
    for fn in ("model.safetensors", "config.json"):
        p = hf_hub_download(repo_id=REPO, filename=fn, revision=REV, local_dir=str(DEST))
        files[fn] = {"path": str(Path(p).resolve()), "sha256": H.sha256_file(p), "bytes": Path(p).stat().st_size}
    state = sf.load_file(files["model.safetensors"]["path"])
    model = H.build_model()
    missing, unexpected = model.load_state_dict(state, strict=False)
    H.require(not missing and not unexpected, f"state dict mismatch: missing={missing} unexpected={unexpected}")
    model.cuda().eval()
    torch.save({"epoch": None, "model": model.state_dict(), "config": {"test15": "NEVER READ", "arm": "U", "seed": None,
                "source": f"https://huggingface.co/{REPO}/tree/{REV}"}}, DEST / "best.pt")
    split = H.load_split("scene_v1")
    folder = H.OUTPUTS / "weights_check" / "LOLv1_wperc_scene_v1_val"
    folder.mkdir(parents=True, exist_ok=False)
    import shutil; shutil.copy(DEST / "best.pt", folder / "best.pt")
    summary = H.detailed_evaluation(model, split["val"], folder, checkpoints=("best",), eval_gated=True)
    row = {k: v for k, v in summary[0].items() if not k.endswith("_n")}
    out = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": {"repo": f"https://huggingface.co/{REPO}",
           "revision": REV, "readme_name": "LOLv1/w_perc.pth (trained with perceptual loss)", "license": "MIT (upstream)"},
           "files": files, "n_tensors": len(state), "parameters": int(sum(v.numel() for v in state.values())),
           "density_k_released": float(state["trans.density_k"].item()),
           "readme_eval15_numbers_not_checked": {"psnr": 23.8091, "ssim": 0.8574, "lpips": 0.0856, "gated": True,
                                                 "why": "eval15 is the test split; never read before the final gate"},
           "validation_split_check": {"split": "scene_v1 (40 images from our485 = the released model's training data)",
                                      "split_sha256": split["sha256"], "metrics": row,
                                      "note": "ungated = identity knobs; *_gated = upstream eval.py LOLv1 setting (alpha_s 1.3)"},
           "test15": "NEVER READ"}
    H.json_save(H.PAPER / "ralph" / "results" / "phase0_weights.json", out)
    print(json.dumps({k: out[k] for k in ("files", "density_k_released")}, indent=1))
    print({k: round(v, 4) for k, v in row.items() if isinstance(v, float)})


if __name__ == "__main__":
    main()
