# D. Follow-ups, extensions, reuses and critiques of HVI-CIDNet / HVI colour space (2024-2026)

Sources: I pulled the Semantic Scholar citation lists for arXiv 2502.20272 (228 citing papers) and 2402.05809 (83 citing papers) on 2026-09-24, then triaged them. I scanned arXiv HTML full texts for "HVI"/"CIDNet", resolved DOIs through doi.org, and read the HVI-CIDNet GitHub issues.
Tier key: Tier 1 = CVPR/ICCV/ECCV/NeurIPS/ICLR/ICML/TPAMI/IJCV. Tier 2 = AAAI/ACM MM/TIP/TCSVT/WACV/BMVC/TMM. Workshop papers (CVPRW/NTIRE) and papers at venues outside the filter are marked "preprint".
"VERIFIED: yes" means the DOI resolved (doi.org handle API) or the arXiv ID resolved.

---

### yan2025hvicidnetplus
- Title: HVI-CIDNet+: Beyond Extreme Darkness for Low-Light Image Enhancement
- Authors: Qingsen Yan, Kangbiao Shi, Yixu Feng, et al.
- Venue: IEEE TCSVT 2026 (early access; arXiv Jul 2025) (Tier 2) — VERIFIED: yes (DOI 10.1109/TCSVT.2026.3710237 resolves to IEEE Xplore 11595581)
- Link: https://arxiv.org/abs/2507.06814
- What it takes from HVI-CIDNet: transform | architecture | loss (journal extension by the same group)
- What it changes or criticises: adds VLM-derived semantic/degradation priors via a Prior-guided Attention Block, plus a Region Refinement Block (conv for information-rich regions, attention for information-scarce ones), aimed at extreme darkness.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? yes, partly. Table V (LOL-v1, same network) reports sRGB 27.259, HSV 25.857, HVI polarization-only 27.788, HVI C_k-only 27.989, full HVI 28.846 dB. C_k is only switched on or off. k is never swept.
- Does it report seeds or variance? no (single numbers; LOL-v1 evaluated with GT-mean)
```bibtex
@article{yan2025hvicidnetplus, title={{HVI-CIDNet+}: Beyond Extreme Darkness for Low-Light Image Enhancement}, author={Yan, Qingsen and Shi, Kangbiao and Feng, Yixu and Hu, Tao and Wu, Peng and Pang, Guansong and Zhang, Yanning}, journal={IEEE Transactions on Circuits and Systems for Video Technology}, year={2026}, doi={10.1109/TCSVT.2026.3710237}}
```

### shi2025fusionnet
- Title: FusionNet: Multi-Model Linear Fusion Framework for Low-Light Image Enhancement
- Authors: Kangbiao Shi, Yixu Feng, Tao Hu, et al.
- Venue: CVPR Workshops (NTIRE) 2025 (preprint — workshop, outside tier list) — VERIFIED: yes (DOI 10.1109/CVPRW67362.2025.00101; arXiv 2504.19295)
- Link: https://arxiv.org/abs/2504.19295
- What it takes from HVI-CIDNet: architecture | checkpoint-level model (CIDNet used as one of three parallel branches) | loss
- What it changes or criticises: linearly fuses CIDNet (HVI), Retinexformer (sRGB) and ESDNet (CNN). It won 1st place in NTIRE 2025 LLIE. It states that because k is trainable, HVI is data-driven, may lack strict independence, and may generalise worse when datasets or scenes change.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no controlled colour-space comparison. The "k1, k2, k3" swept in Fig. 5 (optimum 0.16/0.40/0.44, which sums to 1) appear to be linear fusion weights, not the HVI density k.
- Does it report seeds or variance? no
```bibtex
@inproceedings{shi2025fusionnet, title={{FusionNet}: Multi-Model Linear Fusion Framework for Low-Light Image Enhancement}, author={Shi, Kangbiao and Feng, Yixu and Hu, Tao and Cao, Yu and Wu, Peng and Liang, Yijin and Zhang, Yanning and Yan, Qingsen}, booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW)}, year={2025}}
```

