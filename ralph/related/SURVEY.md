# SURVEY.md — top-tier prior work around HVI-CIDNet (Phase 0 literature pass, 2026-09-24)

Owner: author's assistant (coordinated by Fable 5.1; searches run by six scout agents on
Opus 5.5 / Sonnet 5). Complements writing's `ralph/phase0_related.md` (code + paper facts)
and master's `ralph/phase0_candidates.md`. This file is the narrative; `INDEX.md` is the
generated per-entry table; `survey.bib` holds every BibTeX block; `A_*.md` … `F_*.md` are
the raw slice files with full entries.

Venue filter: Tier 1 = CVPR / ICCV / ECCV / NeurIPS / ICLR / ICML / TPAMI / IJCV.
Tier 2 = AAAI / ACM MM / TIP / TCSVT / WACV / BMVC / TMM (+ TCI, TNNLS, MLSys, ACL where a
methodology reference needed it). Preprints only in slices A and D (HVI follow-ups are
young). Every entry's venue and year was cross-checked against a second source (CVF open
access, DOI page, OpenReview, proceedings site, or dblp); the two exceptions are marked
`VERIFIED: no` in E and are arXiv-only.

| Slice | File | Entries | Verified |
|---|---|---|---|
| A — color-space-based LLIE | `A_colorspace.md` | 15 | 15 |
| B — canonical deep LLIE 2018–2022 (+ dataset provenance) | `B_llie_2018_2022.md` | 20 | 20 |
| C — deep LLIE 2023–2026, non-HVI | `C_llie_2023_2026.md` | 20 | 20 |
| D — works that cite / extend / criticise HVI-CIDNet | `D_hvi_followups.md` | 22 | 22 |
| E — evaluation methodology, reproducibility, metrics, statistics | `E_evaluation.md` | 24 | 22 |
| F — loss functions and two-branch / cross-attention architectures | `F_losses_architectures.md` | 21 | 21 |

Overlaps between slices (same paper, sometimes different bibkey) are listed at the end;
`survey.bib` keeps one entry per paper.

---

## 1. What the literature does NOT contain (the gaps, each traceable to a slice)

1. **No matched-network, multi-seed comparison of HVI against sRGB / HSV / YCbCr.** Every
   color-space ablation found is a single run: HVI-CIDNet+ Table V (sRGB 27.26 / HSV 25.86 /
   HVI 28.85 dB on LOL-v1, GT-mean), VCR (HVI vs HSV only), TPCNet (HVI / LAB / YCbCr on
   LOLv2-Real, single run, YCbCr ahead at 24.98 vs 24.64), RHVI-FDD (HSV / HVI / RHVI), LHSI
   (white-balance task), BC-IHV (intensity law only, no sRGB/HSV/YCbCr arm). [A, D]
2. **No isolated sweep of the density term k.** HVI-CIDNet+ switches C_k on/off; FusionNet's
   "k" sweep is over fusion weights; BC-IHV and RHVI-FDD change the intensity channel and
   leave k fixed. [D]
3. **No top-venue LLIE paper reports mean ± SD over training seeds** — none of the 40 papers
   in B and C, none of the 22 in D, and none of the NTIRE 2024–2026 reports. The only
   three-seed restoration example found is a 2026 deblurring preprint, with seed SD of
   0.2–0.4 dB PSNR, the size of many claimed LLIE gains. [C, D, E]
