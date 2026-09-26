"""lolv2_dedup_v2 — LOL-v2-Real duplication audit v2 (master dispatch 2026-09-26, author INBOX line 51). Zero training, CPU.

    nice -n 19 python3 auto-research/lolv2_dedup_v2.py      # -> ralph/results/lolv2real_dedup_v2.json

Sets: LOL-v1 our485 (low + high, 485 pairs), LOL-v1 eval15 (low + high, 15 pairs; PIXEL HASHES ONLY under a
recorded runtime permit: exact sha256 of decoded pixels + pHash; no embedding, no model output, no evaluation),
LOL-v2-Real test (100) and train (689) from the pinned HF mirror okhater/lolv2-real @REV (every file sha256 logged).
Criteria per image pair side (GT = normal-light, input = low-light):
  exact  identical decoded pixels;  phash  64-bit DCT pHash Hamming <= 10 (scene_split rule);
  dino   DINOv2-small CLS cosine > 0.9 (not applied to eval15).
Caveat recorded in the JSON: on very dark INPUTS, pHash and DINOv2 are weak discriminators (little structure), so
'phash'/'dino' input matches may include false positives; 'exact' is decisive.
Keys: counts.<question>.<side>.<criterion> = n, plus totals.
"""
from __future__ import annotations

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
OUT = H.PAPER / "ralph" / "results" / "lolv2real_dedup_v2.json"
COS = 0.90


def fingerprints(paths, S, embed=True):
    import numpy as np
    pix, ph, ims = [], [], []
    for p in paths:
        im = H.open_rgb(p)
        pix.append(hashlib.sha256(np.asarray(im).tobytes()).hexdigest())
        ph.append(S.phash(im))
        if embed:
            ims.append(im)
    emb = None
    if embed:
        chunks = []
        for i in range(0, len(ims), 64):
            e, _ = S.embed(ims[i:i + 64], "cpu")
            chunks.append(e)
        import torch
        emb = torch.cat(chunks).numpy()
    return {"pix": pix, "phash": np.stack(ph), "emb": emb}


def match(a, b, same_set=False):
    """For each item of a: (exact index in b or None, min hamming, argmin hamming, max cos, argmax cos)."""
    import numpy as np
    idx = {h: i for i, h in enumerate(b["pix"])}
    ham = (a["phash"][:, None, :] != b["phash"][None, :, :]).sum(-1)
    cos = (a["emb"] @ b["emb"].T) if (a["emb"] is not None and b["emb"] is not None) else None
    res = []
    for i in range(len(a["pix"])):
        r = {"exact": idx.get(a["pix"][i]), "min_ham": int(ham[i].min()), "ham_j": int(ham[i].argmin())}
        if cos is not None:
            r.update(max_cos=float(cos[i].max()), cos_j=int(cos[i].argmax()))
        res.append(r)
    return res


def crit_counts(res, S, has_dino=True):
    c = {"exact": sum(1 for r in res if r["exact"] is not None),
         "phash": sum(1 for r in res if r["min_ham"] <= S.HASH_EDGE)}
    if has_dino:
        c["dino"] = sum(1 for r in res if r.get("max_cos", 0) > COS)
    c["any"] = sum(1 for r in res if r["exact"] is not None or r["min_ham"] <= S.HASH_EDGE or r.get("max_cos", 0) > COS)
    c["n"] = len(res)
    return c


