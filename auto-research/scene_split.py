"""scene_split — scene-disjoint LOL-v1 validation split (R2_design_redteam.md §4a).

    python3 auto-research/scene_split.py --gpu 0

Clusters all 500 LOL-v1 GT images (our485/high + eval15/high) by scene with DINOv2-small CLS
embeddings (cosine) plus a 64-bit pHash (Hamming), connected components over edges
cos >= COS_EDGE or hamming <= HASH_EDGE. Validation = whole clusters that contain NO eval15
image, chosen deterministically (seed 42) until >= N_VAL_MIN images. Everything else in
our485 is training, so train/val share no scene cluster.

eval15 access: this script lists and embeds eval15 GT images for clustering ONLY (hvilib
permit, scope recorded in the output JSON). It evaluates nothing.
Writes auto-research/split_scene_v1.json (+sha256) and ralph/results/phase0_val_split_scene.json.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

MODEL = "facebook/dinov2-small"
COS_EDGE, HASH_EDGE, DUP_COS = 0.85, 10, 0.90
N_VAL_MIN, N_VAL_MAX, SEED = 40, 48, 42


def phash(img, size=32, keep=8):
    import numpy as np
    from scipy.fft import dct
    g = np.asarray(img.convert("L").resize((size, size)), dtype=np.float64)
    d = dct(dct(g, axis=0, norm="ortho"), axis=1, norm="ortho")[:keep, :keep]
    return (d > np.median(d)).flatten()


def embed(images, device):
    import torch
    from transformers import AutoImageProcessor, AutoModel
    proc = AutoImageProcessor.from_pretrained(MODEL)
    model = AutoModel.from_pretrained(MODEL).to(device).eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(images), 32):
            x = proc(images=images[i:i + 32], return_tensors="pt").to(device)
            out.append(torch.nn.functional.normalize(model(**x).pooler_output.float(), dim=-1).cpu())
    return torch.cat(out), model.config._name_or_path


def main():
    import numpy as np
    import torch
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    a = ap.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(a.gpu)
    H.import_repo()
    permit = H.allow_test_split("scene clustering of GT images; no evaluation")
    train_names = [n for n in H.list_dir(H.TRAIN_DIR / "high") if H.is_image(n)]
    test_names = [n for n in H.list_dir(H.TEST_DIR / "high") if H.is_image(n)]
    H.require(len(train_names) == 485 and len(test_names) == 15, "unexpected LOL-v1 layout")
    items = [("train", n, H.TRAIN_DIR / "high" / n) for n in train_names] + \
            [("test", n, H.TEST_DIR / "high" / n) for n in test_names]
    images = [H.open_rgb(p) for _, _, p in items]
    hashes = np.stack([phash(im) for im in images])
    device = "cuda" if torch.cuda.is_available() else "cpu"
    emb, model_name = embed(images, device)
    cos = (emb @ emb.T).numpy()
    ham = (hashes[:, None, :] != hashes[None, :, :]).sum(-1)
    n = len(items)
    adj = ((cos >= COS_EDGE) | (ham <= HASH_EDGE)) & ~np.eye(n, dtype=bool)
    ii, jj = np.nonzero(adj)
    n_clusters, label = connected_components(coo_matrix((np.ones(len(ii)), (ii, jj)), shape=(n, n)), directed=False)
    is_test = np.array([s == "test" for s, _, _ in items])
    test_clusters = set(label[is_test].tolist())
    # eval15 near-duplicates in the train set
    tr_idx, te_idx = np.nonzero(~is_test)[0], np.nonzero(is_test)[0]
    dup = []
    for t in te_idx:
        j = tr_idx[np.argmax(cos[t, tr_idx])]
        dup.append({"test": items[t][1], "nearest_train": items[j][1], "cos": float(cos[t, j]),
                    "hamming": int(ham[t, j]), "same_cluster": bool(label[t] == label[j])})
    # validation: whole clusters without any eval15 member, deterministic order
    members = {}
    for k, (s, name, _) in enumerate(items):
        members.setdefault(int(label[k]), []).append(name)
    eligible = sorted(c for c in members if c not in test_clusters)
    random.Random(SEED).shuffle(eligible)
    val, val_clusters = [], []
    for c in eligible:
        if len(val) >= N_VAL_MIN:
            break
        if len(val) + len(members[c]) > N_VAL_MAX:
            continue
        val += members[c]
        val_clusters.append(c)
    val = sorted(val)
    train = sorted(set(train_names) - set(val))
    H.require(not set(val) & set(train) and len(val) + len(train) == 485, "split inconsistency")
    sizes = sorted((len(v) for v in members.values()), reverse=True)
    split = {"name": "scene_v1", "split_seed": SEED, "train_val_source": "our485", "test_source": "eval15",
             "test": "NEVER READ", "rule": f"whole scene clusters (DINOv2 cos>={COS_EDGE} or pHash hamming<={HASH_EDGE}, "
             f"connected components) containing no eval15 image, seeded order, until >= {N_VAL_MIN} images",
             "embedding_model": model_name, "n_train": len(train), "n_val": len(val),
             "val_clusters": val_clusters, "train": train, "val": val}
    split["sha256"] = H.split_sha(split)
    H.json_save(HERE / "split_scene_v1.json", split)
    summary = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "test_split_access": permit,
               "embedding_model": model_name, "edges": {"cos": COS_EDGE, "hamming": HASH_EDGE},
               "n_images": n, "n_clusters": int(n_clusters), "cluster_sizes_top10": sizes[:10],
               "n_singletons": sum(1 for s in sizes if s == 1),
               "clusters_with_eval15": len(test_clusters),
               "train_images_sharing_a_cluster_with_eval15": int(sum(len(members[c]) for c in test_clusters) - 15),
               "eval15_with_train_near_duplicate": {
                   f"cos>{th}": sum(1 for d in dup if d["cos"] > th) for th in (0.80, 0.85, 0.90, 0.95)},
               "eval15_nearest_train": dup,
               "val": {"n": len(val), "n_clusters": len(val_clusters), "names": val},
               "n_train": len(train), "split_file": "auto-research/split_scene_v1.json",
               "split_sha256": split["sha256"],
               "cos_stats_train_train": {"p50": float(np.median(cos[np.ix_(tr_idx, tr_idx)])),
                                         "p99": float(np.percentile(cos[np.ix_(tr_idx, tr_idx)], 99))}}
    H.json_save(H.PAPER / "ralph" / "results" / "phase0_val_split_scene.json", summary)
    print({k: v for k, v in summary.items() if k not in ("eval15_nearest_train", "val")})
    print("val", val)
    print(f"eval15 with train near-duplicate cos>{DUP_COS}:", summary["eval15_with_train_near_duplicate"][f"cos>{DUP_COS}"])


if __name__ == "__main__":
    main()
