# Color-space-based Low-Light Image Enhancement — Literature Scout Output

Slice: deep LLIE methods that operate in, decompose into, or supervise in a non-RGB color space, for
comparison against HVI-CIDNet (Yan et al., CVPR 2025, arXiv 2502.20272).

---

### hu2023bread
- Title: Low-light Image Enhancement via Breaking Down the Darkness
- Authors: Qiming Hu, Xiaojie Guo
- Venue: International Journal of Computer Vision (IJCV) 2023 (Tier 1) — VERIFIED: yes (link.springer.com/article/10.1007/s11263-022-01667-9)
- Link: https://arxiv.org/abs/2111.15557
- Color space / what it does: Converts RGB to a luminance-chrominance space; brightens/denoises luminance, then uses the enhanced luminance to guide a chrominance mapper for color restoration.
- Relevance to HVI-CIDNet: Same "decouple luminance from color, restore separately" philosophy as HVI, but in a fixed (non-learned, non-polar) luminance-chrominance space rather than HVI's polarized HS + learnable intensity. Leaves open whether HVI's polarization/learnable-intensity actually beats a simpler luminance-chrominance split under matched capacity.
- Reported LOL-v1 PSNR if stated: n/a (not stated in sources reviewed)
```bibtex
@article{hu2023bread, title={Low-light Image Enhancement via Breaking Down the Darkness}, author={Hu, Qiming and Guo, Xiaojie}, journal={International Journal of Computer Vision}, year={2023}}
```

### brateanu2025lytnet
- Title: LYT-NET: Lightweight YUV Transformer-based Network for Low-Light Image Enhancement
- Authors: Alexandru Brateanu, Raul Balmez, Adrian Avram, et al.
- Venue: IEEE Signal Processing Letters 2025 (not in specified Tier1/Tier2 venue list; noted as "Other") — VERIFIED: yes (github.com/albrateanu/LYT-Net states "[SPL 2025]"; DOI 10.1109/LSP.2025.3563125)
- Link: https://arxiv.org/abs/2401.15204
- Color space / what it does: Fixed YUV decomposition; separate lightweight paths for luminance (Y) and chrominance (U,V) with cross-fusion (MSEF) blocks.
- Relevance to HVI-CIDNet: A direct "YUV vs HVI" data point — same luminance/chrominance-separation idea but with a classical, non-learned color transform and a much smaller network. Good baseline for an ablation isolating color-space choice from network capacity.
- Reported LOL-v1 PSNR if stated: n/a (not confirmed in sources reviewed)
```bibtex
@article{brateanu2025lytnet, title={LYT-NET: Lightweight YUV Transformer-based Network for Low-Light Image Enhancement}, author={Brateanu, Alexandru and Balmez, Raul and Avram, Adrian and Orhei, Ciprian and Ancuti, Cosmin}, journal={IEEE Signal Processing Letters}, year={2025}}
```

### zhang2022dccnet
- Title: Deep Color Consistent Network for Low-Light Image Enhancement
- Authors: Zhao Zhang, Huan Zheng, Richang Hong, et al.
- Venue: CVPR 2022 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content/CVPR2022/papers/Zhang_Deep_Color_Consistent_Network_for_Low-Light_Image_Enhancement_CVPR_2022_paper.pdf)
- Link: https://openaccess.thecvf.com/content/CVPR2022/papers/Zhang_Deep_Color_Consistent_Network_for_Low-Light_Image_Enhancement_CVPR_2022_paper.pdf
- Color space / what it does: Decouples a low-light image into a gray (structure/texture) image plus an explicit color histogram; a Pyramid Color Embedding module re-injects color into the enhancement pipeline.
- Relevance to HVI-CIDNet: An alternative "decouple structure from color" strategy that uses gray + histogram rather than a genuine alternate color-space basis (H/V/I). Useful as a non-HVI, non-YUV/HSV color-decoupling baseline to broaden the comparison beyond simple color-space swaps.
- Reported LOL-v1 PSNR if stated: n/a (not confirmed in sources reviewed)
```bibtex
@inproceedings{zhang2022dccnet, title={Deep Color Consistent Network for Low-Light Image Enhancement}, author={Zhang, Zhao and Zheng, Huan and Hong, Richang and Xu, Mingliang and Yan, Shuicheng and Wang, Meng}, booktitle={CVPR}, year={2022}}
```