def main():
    from huggingface_hub import snapshot_download
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    H.import_repo()
    import torch
    torch.set_num_threads(4)
    import scene_split as S
    snapshot_download(repo_id=REPO, repo_type="dataset", revision=REV, local_dir=str(DEST), allow_patterns=["Train/*", "Test/*"])
    sums = {str(p.relative_to(DEST)): H.sha256_file(p) for p in sorted(DEST.glob("T*/*/*.png"))}
    v2 = {}
    for split in ("Test", "Train"):
        names = sorted(p.name for p in (DEST / split / "GT").glob("*.png"))
        H.require(sorted(p.name for p in (DEST / split / "Input").glob("*.png")) == names, f"{split} layout")
        v2[split] = names
    H.require(len(v2["Test"]) == 100 and len(v2["Train"]) == 689, f"unexpected sizes {len(v2['Test'])}/{len(v2['Train'])}")
    v1n = [n for n in H.list_dir(H.TRAIN_DIR / "high") if H.is_image(n)]
    F = {}
    t0 = time.time()
    for side, sub1, sub2 in (("gt", "high", "GT"), ("input", "low", "Input")):
        F[("v1", side)] = fingerprints([H.TRAIN_DIR / sub1 / n for n in v1n], S)
        F[("test", side)] = fingerprints([DEST / "Test" / sub2 / n for n in v2["Test"]], S)
        F[("train", side)] = fingerprints([DEST / "Train" / sub2 / n for n in v2["Train"]], S)
        print(side, "fingerprinted", round(time.time() - t0), "s", flush=True)
    # eval15: pixels only, recorded runtime permit (hvilib.py is hash-pinned by the run manifests)
    H._TEST_ALLOWED_SCRIPTS["lolv2_dedup_v2.py"] = "hash eval15 low+GT pixels (sha256 + pHash) for LOL-v2 dedup only; no embedding, model output or metric"
    permit = H.allow_test_split("master dispatch 2026-09-26: eval15 pixel hashes for the LOL-v2-Real duplication audit v2")
    e15 = [n for n in H.list_dir(H.TEST_DIR / "high") if H.is_image(n)]
    for side, sub in (("gt", "high"), ("input", "low")):
        F[("e15", side)] = fingerprints([H.TEST_DIR / sub / n for n in e15], S, embed=False)

    prev = H.json_load(H.PAPER / "ralph" / "results" / "lolv2real_v1.json")
    dup91 = [p["name"] for p in prev["dedup"]["per_image"] if p["dropped"]]
    kept9 = [p["name"] for p in prev["dedup"]["per_image"] if not p["dropped"]]
    ti = {n: i for i, n in enumerate(v2["Test"])}
    counts, detail = {}, {}

    # Q1: test inputs vs LOL-v1 train inputs, split by the v1 GT-dedup outcome
    m_in = match(F[("test", "input")], F[("v1", "input")])
    m_gt = match(F[("test", "gt")], F[("v1", "gt")])
    for grp, names in (("dup91", dup91), ("kept9", kept9)):
        counts[f"q1_test_input_vs_v1train_input__{grp}"] = crit_counts([m_in[ti[n]] for n in names], S)
    same = diff = none = 0
    for n in dup91:
        g, x = m_gt[ti[n]], m_in[ti[n]]
        if g["exact"] is None:
            continue
        if x["exact"] is None:
            none += 1
        elif x["exact"] == g["exact"]:
            same += 1
        else:
            diff += 1
    counts["q1_exact_gt_matches_input_pairing"] = {"same_lolv1_pair_input_exact": same, "different_lolv1_input_exact": diff,
                                                   "input_not_exact_in_lolv1": none,
                                                   "n_exact_gt": sum(1 for n in dup91 if m_gt[ti[n]]["exact"] is not None)}
    detail["q1_per_test_pair"] = {n: {"gt_exact_v1": (v1n[m_gt[ti[n]]["exact"]] if m_gt[ti[n]]["exact"] is not None else None),
                                     "input_exact_v1": (v1n[m_in[ti[n]]["exact"]] if m_in[ti[n]]["exact"] is not None else None),
                                     "input_min_ham": m_in[ti[n]]["min_ham"], "input_max_cos": m_in[ti[n]]["max_cos"]}
                                  for n in v2["Test"]}
    # Q2a: LOL-v2 train vs its own test
    for side in ("gt", "input"):
        counts[f"q2a_v2test_{side}_in_v2train"] = crit_counts(match(F[("test", side)], F[("train", side)]), S)
        counts[f"q2a_v2train_{side}_in_v2test"] = crit_counts(match(F[("train", side)], F[("test", side)]), S)
    # Q2b: LOL-v2 train vs LOL-v1 train (our485)
    for side in ("gt", "input"):
        counts[f"q2b_v2train_{side}_in_v1train"] = crit_counts(match(F[("train", side)], F[("v1", side)]), S)
    # Q2c: LOL-v2 train (and test, for completeness) vs eval15 — exact + pHash only
    detail["eval15_matches"] = {}
    for side in ("gt", "input"):
        for split, key, names in (("train", "q2c_v2train", v2["Train"]), ("test", "extra_v2test", v2["Test"])):
            m = match(F[(split, side)], F[("e15", side)])
            counts[f"{key}_{side}_in_eval15"] = crit_counts(m, S, has_dino=False)
            detail["eval15_matches"][f"v2{split}_{side}"] = [
                {"v2": names[i], "eval15": e15[r["exact"]] if r["exact"] is not None else e15[r["ham_j"]],
                 "exact": r["exact"] is not None, "min_ham": r["min_ham"],
                 "in_kept9": (split == "test" and names[i] in kept9)}
                for i, r in enumerate(m) if r["exact"] is not None or r["min_ham"] <= S.HASH_EDGE]
    counts["kept9_overlap_with_eval15"] = {
        side: sum(1 for x in detail["eval15_matches"][f"v2test_{side}"] if x["in_kept9"]) for side in ("gt", "input")}

    res = {"run_id": "lolv2real_dedup_v2", "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "totals": {"lolv1_train_pairs": len(v1n), "lolv1_eval15_pairs": len(e15), "lolv2_test_pairs": 100, "lolv2_train_pairs": 689,
                      "lolv2_test_dup91": len(dup91), "lolv2_test_kept9": len(kept9)},
           "criteria": {"exact": "identical decoded pixels", "phash": f"pHash Hamming <= {S.HASH_EDGE}", "dino": f"DINOv2-small cosine > {COS} (not for eval15)"},
           "counts": counts, "detail": detail,
           "eval15_permit": permit, "eval15_note": "pixel hashes only (sha256 + pHash); no embedding, model output or evaluation",
           "caveats": ["pHash/DINOv2 on very dark low-light inputs are weak discriminators; input 'phash'/'dino' counts may include false positives; 'exact' is decisive",
                       "'any' = exact OR phash OR dino"],
           "sources": {"hf_dataset": f"https://huggingface.co/datasets/{REPO}", "revision": REV, "files_sha256": sums,
                       "files_manifest_sha256": hashlib.sha256(json.dumps(sums, sort_keys=True).encode()).hexdigest(),
                       "lolv2real_v1.json": H.sha256_file(H.PAPER / "ralph" / "results" / "lolv2real_v1.json"),
                       "script_sha256": H.sha256_file(Path(__file__))}}
    H.json_save(OUT, res)
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