4. **The ~4–5 dB spread in "HVI-CIDNet LOL-v1 PSNR" has never been decomposed.** 28.20
   (paper, GT-mean) vs 23.5–24.0 (FusionNet, PAL, GitHub issue #66, apparently no GT-mean),
   plus test-split checkpoint selection (issue #163) and unmeasured seed variance. [D, E]
5. **The GT-mean convention has no citable origin.** READMEs attribute it to LLFlow / KinD;
   neither names a source. Retinexformer's authors advise against it as ground-truth leakage;
   Liao et al. (ICCV 2025) show the brightness mismatch it hides is systematic. NTIRE
   2024–2026 do not mention it. [E]
6. **Duplicating one composite loss across RGB and a second color space has no Tier-1
   precedent.** The closest is U-Shape Transformer (TIP 2023, RGB + Lab/LCH for underwater
   enhancement); Bread and LYT-Net supervise per-branch instead. [F]
7. **Two robustness claims against HVI are untested under a controlled comparison:** that a
   learned k generalises worse (FusionNet, Multinex), and that CIDNet is brittle to input
   brightness shifts (MILL: LOL-v1 PSNR 26.4 → 17.7 at 20 % blend toward GT; NTIRE 2026
   zero-shot 13.85 dB, below gamma correction). [D]

Mapping to `phase0_candidates.md`: gaps 1, 3, 4 → **C1 + C2** (master's recommendation);
gap 2 and 7 → **C3**; gap 6 → **C4**; gap 7 → **C5**.

## 2. How the thesis should position itself (what to cite where)

- **Paradigm and lineage (intro moves 1–3):** RetinexNet → KinD/KinD++ → DRBN, Zero-DCE,
  EnlightenGAN, MIRNet → RUAS, URetinex-Net, SCI, SNR-Aware, LLFlow → Retinexformer,
  Diff-Retinex, GSAD, LLFormer → Zero-IG, LightenDiffusion, QuadPrior, MambaLLIE, GLARE,
  CoLIE → CWNet, Efficient Diffusion, RETINEV (2025). [B, C]
- **Color-space family (move 5, "our angle"):** Bread (IJCV 2023), DCC-Net (CVPR 2022),
  LCDPNet (ECCV 2022), IAT (BMVC 2022), CoLIE (ECCV 2024, HSV), Ucolor (TIP 2021, multi-space
  fusion), CSTNet (NeurIPS 2025, learnable YCbCr-like space for deraining), CATformer (TCSVT
  2026, von Kries + CIELAB), LYT-Net (SPL 2025, YUV), plus the 2026 preprints AdaLAB,
  log-domain IC decoupling, YUV revisit. [A, D]
- **HVI follow-ups to position against (related-work appendix):** HVI-CIDNet+ (TCSVT 2026),
  FusionNet (CVPRW 2025, NTIRE winner), RHVI-FDD, BC-IHV, TCA-Net, VCR (TCSVT 2026), HAIMNet
  (TIP 2026), InterLight, TPCNet, JarvisIR (CVPR 2025, reuses CIDNet as a tool). [D]
- **Protocol justification (method section):** Musgrave et al. (ECCV 2020) for
  validation-vs-test selection; Bouthillier et al. (MLSys 2021) and Pineau et al. (JMLR
  2021) for seeds and error bars; Recht et al. (ICML 2019) for test-set reuse, cited
  carefully; Nguyen et al. (WACV 2024) for LOL train/test scene overlap; Liao et al. (ICCV
  2025) and Wang & Bovik (2009) for GT-mean; NTIRE 2024/2025/2026 for hidden-GT practice;
  Dror et al. (ACL 2018) and Koehn (EMNLP 2004) for paired tests on 15 images. [E]
- **Loss provenance (if C4 or any loss ablation runs):** Johnson et al. (ECCV 2016), Ledig
  et al. (CVPR 2017), Zhao et al. (TCI 2017), Lai et al. (CVPR 2017), MPRNet (CVPR 2021),
  Zero-DCE color-constancy loss, Jo et al. (CVPRW 2020) for LPIPS-as-loss and weight
  sensitivity, U-Shape Transformer (TIP 2023) for the dual-space precedent. [F]
- **Architecture provenance:** Restormer (CVPR 2022, MDTA + GDFN → LCA), Uformer, NAFNet,
  SwinIR, MIRNet, and the two-branch neighbours Bread, DCC-Net, LYT-Net, URetinex-Net,
  Retinexformer, SNR-Aware. [F]

## 3. Reproducibility record for HVI-CIDNet's LOL-v1 number (from D; every line has a source)

| Source | LOL-v1 PSNR / SSIM | Protocol note |
|---|---|---|
| HVI-CIDNet paper, carried into HVI-CIDNet+ Table I | 28.20 / 0.889 | GT-mean (stated in HVI-CIDNet+) |
| README `w_perc`, no GT-mean | 23.81 / 0.857 | authors' weights |
| FusionNet (same group, CVPRW 2025) | 23.50 / 0.870 | not stated; consistent with no GT-mean |
| PAL (arXiv 2604.08172), retrained "original config" | 23.97 / 0.849 | no GT-mean implied |
| GitHub issue #66, RTX 4090, default hyper-parameters | 23.59 / 0.854 | user retrain, closed without explanation |
| GitHub issue #50 | 24.7 | third-party, hyper-parameters unknown |
| NTIRE 2026 challenge data, zero-shot CIDNet | 13.85 | below gamma correction (14.91) |

Open GitHub issues #160 / #162 / #163 ask about LOL-v1 reproduction, LOLv2-Real (23.89 vs
24.11), and how checkpoints were selected without a validation split.

## 4. Items that still need attention before anything is cited

- `E`: `pilligua2025multiintensity` and `shafi2026iphoneblur` are arXiv-only (VERIFIED: no).
- `D`: RHVI-FDD's "ICMR 2026" and InterLight's "IJCAI 2026" come from the papers themselves.
- Bread's author order differs between slices (`hu2023bread` in A vs `guo2023bread` in B/F);
  Springer lists Guo, Hu. `survey.bib` keeps `guo2023bread`.
- `C`: most 2023–2026 entries have LOL-v1 PSNR marked n/a; numbers must come from the papers'
  tables, not from this survey, before they enter the paper.
- `writing` still owns `custom.bib`: merge from `survey.bib` only after its own
  bibtex-verify pass (one subagent per entry), per harness/writing.md §4c.