### liu2025ntire
- Title: NTIRE 2025 Challenge on Low Light Image Enhancement: Methods and Results
- Authors: Xiaoning Liu, Zongwei Wu, Florin-Alexandru Vasluianu, et al.
- Venue: CVPR Workshops 2025 (preprint — workshop/challenge report) — VERIFIED: yes (DOI 10.1109/CVPRW67362.2025.00114; arXiv 2510.13670)
- Link: https://arxiv.org/abs/2510.13670
- What it takes from HVI-CIDNet: architecture (via the winning team NWPU-HVI / FusionNet)
- What it changes or criticises: challenge report. 28 valid teams. The HVI-based FusionNet ranked 1st (PSNR 26.24, SSIM 0.861). In the text I scanned, the only explicit HVI/CIDNet mentions belong to the NWPU-HVI entry.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no
- Does it report seeds or variance? no
```bibtex
@inproceedings{liu2025ntire, title={{NTIRE} 2025 Challenge on Low Light Image Enhancement: Methods and Results}, author={Liu, Xiaoning and Wu, Zongwei and Vasluianu, Florin-Alexandru and others}, booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW)}, year={2025}}
```

### ciubotariu2026ntire
- Title: Low Light Image Enhancement Challenge at NTIRE 2026
- Authors: G. Ciubotariu, A. Sharif (listed as "A. SharifSM" in S2), Abdur Rehman, et al.
- Venue: arXiv 2026 (preprint; NTIRE 2026 challenge report) — VERIFIED: yes (arXiv 2604.17669 resolves)
- Link: https://arxiv.org/abs/2604.17669
- What it takes from HVI-CIDNet: architecture | checkpoint (several team entries)
- What it changes or criticises: HVI/CIDNet entries include WIRNet (Track 2 rank 4; gated LCA plus DWT inside CIDNet, argues the I-branch entangles noise with high frequencies), BAU-Vision "Wave-P" (Track 1 rank 5; says CIDNet's interpolation sampling loses high frequencies) and SNUCV MB-LPFR (Track 1 rank 6; CIDNet+ as the low-frequency branch fused with OSEDiff). Team YuFans reports that zero-shot CIDNet scored only 13.85 dB on the challenge data, below plain gamma correction (14.91 dB).
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no
- Does it report seeds or variance? no
```bibtex
@article{ciubotariu2026ntire, title={Low Light Image Enhancement Challenge at {NTIRE} 2026}, author={Ciubotariu, G. and Sharif, A. and Rehman, Abdur and others}, journal={arXiv preprint arXiv:2604.17669}, year={2026}}
```

### yan2026ntireellie
- Title: NTIRE 2026 Challenge on Efficient Low Light Image Enhancement: Methods and Results
- Authors: Jiebin Yan, Chenyu Tu, Weixia Zhang, et al.
- Venue: arXiv 2026 (preprint; NTIRE 2026 challenge report) — VERIFIED: yes (arXiv 2605.02212 resolves)
- Link: https://arxiv.org/abs/2605.02212
- What it takes from HVI-CIDNet: transform | architecture | loss (team entries)
- What it changes or criticises: three sub-1M-parameter HVI entries. NCHU-CVLab "Efficient-HVI" (rank 5, 0.96M). sysu_701 (rank 12; CIDNet with a shallower U-Net, fewer channels and heads, plus "dynamic HVI weighting"). Cidaut AI (rank 17; IEL replaced with a NAFBlock-style NIEL, CIDNet RGB+HVI loss kept).
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no
- Does it report seeds or variance? no
```bibtex
@article{yan2026ntireellie, title={{NTIRE} 2026 Challenge on Efficient Low Light Image Enhancement: Methods and Results}, author={Yan, Jiebin and Tu, Chenyu and Zhang, Weixia and others}, journal={arXiv preprint arXiv:2605.02212}, year={2026}}
```

### yang2026rhvifdd
- Title: RHVI-FDD: A Hierarchical Decoupling Framework for Low-Light Image Enhancement
- Authors: Junhao Yang, Bo Yang, Hongwei Ge, et al.
- Venue: arXiv 2026; the paper header says ACM ICMR 2026 (preprint — ICMR is outside the tier list) — VERIFIED: yes for arXiv 2604.05781; ICMR acceptance not independently verified
- Link: https://arxiv.org/abs/2604.05781
- What it takes from HVI-CIDNet: transform | architecture (HVI-CIDNet is the stated baseline)
- What it changes or criticises: argues that the Max-RGB intensity in HVI is very sensitive to positive noise spikes. Adds an Illumination Refinement Module (RHVI = robust HVI) and a DCT-based three-band Frequency-Domain Decoupling of chrominance features.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? yes, partly. Its colour-space ablation on LOLv2-Real reports HSV 21.698, HVI 23.921, RHVI 24.822 dB. k is not ablated.
- Does it report seeds or variance? no
```bibtex
@inproceedings{yang2026rhvifdd, title={{RHVI-FDD}: A Hierarchical Decoupling Framework for Low-Light Image Enhancement}, author={Yang, Junhao and Yang, Bo and Ge, Hongwei and Liang, Yanchun and Lee, Heow Pueh and Wu, Chunguo}, booktitle={Proceedings of the ACM International Conference on Multimedia Retrieval (ICMR)}, year={2026}, note={arXiv:2604.05781}}
```

### ai2026bcihv
- Title: BC-IHV: Conditioning the Color Space for Stable Rectified-Flow Low-Light Enhancement
- Authors: Yi Ai, Zheng Chen, Yuanhao Cai, et al.
- Venue: arXiv 2026 (preprint, submitted 22 Aug 2026) — VERIFIED: yes (arXiv 2608.21847 resolves)
- Link: https://arxiv.org/abs/2608.21847
- What it takes from HVI-CIDNet: transform (keeps HVI chromaticity with the k-power term unchanged) | baseline
- What it changes or criticises: argues that HVI keeps a linear intensity v = max(R,G,B), which crowds dark values near zero. Replaces it with a learnable Box-Cox intensity (lambda = 1 gives back HVI) inside a structure-anchored rectified-flow model.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? yes for intensity, no for k. It runs a controlled comparison with the same SA-RF network, losses and schedule on LOLv2-Real: HVI 22.54, log-IHV 22.99, BC-IHV 24.21 dB. Learned lambda was 0.818 / 0.646 / 0.569 on LOL-v1 / v2-Real / v2-Syn. k is not ablated. There is no sRGB, HSV or YCbCr arm.
- Does it report seeds or variance? partly. It mentions "independent seeds" and five-point means for training trajectories, but gives no std for the main tables.
```bibtex
@article{ai2026bcihv, title={{BC-IHV}: Conditioning the Color Space for Stable Rectified-Flow Low-Light Enhancement}, author={Ai, Yi and Chen, Zheng and Cai, Yuanhao and Zhang, Yulun and Yang, Xiaokang}, journal={arXiv preprint arXiv:2608.21847}, year={2026}}
```

### wu2026tcanet
- Title: Thresholded Cross-Attention for Reliable Intensity-Chromaticity Fusion in Low-Light Image Enhancement
- Authors: Yanyi Wu, Xu Zhang, Junkai Chen, et al.
- Venue: arXiv 2026 (preprint) — VERIFIED: yes (arXiv 2607.13925 resolves)
- Link: https://arxiv.org/abs/2607.13925
- What it takes from HVI-CIDNet: transform | loss (RGB plus lambda_hvi times the HVI loss) | dual-stream design
- What it changes or criticises: argues that the weak point of HVI-based LLIE is how the two streams are fused back together, not the colour representation. Replaces Top-K cross-attention with confidence-thresholded cross-attention, and adds a phase-guided Fourier intensity initialisation and a scale-consistency regulariser.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no (explicitly "rather than introducing yet another color representation")
- Does it report seeds or variance? no (not seen in the text I scanned)
```bibtex
@article{wu2026tcanet, title={Thresholded Cross-Attention for Reliable Intensity-Chromaticity Fusion in Low-Light Image Enhancement}, author={Wu, Yanyi and Zhang, Xu and Chen, Junkai and others}, journal={arXiv preprint arXiv:2607.13925}, year={2026}}
```

### cheng2026vcr
- Title: VCR: Variance-Driven Channel Recalibration for Robust Low-Light Enhancement
- Authors: Zhi-Xin Cheng, Fang-Wen Zhang, Xiao-Tian Yin, et al.
- Venue: IEEE TCSVT 2026 (Tier 2) — VERIFIED: yes (DOI 10.1109/TCSVT.2026.3689584; arXiv 2603.10975)
- Link: https://arxiv.org/abs/2603.10975
- What it takes from HVI-CIDNet: transform (HVI, trainable density-k) | framework
- What it changes or criticises: says HVI methods suffer channel-level inconsistency between luminance and chrominance and misaligned colour distributions. Adds variance-guided channel filtering (CAA) and a colour-distribution alignment module (CDA).
- Does it sweep / ablate the density k, or compare HVI against other color spaces? yes, HVI vs HSV only. Table V: CIDNet-HVI 24.111 vs CIDNet-HSV 21.349; VCR-HVI 24.758 vs VCR-HSV 22.104. k is described but not ablated.
- Does it report seeds or variance? no
```bibtex
@article{cheng2026vcr, title={{VCR}: Variance-Driven Channel Recalibration for Robust Low-Light Enhancement}, author={Cheng, Zhi-Xin and Zhang, Fang-Wen and Yin, Xiao-Tian and others}, journal={IEEE Transactions on Circuits and Systems for Video Technology}, year={2026}, doi={10.1109/TCSVT.2026.3689584}}
```

### wang2026haimnet
- Title: HAIMNet: A Hierarchical Adaptive Interaction Modulation Network for Low-Light Image Enhancement
- Authors: Xiaofeng Wang, Ziqian Wang, Mei-Jia Guo, et al.
- Venue: IEEE TIP 2026 (Tier 2) — VERIFIED: yes (DOI 10.1109/TIP.2026.3714857)
- Link: https://doi.org/10.1109/TIP.2026.3714857
- What it takes from HVI-CIDNet: transform (luminance/chromaticity decoupling in HVI)
- What it changes or criticises: replaces the CIDNet interaction with an inter-branch attention-modulation block and cross-branch gated affine fusion. Evaluated on 11 datasets.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? unknown. I read only the abstract and the GitHub README, and neither mentions k or colour-space ablations.
- Does it report seeds or variance? unknown (abstract only)
```bibtex
@article{wang2026haimnet, title={{HAIMNet}: A Hierarchical Adaptive Interaction Modulation Network for Low-Light Image Enhancement}, author={Wang, Xiaofeng and Wang, Ziqian and Guo, Mei-Jia and others}, journal={IEEE Transactions on Image Processing}, year={2026}, doi={10.1109/TIP.2026.3714857}}
```

### han2026clerwkv
- Title: Towards Controllable Low-Light Image Enhancement: A Continuous Multi-illumination Dataset and Efficient State Space Framework
- Authors: Hong-Ru Han, Tingrui Guo, Liming Zhang, et al.
- Venue: arXiv 2026 (preprint) — VERIFIED: yes (arXiv 2603.25296 resolves)
- Link: https://arxiv.org/abs/2603.25296
- What it takes from HVI-CIDNet: transform (HVIT used both for input decoupling and to build supervision targets)
- What it changes or criticises: reframes LLIE as controllable, conditioned on a target luminance beta, and trains RWKV-SSM on the new Light100 dataset. Uses HVI for "noise-decoupled supervision": H,V from the reference and I from the capture at target illumination. Argues this reduces reliance on GT-mean evaluation.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no (not seen in the text I scanned)
- Does it report seeds or variance? no (not seen)
```bibtex
@article{han2026clerwkv, title={Towards Controllable Low-Light Image Enhancement: A Continuous Multi-illumination Dataset and Efficient State Space Framework}, author={Han, Hong-Ru and Guo, Tingrui and Zhang, Liming and others}, journal={arXiv preprint arXiv:2603.25296}, year={2026}}
```

### wang2026interlight
- Title: InterLight: Leveraging Intrinsic Illumination Priors for Low-Light Image Enhancement
- Authors: Ziqi Wang, Xu Zhang, Laibin Chang, et al.
- Venue: arXiv 2026; arXiv comment says IJCAI 2026 (preprint — IJCAI is outside the tier list) — VERIFIED: yes for arXiv 2605.19982; IJCAI acceptance not independently verified
- Link: https://arxiv.org/abs/2605.19982
- What it takes from HVI-CIDNet: transform (HVI with the density-adaptive C_k) | loss (RGB plus mu_hvi times the HVI loss) | dual-branch layout
- What it changes or criticises: adds physics-guided sensor-level augmentation, illumination-aware prompts and a luminance-gated memory for dark-region detail.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no (not seen in the text I scanned)
- Does it report seeds or variance? no (not seen)
```bibtex
@article{wang2026interlight, title={{InterLight}: Leveraging Intrinsic Illumination Priors for Low-Light Image Enhancement}, author={Wang, Ziqi and Zhang, Xu and Chang, Laibin and Chen, Shi and Ma, Jiaqi and Zhang, Huan}, journal={arXiv preprint arXiv:2605.19982}, year={2026}}
```

### shi2025tpcnet
- Title: TPCNet: Triple Physical Constraints for Low-light Image Enhancement
- Authors: Jing-Yi Shi, Ming-Fei Li, Ling-An Wu
- Venue: arXiv 2025 (preprint) — VERIFIED: yes (arXiv 2511.22052 resolves)
- Link: https://arxiv.org/abs/2511.22052
- What it takes from HVI-CIDNet: transform (as one option) | IEL module | loss design ("inspired by" CIDNet) | baseline
- What it changes or criticises: Kubelka-Munk-based physical constraints in feature space. Says HVI-CIDNet recovers colour well but blurs details.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? yes. Same TPCNet network on LOLv2-Real: HVI 24.641 / 0.881, LAB 24.588 / 0.873, YCbCr 24.978 / 0.882 (YCbCr best). Single run. No sRGB arm. k is not swept.
- Does it report seeds or variance? no
```bibtex
@article{shi2025tpcnet, title={{TPCNet}: Triple Physical Constraints for Low-light Image Enhancement}, author={Shi, Jing-Yi and Li, Ming-Fei and Wu, Ling-An}, journal={arXiv preprint arXiv:2511.22052}, year={2025}}
```

### cheng2026lhsi
- Title: Perception-Inspired Color Space Design for Photo White Balance Editing
- Authors: Yang Cheng, Ziteng Cui, Shenghan Su, et al.
- Venue: WACV 2026 (Tier 2) — VERIFIED: yes (DOI 10.1109/WACV61042.2026.00365; arXiv 2512.09383)
- Link: https://arxiv.org/abs/2512.09383
- What it takes from HVI-CIDNet: transform idea (HVI-style Cartesian r·sin/r·cos encoding of the chroma plane) | HVI used as a comparison space
- What it changes or criticises: moves the idea to white-balance editing with a learnable HSI space (learnable luminance axis plus piecewise-linear learnable mappings).
- Does it sweep / ablate the density k, or compare HVI against other color spaces? yes, colour spaces. Same U-Net compared across CIELAB, HSV, HVI and LHSI. Set1-Test MSE: CIELAB 118.80, HSV 113.91, HVI 101.79, LHSI 71.54 (HVI roughly equals HSV on Set2 and Cube+). No sRGB arm. No k sweep.
- Does it report seeds or variance? no
```bibtex
@inproceedings{cheng2026lhsi, title={Perception-Inspired Color Space Design for Photo White Balance Editing}, author={Cheng, Yang and Cui, Ziteng and Su, Shenghan and Gu, Lin and Zhang, Zenghui}, booktitle={Proceedings of the IEEE/CVF Winter Conference on Applications of Computer Vision (WACV)}, year={2026}}
```

### li2026pal
- Title: On the Global Photometric Alignment for Low-Level Vision
- Authors: Mingjia Li, Tian-Le Du, Hainuo Wang, et al.
- Venue: arXiv 2026 (preprint) — VERIFIED: yes (arXiv 2604.08172 resolves)
- Link: https://arxiv.org/abs/2604.08172
- What it takes from HVI-CIDNet: architecture (CIDNet trained as one of 16 backbones, and the backbone for all ablations)
- What it changes or criticises: argues that per-pair photometric inconsistency in paired LLIE data dominates the pixel-loss gradients. Proposes a closed-form affine photometric alignment loss (PAL). With CIDNet: LOL-v1 23.97 → 24.13, LOLv2-Real 23.19 → 23.95, LOLv2-Syn 25.44 → 25.84 dB.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no (ablates PAL's alpha and epsilon on CIDNet)
- Does it report seeds or variance? no
```bibtex
@article{li2026pal, title={On the Global Photometric Alignment for Low-Level Vision}, author={Li, Mingjia and Du, Tian-Le and Wang, Hainuo and others}, journal={arXiv preprint arXiv:2604.08172}, year={2026}}
```

### pilligua2025mill
- Title: Evaluating Low-Light Image Enhancement Across Multiple Intensity Levels
- Authors: Maria Pilligua, David Serrano-Lozano, Pai Peng, et al.
- Venue: arXiv 2025 (preprint) — VERIFIED: yes (arXiv 2511.15496 resolves)
- Link: https://arxiv.org/abs/2511.15496
- What it takes from HVI-CIDNet: baseline only (retrained with the official code on the new MILL dataset)
- What it changes or criticises: CIDNet is brittle when input brightness moves off the training distribution. When LOL-v1 inputs are blended with GT, PSNR_L falls 26.381 → 17.721 at 20% and → 14.115 at 50%, and dE76 rises 10.59 → 16.98 → 24.81. On MILL-s it trails Retinexformer at every intensity level. The authors attribute this to CIDNet's specialised colour transform and losses.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no
- Does it report seeds or variance? no
```bibtex
@article{pilligua2025mill, title={Evaluating Low-Light Image Enhancement Across Multiple Intensity Levels}, author={Pilligua, Maria and Serrano-Lozano, David and Peng, Pai and others}, journal={arXiv preprint arXiv:2511.15496}, year={2025}}
```

### brateanu2026multinex
- Title: Multinex: Lightweight Low-light Image Enhancement via Multi-prior Retinex
- Authors: Alexandru Brateanu, Tingting Mu, Cosmin Ancuti, et al.
- Venue: arXiv 2026 (preprint) — VERIFIED: yes (arXiv 2604.10359 resolves)
- Link: https://arxiv.org/abs/2604.10359
- What it takes from HVI-CIDNet: baseline only (CIDNet as the "mid-sized" reference)
- What it changes or criticises: says HVI's learnable mappings are "highly data-dependent and can be unstable during training and inference", and that relying on a single colour space (RGB, YUV or HVI) wastes complementary cues. Fuses priors from several analytic representations in a 45K-parameter or 0.7K-parameter model.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no (multi-representation fusion, but no controlled HVI-vs-X arm on the same network was seen)
- Does it report seeds or variance? no
```bibtex
@article{brateanu2026multinex, title={Multinex: Lightweight Low-light Image Enhancement via Multi-prior Retinex}, author={Brateanu, Alexandru and Mu, Tingting and Ancuti, Cosmin and others}, journal={arXiv preprint arXiv:2604.10359}, year={2026}}
```

### du2026atp
- Title: Anchor then Polish for Low-light Enhancement
- Authors: Tian-Le Du, Mingjia Li, Hainuo Wang, et al.
- Venue: arXiv 2026 (preprint) — VERIFIED: yes (arXiv 2603.15472 resolves)
- Link: https://arxiv.org/abs/2603.15472
- What it takes from HVI-CIDNet: baseline only
- What it changes or criticises: reports "significant luminance deviations" for CIDNet. Argues that global luminance adjustment is essentially linear, so it anchors it with a 12-DoF projection matrix before local polishing.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no
- Does it report seeds or variance? no
```bibtex
@article{du2026atp, title={Anchor then Polish for Low-light Enhancement}, author={Du, Tian-Le and Li, Mingjia and Wang, Hainuo and others}, journal={arXiv preprint arXiv:2603.15472}, year={2026}}
```

### lin2025jarvisir
- Title: JarvisIR: Elevating Autonomous Driving Perception with Intelligent Image Restoration
- Authors: Yunlong Lin, Zixu Lin, Haoyu Chen, et al.
- Venue: CVPR 2025 (Tier 1) — VERIFIED: yes (DOI 10.1109/CVPR52734.2025.02084; arXiv 2504.04158)
- Link: https://arxiv.org/abs/2504.04158
- What it takes from HVI-CIDNet: checkpoint (HVI-CIDNet is one of the low-light "expert tools" a VLM agent can call)
- What it changes or criticises: nothing in CIDNet itself. It shows HVI-CIDNet being reused as an off-the-shelf module.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no
- Does it report seeds or variance? no
```bibtex
@inproceedings{lin2025jarvisir, title={{JarvisIR}: Elevating Autonomous Driving Perception with Intelligent Image Restoration}, author={Lin, Yunlong and Lin, Zixu and Chen, Haoyu and others}, booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2025}}
```

### verma2025qcidnet
- Title: Q-CIDNet: Perceptual Quality Aware Color and Intensity Decoupling Network for Video Quality Enhancement
- Authors: Ajeet Kumar Verma, S. Tripathi, Vinit Jakhetiya, et al.
- Venue: CVPR Workshops (NTIRE) 2025 (preprint — workshop) — VERIFIED: yes (DOI 10.1109/CVPRW67362.2025.00117)
- Link: https://doi.org/10.1109/CVPRW67362.2025.00117
- What it takes from HVI-CIDNet: architecture | checkpoint ("initialized with pretrained weights")
- What it changes or criticises: applies CIDNet to video-conferencing enhancement (NTIRE 2025 VQE track) and adds a perceptual / video-quality-metric loss.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no (abstract level; the CVF page returned 403 and the full text was not read)
- Does it report seeds or variance? no (abstract level)
```bibtex
@inproceedings{verma2025qcidnet, title={{Q-CIDNet}: Perceptual Quality Aware Color and Intensity Decoupling Network for Video Quality Enhancement}, author={Verma, Ajeet Kumar and Tripathi, S. and Jakhetiya, Vinit and others}, booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW)}, year={2025}}
```

### guan2025cstnet
- Title: Rethinking Nighttime Image Deraining via Learnable Color Space Transformation
- Authors: Qiyuan Guan, Xiang Chen, Guiyue Jin, et al.
- Venue: NeurIPS 2025 (Tier 1) — VERIFIED: yes (neurips.cc/virtual/2025/poster/118470; OpenReview PDF; arXiv 2510.17440)
- Link: https://arxiv.org/abs/2510.17440
- What it takes from HVI-CIDNet: baseline only (cites HVI among decoupled colour spaces)
- What it changes or criticises: a learnable YCbCr-like colour-space converter for nighttime deraining. This is the closest Tier-1 "learnable colour space" competitor idea, but it does not use HVI.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? no (HVI is only mentioned, not tested)
- Does it report seeds or variance? no
```bibtex
@inproceedings{guan2025cstnet, title={Rethinking Nighttime Image Deraining via Learnable Color Space Transformation}, author={Guan, Qiyuan and Chen, Xiang and Jin, Guiyue and Jin, Jiyu and Fan, Shumin and Song, Tianyu and Pan, Jinshan}, booktitle={Advances in Neural Information Processing Systems (NeurIPS)}, year={2025}}
```

### wu2026catformer
- Title: Device-Independent Low-Light Image Enhancement via Learnable Von Kries Chromatic Adaptation Transform
- Authors: Kun-Yang Wu, Jun Lin, Zheng-Peng Li, et al.
- Venue: IEEE TCSVT 2026 (Tier 2) — VERIFIED: yes (DOI 10.1109/TCSVT.2026.3700071)
- Link: https://doi.org/10.1109/TCSVT.2026.3700071
- What it takes from HVI-CIDNet: baseline only (cites HVI; I did not read the comparison tables)
- What it changes or criticises: argues that sRGB, and colour spaces decoupled from it, give "unanchored" mappings. Uses a learnable per-pixel von Kries CAT to a standard white point, then decoupled restoration in CIELAB. This is an alternative position to HVI.
- Does it sweep / ablate the density k, or compare HVI against other color spaces? unknown (abstract only)
- Does it report seeds or variance? unknown (abstract only)
```bibtex
@article{wu2026catformer, title={Device-Independent Low-Light Image Enhancement via Learnable Von Kries Chromatic Adaptation Transform}, author={Wu, Kun-Yang and Lin, Jun and Li, Zheng-Peng and others}, journal={IEEE Transactions on Circuits and Systems for Video Technology}, year={2026}, doi={10.1109/TCSVT.2026.3700071}}
```

---

## Out-of-filter HVI derivatives (seen in S2 citation lists; venues outside Tier 1/2; not checked in detail)
Information Fusion 2026 "SNR-Aware framework ... in HVI space" (10.1016/j.inffus.2026.104350); HGD-Net, Information Sciences 2026 (10.1016/j.ins.2026.123666); ACIDNet, Pattern Recognition 2026 (10.1016/j.patcog.2026.114139); HReMatch, ESWA 2026 (HVI enhancement for feature matching); HIDENet, SIVP 2026; VMamba-LLIE, Multimedia Systems 2026; Mamba-transformer in HVI space, Multimedia Systems 2025; HVD-Net, Sci. Rep. 2026 (HSV with continuous hue); HVI-space low-light video enhancement with fuzzy sets, Sci. Rep. 2026; CAGNet (HVI dual-path underwater, CAIT 2025); SG-CIDNet, HVI-FENet, HVI-FFNet, AIE-Net, HVI-CIDNet-industrial (SPIE/IEEE conference papers); DLFE-Net (PMC). Also IJCAI 2026 SPACE (10.24963/ijcai.2026/235), which cites HVI; its use of HVI was not checked.

---

## Reproducibility reports (LOL-v1 unless noted)
- **Paper number carried forward:** HVI-CIDNet LOL-v1 = 28.201 dB / 0.889 SSIM. HVI-CIDNet+ (Table I) states it was evaluated *with GT-mean*. RHVI-FDD and VCR reuse this number as their baseline without retraining.
- **FusionNet (same authors' group, CVPRW 2025):** lists CIDNet on LOL-v1 at 23.50 dB / 0.870 SSIM / 0.105 LPIPS, about 4.7 dB below the GT-mean figure. The protocol is not stated but is consistent with no GT-mean.
- **PAL (arXiv 2604.08172):** trains CIDNet "with original training configurations" and gets 23.97 / 0.849 (LOL-v1), 23.19 / 0.857 (LOLv2-Real) and 25.44 / 0.935 (LOLv2-Syn).
- **GitHub issue #66 ("LOLv1 PSNR/SSIM variance from paper metrics"):** a user retrained on an RTX 4090 with PyTorch 2.2.2 and the default hyperparameters and got **23.5881 / 0.8539**. Closed, with no visible maintainer explanation.
- **GitHub #50:** reports someone else reaching PSNR 24.7 on LOL-v1 and asks which hyperparameters were changed. No visible reply.
- **GitHub #140** (Nov 2025, closed): cannot reach the paper's LOL-v1 w_perc numbers; no numbers posted. **#160** (Jun 2026, closed Jul 2026): "why can't I reproduce your LOL-v1 results?"; no numbers or visible reply.
- **GitHub #162** (Aug 2026, open), LOLv2-Real: reproduced 23.89 vs paper 24.11 (best-normal) / 23.90 (best-PSNR). **#163** (Aug 2026, open): asks how checkpoints were selected, given LOLv2-Real has no separate validation split. **#122** asks whether the Table 1 LOLv2-Real metrics came from the same weights. **#132 / #133**: LOLv2-Syn reproduction problems.
- **GitHub #80:** changing the inference-time `alpha_i` (0.5 vs 0.1) with the HF LOLv1-wperc checkpoint gave identical outputs. No reply.
- **NTIRE 2026 LLIE report:** zero-shot CIDNet scored 13.85 dB on the challenge data, below gamma correction (14.91 dB).
- **MILL (arXiv 2511.15496):** CIDNet retrained with the official code. LOL-v1 luminance PSNR falls from 26.38 to 17.72 when inputs are blended 20% toward GT.
- **BC-IHV:** HVI under their SA-RF network reaches 22.54 dB on LOLv2-Real (not a CIDNet reproduction).

## What nobody has done yet
- None of the papers I found compares HVI against sRGB, HSV and YCbCr on the *same CIDNet network across multiple seeds*. Every colour-space ablation is a single run: HVI-CIDNet+ Table V, VCR Table V (HVI vs HSV only), TPCNet (HVI/LAB/YCbCr), RHVI-FDD (HSV/HVI/RHVI), LHSI (WB task) and BC-IHV (intensity law only).
- The one same-network test that included YCbCr (TPCNet, LOLv2-Real) found YCbCr ahead of HVI (24.98 vs 24.64 dB). The gap is within plausible seed noise, and nobody has checked it inside CIDNet.
- I found no isolated sweep of the density k. HVI-CIDNet+ only switches C_k on or off. FusionNet's "k" sweep appears to be over fusion weights. BC-IHV and RHVI-FDD change the intensity channel and leave k fixed.
- Nobody has separated the roughly 4-5 dB LOL-v1 gap into its likely causes: GT-mean evaluation (28.2) vs no GT-mean (23.5-24.0 in FusionNet, PAL and issue #66), checkpoint selection on the test set (#163), and seed variance.
- The claim that HVI generalises worse because k is learned (FusionNet, Multinex) and CIDNet's brittleness to input brightness (MILL, NTIRE 2026 zero-shot) have not been tested with a fixed-k vs learned-k vs other-colour-space comparison.