### ma2022csdnet
- Title: Learning Deep Context-Sensitive Decomposition for Low-Light Image Enhancement
- Authors: Long Ma, Risheng Liu, Jiaao Zhang, et al.
- Venue: IEEE Transactions on Neural Networks and Learning Systems (TNNLS) 2022 (not in specified Tier1/Tier2 list; noted as "Other") — VERIFIED: yes (ieeexplore.ieee.org/document/9420270)
- Link: https://arxiv.org/abs/2112.05147
- Color space / what it does: Retinex-style two-stream reflectance/illumination decomposition with a "context-sensitive decomposition connection"; not a genuine alternate color-space basis but a luminance/reflectance split, listed here as the closest CSDNet match to the thesis's seed example.
- Relevance to HVI-CIDNet: Illustrates the Retinex-decomposition alternative to color-space reparameterization; worth citing to distinguish "decompose via physical Retinex model" from "reparameterize into a new color space" (HVI's actual claim).
- Reported LOL-v1 PSNR if stated: n/a
```bibtex
@article{ma2022csdnet, title={Learning Deep Context-Sensitive Decomposition for Low-Light Image Enhancement}, author={Ma, Long and Liu, Risheng and Zhang, Jiaao and Fan, Xin and Luo, Zhongxuan}, journal={IEEE Transactions on Neural Networks and Learning Systems}, volume={33}, number={10}, pages={5666--5680}, year={2022}}
```

### cui2022iat
- Title: You Only Need 90K Parameters to Adapt Light: A Light Weight Transformer for Image Enhancement and Exposure Correction
- Authors: Ziteng Cui, Kunchang Li, Lin Gu, et al.
- Venue: BMVC 2022 (Tier 2) — VERIFIED: yes (bmvc2022.mpi-inf.mpg.de/0238.pdf; github.com/cuiziteng/Illumination-Adaptive-Transformer)
- Link: https://arxiv.org/abs/2205.14871
- Color space / what it does: Operates in sRGB but its global branch predicts a 3x3 color-correction matrix + gamma (an implicit, learned color transform), inspired by classic ISP color pipelines.
- Relevance to HVI-CIDNet: Shows a much cheaper (~90K param) alternative to learning color correction implicitly via a matrix rather than by moving to an explicit new color space; useful as an efficiency/parameter-count reference point rather than a color-space peer.
- Reported LOL-v1 PSNR if stated: n/a (not confirmed in sources reviewed; original paper reports ~23-24 dB range on LOL but exact figure not verified here)
```bibtex
@inproceedings{cui2022iat, title={You Only Need 90K Parameters to Adapt Light: A Light Weight Transformer for Image Enhancement and Exposure Correction}, author={Cui, Ziteng and Li, Kunchang and Gu, Lin and Su, Shenghan and Gao, Peng and Jiang, Zhengkai and Qiao, Yu and Harada, Tatsuya}, booktitle={BMVC}, year={2022}}
```

### yin2023clediffusion
- Title: CLE Diffusion: Controllable Light Enhancement Diffusion Model
- Authors: Yuyang Yin, Dejia Xu, Chuangchuang Tan, et al.
- Venue: ACM MM 2023 (Tier 2) — VERIFIED: yes (dl.acm.org/doi/10.1145/3581783.3612145)
- Link: https://arxiv.org/abs/2308.06725
- Color space / what it does: sRGB-space conditional diffusion model with an illumination-embedding for user-controllable brightness; not itself color-space-based, included because it is a common LLIE comparator with explicit brightness/color controllability that any color-space claim (like HVI's) should be checked against.
- Relevance to HVI-CIDNet: Diffusion + SAM-guided region control is a different axis (controllability) than color-space choice; useful mainly as a non-color-space SOTA reference, not a direct color-space ablation partner.
- Reported LOL-v1 PSNR if stated: n/a
```bibtex
@inproceedings{yin2023clediffusion, title={CLE Diffusion: Controllable Light Enhancement Diffusion Model}, author={Yin, Yuyang and Xu, Dejia and Tan, Chuangchuang and Liu, Ping and Zhao, Yao and Wei, Yunchao}, booktitle={ACM International Conference on Multimedia (ACM MM)}, year={2023}}
```

### lore2017llnet
- Title: LLNet: A Deep Autoencoder Approach to Natural Low-light Image Enhancement
- Authors: Kin Gwn Lore, Adedotun Akintayo, Soumik Sarkar
- Venue: Pattern Recognition, vol. 61, 2017 (not in specified Tier1/Tier2 list; included as the field's foundational deep-learning baseline per seed list) — VERIFIED: yes (ui.adsabs.harvard.edu/abs/2017PatRe..61..650L/abstract)
- Link: https://arxiv.org/abs/1511.03995
- Color space / what it does: Stacked sparse denoising autoencoder trained directly on (synthetically darkened) intensity/RGB patches; does NOT perform an explicit color-space transform or luminance/chrominance decoupling.
- Relevance to HVI-CIDNet: Historical anchor showing the pre-color-space-aware era of deep LLIE; useful only to frame how far the field has moved toward explicit color-space reasoning, not as a color-space comparator itself.
- Reported LOL-v1 PSNR if stated: n/a (LOL dataset postdates this paper)
```bibtex
@article{lore2017llnet, title={LLNet: A deep autoencoder approach to natural low-light image enhancement}, author={Lore, Kin Gwn and Akintayo, Adedotun and Sarkar, Soumik}, journal={Pattern Recognition}, volume={61}, pages={650--662}, year={2017}}
```

### zhang2019kind
- Title: Kindling the Darkness: A Practical Low-light Image Enhancer
- Authors: Yonghua Zhang, Jiawan Zhang, Xiaojie Guo
- Venue: ACM MM 2019 (Tier 2) — VERIFIED: yes (dl.acm.org/doi/10.1145/3343031.3350926)
- Link: https://arxiv.org/abs/1905.04161
- Color space / what it does: Retinex-based split into illumination and reflectance layers (not a color-space reparameterization, but the classic luminance/reflectance decoupling precedent that HVI-style methods build on).
- Relevance to HVI-CIDNet: Standard baseline almost every LLIE color/illumination-decoupling paper (including HVI-CIDNet's lineage) compares against; useful as the canonical "decompose, don't reparameterize" reference point.
- Reported LOL-v1 PSNR if stated: n/a (commonly cited ~20.8 dB in later surveys, but not independently confirmed here)
```bibtex
@inproceedings{zhang2019kind, title={Kindling the Darkness: A Practical Low-light Image Enhancer}, author={Zhang, Yonghua and Zhang, Jiawan and Guo, Xiaojie}, booktitle={ACM International Conference on Multimedia (ACM MM)}, year={2019}}
```

### wang2022lcdpnet
- Title: Local Color Distributions Prior for Image Enhancement
- Authors: Haoyuan Wang, Ke Xu, Rynson W.H. Lau
- Venue: ECCV 2022 (Tier 1) — VERIFIED: yes (link.springer.com/chapter/10.1007/978-3-031-19797-0_20; github.com/onpix/LCDPNet)
- Link: https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136780336.pdf
- Color space / what it does: Stays in sRGB but models local color-histogram/distribution priors per region to jointly fix over- and under-exposure; not a color-space swap, included as the closest "color-distribution-as-prior" adjacent work.
- Relevance to HVI-CIDNet: Represents an alternative to changing color space entirely — using local color statistics as a prior within RGB. Highlights a gap: no work has cross-compared "new color space" (HVI) vs "color-distribution prior in RGB" (LCDPNet) under one architecture.
- Reported LOL-v1 PSNR if stated: n/a (paper reports its own dataset/MSEC PSNR ~22.3-23.2 dB, not LOL-v1)
```bibtex
@inproceedings{wang2022lcdpnet, title={Local Color Distributions Prior for Image Enhancement}, author={Wang, Haoyuan and Xu, Ke and Lau, Rynson W.H.}, booktitle={ECCV}, year={2022}}
```

### li2021ucolor
- Title: Underwater Image Enhancement via Medium Transmission-Guided Multi-Color Space Embedding
- Authors: Chongyi Li, Saeed Anwar, Junhui Hou, et al.
- Venue: IEEE Transactions on Image Processing (TIP), vol. 30, 2021 (Tier 2) — VERIFIED: yes (DOI 10.1109/TIP.2021.3076367; pubmed.ncbi.nlm.nih.gov/33961554)
- Link: https://arxiv.org/abs/2104.13015
- Color space / what it does: Encodes features from multiple color spaces (RGB, HSV, Lab) simultaneously with an attention mechanism, guided by a physical medium-transmission model, rather than committing to one alternate space.
- Relevance to HVI-CIDNet: Adjacent-domain (underwater) evidence that fusing several color spaces can outperform any single one — a different strategy from HVI's "engineer one better space." Directly relevant to the thesis's core question of whether one bespoke space (HVI) beats using/combining existing ones.
- Reported LOL-v1 PSNR if stated: n/a (underwater benchmarks, not LOL)
```bibtex
@article{li2021ucolor, title={Underwater Image Enhancement via Medium Transmission-Guided Multi-Color Space Embedding}, author={Li, Chongyi and Anwar, Saeed and Hou, Junhui and Cong, Runmin and Guo, Chunle and Ren, Wenqi}, journal={IEEE Transactions on Image Processing}, volume={30}, pages={4985--5000}, year={2021}}
```

### he2025dlfenet
- Title: DLFE-Net: Preserving Details and Removing Noise Using HVI Color Space for Low-Light Image Enhancement
- Authors: Zhaokun He, Xin Yuan, Guozhu Hao, et al.
- Venue: Sensors (MDPI), 2025 (not in specified Tier1/Tier2 list; noted as "Other") — VERIFIED: yes (DOI 10.3390/s25175353; pmc.ncbi.nlm.nih.gov/articles/PMC12431520)
- Link: https://doi.org/10.3390/s25175353
- Color space / what it does: Directly adopts HVI color space (from Yan et al.) and adds detail-preserving/noise-removal branches on top of intensity and color maps.
- Relevance to HVI-CIDNet: A direct downstream user/extension of HVI itself — evidence the community is already treating HVI as a reusable component rather than re-testing it against sRGB/HSV/YCbCr under matched conditions, which is exactly the gap the thesis targets.
- Reported LOL-v1 PSNR if stated: n/a (not confirmed in sources reviewed)
```bibtex
@article{he2025dlfenet, title={DLFE-Net: Preserving Details and Removing Noise Using HVI Color Space for Low-Light Image Enhancement}, author={He, Zhaokun and Yuan, Xin and Hao, Guozhu and Wang, Wei}, journal={Sensors}, volume={25}, number={17}, pages={5353}, year={2025}}
```

### yan2025hvicidnetplus
- Title: HVI-CIDNet+: Beyond Extreme Darkness for Low-Light Image Enhancement
- Authors: Qingsen Yan, Kangbiao Shi, Yixu Feng, et al.
- Venue: arXiv preprint, 2025 (preprint) — VERIFIED: yes (arxiv.org/abs/2507.06814, submitted July 9 2025; directly authored by the original HVI-CIDNet team)
- Link: https://arxiv.org/abs/2507.06814
- Color space / what it does: Extends HVI-CIDNet with a Prior-guided Attention Block (using pretrained vision-language priors) and a Region Refinement Block, staying in the HVI color space.
- Relevance to HVI-CIDNet: The authors' own follow-up — confirms HVI is being iterated on for capacity/robustness rather than re-examined for whether the color space itself (vs. network additions) is what drives gains. Directly useful to cite when arguing the "does HVI itself help" question remains unanswered even by the original authors.
- Reported LOL-v1 PSNR if stated: n/a (reports gains mainly on extreme-dark/LOL-variant sets, exact figure not confirmed here)
```bibtex
@article{yan2025hvicidnetplus, title={HVI-CIDNet+: Beyond Extreme Darkness for Low-Light Image Enhancement}, author={Yan, Qingsen and Shi, Kangbiao and Feng, Yixu and Hu, Tao and Wu, Peng and Pang, Guansong and Zhang, Yanning}, journal={arXiv preprint arXiv:2507.06814}, year={2025}}
```

### yang2026rhvifdd
- Title: RHVI-FDD: A Hierarchical Decoupling Framework for Low-Light Image Enhancement
- Authors: Junhao Yang, Bo Yang, Hongwei Ge, et al.
- Venue: arXiv preprint, 2026 (preprint) — VERIFIED: yes (arxiv.org/abs/2604.05781, submitted April 7 2026)
- Link: https://arxiv.org/abs/2604.05781
- Color space / what it does: Proposes an "RHVI transform" (robust variant of HVI) plus a Discrete-Cosine-Transform-based Frequency-Domain Decoupling module that further splits chrominance into low/mid/high-frequency bands (tone, detail, noise).
- Relevance to HVI-CIDNet: A 2026 direct modification of HVI itself aimed at fixing noise-driven estimation bias in the H/V transform — strong evidence the exact HVI formulation still has known weaknesses, and a candidate for a "HVI vs RHVI vs sRGB" ablation.
- Reported LOL-v1 PSNR if stated: n/a (not confirmed in sources reviewed)
```bibtex
@article{yang2026rhvifdd, title={RHVI-FDD: A Hierarchical Decoupling Framework for Low-Light Image Enhancement}, author={Yang, Junhao and Yang, Bo and Ge, Hongwei and Liang, Yanchun and Lee, Heow Pueh and Wu, Chunguo}, journal={arXiv preprint arXiv:2604.05781}, year={2026}}
```

### wu2026tcanet
- Title: Thresholded Cross-Attention for Reliable Intensity-Chromaticity Fusion in Low-Light Image Enhancement
- Authors: Yanyi Wu, Xu Zhang, Junkai Chen, et al.
- Venue: arXiv preprint, 2026 (preprint) — VERIFIED: yes (arxiv.org/abs/2607.13925, submitted July 15 2026)
- Link: https://arxiv.org/abs/2607.13925
- Color space / what it does: Works within the HVI framework; replaces fixed Top-K sparse cross-attention (as used to fuse intensity and chromaticity streams, e.g. in CIDNet) with an adaptive, confidence-thresholded attention (TCA-Net).
- Relevance to HVI-CIDNet: Targets the intensity-chromaticity fusion mechanism inside HVI-style networks specifically, isolating "is it the color space or the fusion attention that helps" — directly useful for the thesis's ablation framing.
- Reported LOL-v1 PSNR if stated: n/a (not confirmed in sources reviewed)
```bibtex
@article{wu2026tcanet, title={Thresholded Cross-Attention for Reliable Intensity-Chromaticity Fusion in Low-Light Image Enhancement}, author={Wu, Yanyi and Zhang, Xu and Chen, Junkai and Chang, Laibin and Ma, Jiaqi and Chen, Shi and Zhu, Linwei and Di, Jianglei and Zhang, Huan}, journal={arXiv preprint arXiv:2607.13925}, year={2026}}
```

### yang2026cage
- Title: Towards Color-Faithful Low-Light Image Enhancement via Adaptive Color Debiasing and Saturation Rectification
- Authors: Zhichen Yang, Rui Xu, Yuzhen Niu, et al.
- Venue: arXiv preprint, 2026 (preprint) — VERIFIED: yes (arxiv.org/abs/2608.10512, submitted August 11 2026)
- Link: https://arxiv.org/abs/2608.10512
- Color space / what it does: Introduces "AdaLAB," a cylindrical, per-image-adaptive LAB color space with a forward transform (AdaCCT) that de-biases chroma before enhancement and an inverse transform that rectifies saturation/gamut afterward.
- Relevance to HVI-CIDNet: A LAB-based, explicitly adaptive/learnable alternate color space proposed in the same spirit as HVI (fix known color-space pathologies via a bespoke transform) but built on LAB/cylindrical geometry instead of a polar HSV-like basis — a natural third color-space arm (sRGB/HSV/YCbCr/HVI/AdaLAB) for the thesis's comparison.
- Reported LOL-v1 PSNR if stated: n/a (not confirmed in sources reviewed)
```bibtex
@article{yang2026cage, title={Towards Color-Faithful Low-Light Image Enhancement via Adaptive Color Debiasing and Saturation Rectification}, author={Yang, Zhichen and Xu, Rui and Niu, Yuzhen and Li, Fusheng and Da, Hui and Cheng, Ri}, journal={arXiv preprint arXiv:2608.10512}, year={2026}}
```

### yan2026yuvrevisit
- Title: Revisiting Lightweight Low-Light Image Enhancement: From a YUV Color Space Perspective
- Authors: Hailong Yan, Shice Liu, Xiangtao Zhang, et al.
- Venue: arXiv preprint, 2026 (preprint) — VERIFIED: yes (arxiv.org/abs/2601.17349, submitted January 24 2026)
- Link: https://arxiv.org/abs/2601.17349
- Color space / what it does: Frequency-domain analysis showing Y loses low-frequency content while U/V are corrupted by high-frequency noise under low light; designs channel-specific attention modules per YUV channel accordingly.
- Relevance to HVI-CIDNet: Directly argues for YUV on frequency-domain grounds (a different justification than HVI's red-artifact/black-artifact motivation) — a strong, recent, matched-network-style YUV baseline/justification to set against HVI's polar-space argument.
- Reported LOL-v1 PSNR if stated: n/a (not confirmed in sources reviewed)
```bibtex
@article{yan2026yuvrevisit, title={Revisiting Lightweight Low-Light Image Enhancement: From a YUV Color Space Perspective}, author={Yan, Hailong and Liu, Shice and Zhang, Xiangtao and Yao, Lujian and Yang, Fengxiang and Chen, Jinwei and Li, Bo}, journal={arXiv preprint arXiv:2601.17349}, year={2026}}
```

### bai2026logdomain
- Title: Rethinking Low-Light Image Enhancement: A Log-Domain Intensity–Chromaticity Decoupling Perspective
- Authors: Guangrui Bai, Yifan Mei, Yahui Deng, et al.
- Venue: arXiv preprint, 2026 (preprint) — VERIFIED: yes (arxiv.org/abs/2605.02627, submitted May 4 2026)
- Link: https://arxiv.org/abs/2605.02627
- Color space / what it does: Decouples intensity and chromaticity in the log domain (rather than HVI's polar/linear domain) with explicit reconstruction constraints to curb channel amplification and chromatic noise.
- Relevance to HVI-CIDNet: Another 2026 intensity-chromaticity decoupling scheme, but in log space instead of HVI's polar space — directly comparable "which decoupling geometry helps" data point, and it reports numbers on LOLv2-Real/FiveK/LSRW rather than LOL-v1, widening the benchmark set worth matching.
- Reported LOL-v1 PSNR if stated: n/a (reports 29.71 dB PSNR / 0.89 SSIM on LOLv2-Real, not LOL-v1)
```bibtex
@article{bai2026logdomain, title={Rethinking Low-Light Image Enhancement: A Log-Domain Intensity--Chromaticity Decoupling Perspective}, author={Bai, Guangrui and Mei, Yifan and Deng, Yahui and Chen, Yuhan and Qiu, Yuze and Liu, Wenhai and Dong, Erbao}, journal={arXiv preprint arXiv:2605.02627}, year={2026}}
```

---

## Gaps I noticed

1. No study holds the network architecture and seeds fixed while swapping *only* the input/output color space among sRGB, HSV, YCbCr, LAB, and HVI — every paper reviewed pairs its proposed space with its own bespoke architecture, so HVI's gains are confounded with CIDNet's cross-attention design.
2. Almost no paper reports LOL-v1 PSNR alongside a clearly stated ablation of "same network, RGB vs. color-space-X input" — most color-space claims rest on comparing full pipelines against other papers' full pipelines, not controlled swaps.
3. The 2025-2026 HVI-adjacent preprints (HVI-CIDNet+, RHVI-FDD, TCA-Net, DLFE-Net) all extend or reuse HVI rather than testing whether a different space (YCbCr, LAB/AdaLAB, plain YUV) plugged into the *same* CIDNet backbone would match or beat it.
4. Underwater/restoration multi-color-space work (Ucolor) shows fusing several spaces can beat any single space, but this fusion strategy has not been tried against HVI under an LLIE-matched network — an open ablation arm (single new space vs. multi-space fusion).
5. No identified work compares HVI against the two 2026 alternative decoupling geometries found here (AdaLAB's cylindrical LAB, and the log-domain intensity-chromaticity split) under one shared encoder/decoder and training seed, which is precisely the controlled comparison the thesis proposes to run.
