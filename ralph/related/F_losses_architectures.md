# Literature Scout: Loss Functions & Two-Branch/Cross-Attention Architectures for HVI-CIDNet Provenance

## (A) Loss functions for image restoration/enhancement

### johnson2016perceptual
- Title: Perceptual Losses for Real-Time Style Transfer and Super-Resolution
- Authors: Justin Johnson, Alexandre Alahi, Li Fei-Fei
- Venue: ECCV 2016 (Tier 1) — VERIFIED: yes (openaccess/Springer DOI 10.1007/978-3-319-46475-6_43; arXiv 1603.08155)
- Link: https://arxiv.org/abs/1603.08155
- Component: perceptual
- What it establishes: Introduces feature-space ("perceptual") reconstruction and style losses computed on pretrained VGG activations for feed-forward image transformation networks.
- Relevance to HVI-CIDNet: Direct provenance for the 0.01·VGG19 perceptual loss term used in both RGB and HVI branches.
```bibtex
@inproceedings{johnson2016perceptual, title={Perceptual losses for real-time style transfer and super-resolution}, author={Johnson, Justin and Alahi, Alexandre and Fei-Fei, Li}, booktitle={European Conference on Computer Vision (ECCV)}, year={2016}}
```

### ledig2017srgan
- Title: Photo-Realistic Single Image Super-Resolution Using a Generative Adversarial Network
- Authors: Christian Ledig, Lucas Theis, Ferenc Huszár, et al.
- Venue: CVPR 2017 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content_cvpr_2017)
- Link: https://openaccess.thecvf.com/content_cvpr_2017/html/Ledig_Photo-Realistic_Single_Image_CVPR_2017_paper.html
- Component: perceptual
- What it establishes: Popularized VGG-feature-space perceptual/content loss combined with adversarial loss as the standard training recipe for photo-realistic restoration networks.
- Relevance to HVI-CIDNet: Second canonical source (alongside Johnson et al.) for the VGG19 perceptual loss term; widely cited as the origin of "perceptual loss" in restoration/enhancement pipelines.
```bibtex
@inproceedings{ledig2017srgan, title={Photo-realistic single image super-resolution using a generative adversarial network}, author={Ledig, Christian and Theis, Lucas and Husz{\'a}r, Ferenc and Caballero, Jose and Cunningham, Andrew and Acosta, Alejandro and Aitken, Andrew and Tejani, Alykhan and Totz, Johannes and Wang, Zehan and Shi, Wenzhe}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2017}}
```

### zhao2017loss
- Title: Loss Functions for Image Restoration with Neural Networks
- Authors: Hang Zhao, Orazio Gallo, Iuri Frosio, Jan Kautz
- Venue: IEEE Transactions on Computational Imaging (TCI), vol. 3, 2017 (Tier 2) — VERIFIED: yes (dblp.org/db/journals/tci/tci3.html; IEEE Xplore 7797130)
- Link: https://arxiv.org/abs/1511.08861
- Component: SSIM
- What it establishes: Systematically compares L1/L2/SSIM/MS-SSIM and mixed losses for restoration networks; proposes an MS-SSIM+L1 mixed loss and shows loss-weight/combination choice materially changes perceptual quality — the canonical loss-weight-sensitivity study for restoration.
- Relevance to HVI-CIDNet: Direct provenance for using SSIM as a training loss (the 0.5·SSIM term) and the reference point for any loss-weight ablation the thesis performs.
```bibtex
@article{zhao2017loss, title={Loss functions for image restoration with neural networks}, author={Zhao, Hang and Gallo, Orazio and Frosio, Iuri and Kautz, Jan}, journal={IEEE Transactions on Computational Imaging}, volume={3}, number={1}, pages={47--57}, year={2017}}
```

### lai2017lapsrn
- Title: Deep Laplacian Pyramid Networks for Fast and Accurate Super-Resolution
- Authors: Wei-Sheng Lai, Jia-Bin Huang, Narendra Ahuja, Ming-Hsuan Yang
- Venue: CVPR 2017 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content_cvpr_2017)
- Link: https://openaccess.thecvf.com/content_cvpr_2017/html/Lai_Deep_Laplacian_Pyramid_CVPR_2017_paper.html
- Component: edge
- What it establishes: Introduces a Laplacian-pyramid framework that progressively predicts high-frequency sub-band residuals, making the Laplacian pyramid a standard structural/edge representation for restoration losses and architectures.
- Relevance to HVI-CIDNet: Canonical precedent for the Laplacian-pyramid formulation underlying the 50·edge (Laplacian-pyramid MSE) loss term.
```bibtex
@inproceedings{lai2017lapsrn, title={Deep laplacian pyramid networks for fast and accurate super-resolution}, author={Lai, Wei-Sheng and Huang, Jia-Bin and Ahuja, Narendra and Yang, Ming-Hsuan}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2017}}
```

### zamir2021mprnet
- Title: Multi-Stage Progressive Image Restoration
- Authors: Syed Waqas Zamir, Aditya Arora, Salman Khan, et al.
- Venue: CVPR 2021 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content/CVPR2021)
- Link: https://openaccess.thecvf.com/content/CVPR2021/papers/Zamir_Multi-Stage_Progressive_Image_Restoration_CVPR_2021_paper.pdf
- Component: edge
- What it establishes: Trains a multi-stage restoration network with an explicit Charbonnier loss plus an "edge loss" L_edge = √(‖Δ(X)-Δ(Y)‖²+ε²) where Δ is the Laplacian operator (λ_edge = 0.05), directly analogous in form to a Laplacian-based edge/gradient loss term.
- Relevance to HVI-CIDNet: A directly citable modern (CVPR-tier) precedent for a Laplacian-operator "edge loss" summed with a pixel-fidelity loss, matching the structure (though not the pyramid form) of HVI-CIDNet's edge term.
```bibtex
@inproceedings{zamir2021mprnet, title={Multi-stage progressive image restoration}, author={Zamir, Syed Waqas and Arora, Aditya and Khan, Salman and Hayat, Munawar and Khan, Fahad Shahbaz and Yang, Ming-Hsuan and Shao, Ling}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2021}}
```

### guo2020zerodce
- Title: Zero-Reference Deep Curve Estimation for Low-Light Image Enhancement
- Authors: Chunle Guo, Chongyi Li, Jichang Guo, et al.
- Venue: CVPR 2020 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content_CVPR_2020)
- Link: https://openaccess.thecvf.com/content_CVPR_2020/html/Guo_Zero-Reference_Deep_Curve_Estimation_for_Low-Light_Image_Enhancement_CVPR_2020_paper.html
- Component: color
- What it establishes: Introduces a non-reference color constancy loss that enforces Gray-World-style inter-channel balance to prevent color casts during curve-based light adjustment.
- Relevance to HVI-CIDNet: The canonical LLIE-specific color loss; relevant precedent/contrast for any color-fidelity term considered in an ablation of HVI-CIDNet's loss (which instead relies on dual-space L1/SSIM/edge/perceptual terms for color fidelity).
```bibtex
@inproceedings{guo2020zerodce, title={Zero-reference deep curve estimation for low-light image enhancement}, author={Guo, Chunle and Li, Chongyi and Guo, Jichang and Loy, Chen Change and Hou, Junhui and Kwong, Sam and Cong, Runmin}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2020}}
```

### afifi2021exposure
- Title: Learning Multi-Scale Photo Exposure Correction
- Authors: Mahmoud Afifi, Konstantinos G. Derpanis, Björn Ommer, Michael S. Brown
- Venue: CVPR 2021 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content/CVPR2021)
- Link: https://openaccess.thecvf.com/content/CVPR2021/papers/Afifi_Learning_Multi-Scale_Photo_Exposure_Correction_CVPR_2021_paper.pdf
- Component: color
- What it establishes: Coarse-to-fine exposure-correction network trained with a combination of reconstruction loss, a Laplacian-pyramid loss, and adversarial loss, splitting the objective across color and detail sub-problems (paralleling color/exposure losses used in HDR/exposure work).
- Relevance to HVI-CIDNet: Precedent for combining a Laplacian-pyramid loss with color/exposure-sensitive supervision in an exposure/illumination-correction setting closely related to LLIE.
```bibtex
@inproceedings{afifi2021exposure, title={Learning multi-scale photo exposure correction}, author={Afifi, Mahmoud and Derpanis, Konstantinos G and Ommer, Bj{\"o}rn and Brown, Michael S}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2021}}
```

### zhang2018lpips
- Title: The Unreasonable Effectiveness of Deep Features as a Perceptual Metric
- Authors: Richard Zhang, Phillip Isola, Alexei A. Efros, et al.
- Venue: CVPR 2018 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content_cvpr_2018)
- Link: https://arxiv.org/abs/1801.03924
- Component: LPIPS-loss
- What it establishes: Introduces LPIPS, a learned deep-feature perceptual similarity metric calibrated on human judgments, shown to correlate with perception far better than PSNR/SSIM.
- Relevance to HVI-CIDNet: Foundational citation whenever LPIPS is used either as an evaluation metric or (per Jo et al. below) as a differentiable training loss, relevant to any perceptual-loss ablation alternative to the VGG19 term.
```bibtex
@inproceedings{zhang2018lpips, title={The unreasonable effectiveness of deep features as a perceptual metric}, author={Zhang, Richard and Isola, Phillip and Efros, Alexei A and Shechtman, Eli and Wang, Oliver}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2018}}
```

### jo2020investigating
- Title: Investigating Loss Functions for Extreme Super-Resolution
- Authors: Younghyun Jo, Sejong Yang, Seon Joo Kim
- Venue: CVPR Workshops (NTIRE) 2020 (Tier 2, workshop) — VERIFIED: yes (openaccess.thecvf.com/content_CVPRW_2020; IEEE Xplore 9150941)
- Link: https://openaccess.thecvf.com/content_CVPRW_2020/papers/w31/Jo_Investigating_Loss_Functions_for_Extreme_Super-Resolution_CVPRW_2020_paper.pdf
- Component: LPIPS-loss
- What it establishes: Empirically compares VGG-perceptual-loss GANs against an LPIPS-loss GAN for x16 perceptual super-resolution, showing LPIPS-as-training-loss gives more consistent details than VGG perceptual loss alone; also studies sensitivity to loss weighting.
- Relevance to HVI-CIDNet: Directly citable precedent for using LPIPS (rather than/alongside VGG perceptual loss) as a differentiable training loss, and for empirical loss-weight sensitivity in a restoration setting — useful for the thesis's loss-ablation design.
```bibtex
@inproceedings{jo2020investigating, title={Investigating loss functions for extreme super-resolution}, author={Jo, Younghyun and Yang, Sejong and Kim, Seon Joo}, booktitle={IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW, NTIRE)}, year={2020}}
```

### peng2023ushape
- Title: U-Shape Transformer for Underwater Image Enhancement
- Authors: Lintao Peng, Chunli Zhu, Liheng Bian
- Venue: IEEE Transactions on Image Processing (TIP) 2023 (Tier 2) — VERIFIED: yes (DOI 10.1109/TIP.2023.3276332; arXiv 2111.11843)
- Link: https://arxiv.org/abs/2111.11843
- Component: dual-space
- What it establishes: Trains a U-shaped Transformer restoration network with a multi-color-space loss that supervises the output jointly in RGB and in Lab/LCH space to better constrain hue/saturation/lightness, in addition to a perceptual loss.
- Relevance to HVI-CIDNet: The clearest Tier-2 precedent found for HVI-CIDNet's core loss design choice of summing a loss over RGB plus a second (photometric) color space — see "Precedents" section below.
```bibtex
@article{peng2023ushape, title={U-shape transformer for underwater image enhancement}, author={Peng, Lintao and Zhu, Chunli and Bian, Liheng}, journal={IEEE Transactions on Image Processing}, volume={32}, pages={3066--3079}, year={2023}}
```

## (B) Two-branch / luminance–chrominance architectures and cross-attention blocks

### zamir2022restormer
- Title: Restormer: Efficient Transformer for High-Resolution Image Restoration
- Authors: Syed Waqas Zamir, Aditya Arora, Salman Khan, et al.
- Venue: CVPR 2022 (Oral) (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content/CVPR2022)
- Link: https://openaccess.thecvf.com/content/CVPR2022/papers/Zamir_Restormer_Efficient_Transformer_for_High-Resolution_Image_Restoration_CVPR_2022_paper.pdf
- Component: cross-attention
- What it establishes: Proposes Multi-Dconv-head Transposed Attention (MDTA, channel-wise rather than spatial self-attention) and a Gated-Dconv Feed-Forward Network (GDFN) inside a U-shaped hierarchical encoder-decoder for high-resolution restoration.
- Relevance to HVI-CIDNet: Direct architectural ancestor — HVI-CIDNet's Lighten Cross-Attention blocks are explicitly derived from Restormer's transposed attention + gated feed-forward design, adapted to cross-branch (intensity/chroma) rather than self-attention.
```bibtex
@inproceedings{zamir2022restormer, title={Restormer: Efficient transformer for high-resolution image restoration}, author={Zamir, Syed Waqas and Arora, Aditya and Khan, Salman and Hayat, Munawar and Khan, Fahad Shahbaz and Yang, Ming-Hsuan}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2022}}
```

### wang2022uformer
- Title: Uformer: A General U-Shaped Transformer for Image Restoration
- Authors: Zhendong Wang, Xiaodong Cun, Jianmin Bao, et al.
- Venue: CVPR 2022 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content/CVPR2022)
- Link: https://openaccess.thecvf.com/content/CVPR2022/papers/Wang_Uformer_A_General_U-Shaped_Transformer_for_Image_Restoration_CVPR_2022_paper.pdf
- Component: backbone
- What it establishes: Hierarchical U-shaped encoder-decoder built from window-based Locally-enhanced Window (LeWin) Transformer blocks with a depth-wise-conv feed-forward network.
- Relevance to HVI-CIDNet: Closest competing U-shaped Transformer restoration backbone; useful contrast point for HVI-CIDNet's two-U-branch design and its choice of channel (Restormer-style) vs. window (Uformer-style) attention.
```bibtex
@inproceedings{wang2022uformer, title={Uformer: A general u-shaped transformer for image restoration}, author={Wang, Zhendong and Cun, Xiaodong and Bao, Jianmin and Zhou, Wengang and Liu, Jianzhuang and Li, Houqiang}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2022}}
```

### chen2022nafnet
- Title: Simple Baselines for Image Restoration
- Authors: Liangyu Chen, Xiaojie Chu, Xiangyu Zhang, Jian Sun
- Venue: ECCV 2022 (Tier 1) — VERIFIED: yes (link.springer.com/chapter/10.1007/978-3-031-20071-7_2; ecva.net)
- Link: https://arxiv.org/abs/2204.04676
- Component: backbone
- What it establishes: Nonlinear-Activation-Free Network (NAFNet) shows a minimalist U-shaped CNN backbone (no self-attention, gated linear units instead) matches/exceeds Transformer restoration baselines.
- Relevance to HVI-CIDNet: Alternative simple U-shaped restoration baseline; relevant as an efficiency contrast to HVI-CIDNet's Restormer-derived cross-attention blocks in any ablation of backbone complexity.
```bibtex
@inproceedings{chen2022nafnet, title={Simple baselines for image restoration}, author={Chen, Liangyu and Chu, Xiaojie and Zhang, Xiangyu and Sun, Jian}, booktitle={European Conference on Computer Vision (ECCV)}, year={2022}}
```

### liang2021swinir
- Title: SwinIR: Image Restoration Using Swin Transformer
- Authors: Jingyun Liang, Jiezhang Cao, Guolei Sun, et al.
- Venue: ICCV Workshops (AIM) 2021 (Tier 1, workshop) — VERIFIED: yes (openaccess.thecvf.com/content/ICCV2021W/AIM)
- Link: https://arxiv.org/abs/2108.10257
- Component: backbone
- What it establishes: Residual Swin Transformer Blocks (RSTB) for shallow/deep feature extraction plus reconstruction, a strong Swin-based restoration baseline across SR/denoising/JPEG-artifact removal.
- Relevance to HVI-CIDNet: Widely cited Transformer restoration backbone predating Restormer/Uformer/NAFNet; establishes the "hierarchical windowed-Transformer for restoration" lineage HVI-CIDNet's cross-attention blocks build on.
```bibtex
@inproceedings{liang2021swinir, title={SwinIR: Image restoration using Swin transformer}, author={Liang, Jingyun and Cao, Jiezhang and Sun, Guolei and Zhang, Kai and Van Gool, Luc and Timofte, Radu}, booktitle={IEEE/CVF International Conference on Computer Vision Workshops (ICCVW)}, year={2021}}
```

### zamir2020mirnet
- Title: Learning Enriched Features for Real Image Restoration and Enhancement
- Authors: Syed Waqas Zamir, Aditya Arora, Salman Khan, et al.
- Venue: ECCV 2020 (Tier 1) — VERIFIED: yes (ecva.net/papers/eccv_2020; arXiv 2003.06792)
- Link: https://arxiv.org/abs/2003.06792
- Component: two-branch
- What it establishes: MIRNet's multi-scale residual block keeps a high-resolution "main branch" running in parallel with complementary lower-resolution branches, fused via selective kernel feature exchange — a parallel-branch (not luma/chroma but multi-scale) enhancement architecture.
- Relevance to HVI-CIDNet: Precedent for a multi-branch (parallel, information-exchanging) restoration/enhancement architecture predating the two-branch intensity/chroma split, useful for framing the design space HVI-CIDNet's two U-branches occupy.
```bibtex
@inproceedings{zamir2020mirnet, title={Learning enriched features for real image restoration and enhancement}, author={Zamir, Syed Waqas and Arora, Aditya and Khan, Salman and Hayat, Munawar and Khan, Fahad Shahbaz and Yang, Ming-Hsuan and Shao, Ling}, booktitle={European Conference on Computer Vision (ECCV)}, year={2020}}
```

### zhang2022dccnet
- Title: Deep Color Consistent Network for Low-Light Image Enhancement
- Authors: Zhao Zhang, Huan Zheng, Richang Hong, et al.
- Venue: CVPR 2022 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content/CVPR2022; DOI 10.1109/CVPR52688.2022.00194)
- Link: https://openaccess.thecvf.com/content/CVPR2022/papers/Zhang_Deep_Color_Consistent_Network_for_Low-Light_Image_Enhancement_CVPR_2022_paper.pdf
- Component: two-branch
- What it establishes: Decouples a low-light image into a grayscale (structure) component and a color histogram, processed by separate structure- and color-oriented pathways fused via a pyramid color embedding module.
- Relevance to HVI-CIDNet: A directly comparable two-branch decoupled-color LLIE architecture (grayscale/structure vs. color, rather than intensity vs. chroma), a natural architectural neighbor for HVI-CIDNet's intensity/chroma split.
```bibtex
@inproceedings{zhang2022dccnet, title={Deep color consistent network for low-light image enhancement}, author={Zhang, Zhao and Zheng, Huan and Hong, Richang and Xu, Mingliang and Yan, Shuicheng and Wang, Meng}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2022}}
```

### guo2022bread
- Title: Low-Light Image Enhancement via Breaking Down the Darkness
- Authors: Xiaojie Guo, Qiming Hu
- Venue: IJCV, vol. 131, 2023 (published online 2022) (Tier 1) — VERIFIED: yes (link.springer.com/article/10.1007/s11263-022-01667-9; dl.acm.org DOI 10.1007/s11263-022-01667-9)
- Link: https://arxiv.org/abs/2111.15557
- Component: two-branch
- What it establishes: Explicitly converts RGB into a luminance-chrominance representation and processes the two with a noise-suppression network on brightened luminance and a chrominance mapper guided by the enhanced luminance.
- Relevance to HVI-CIDNet: One of the closest architectural precedents in the survey — an explicit RGB→luminance/chrominance decomposition with cross-guidance between the two branches, directly analogous to HVI-CIDNet's intensity/chroma U-branches.
```bibtex
@article{guo2022bread, title={Low-light image enhancement via breaking down the darkness}, author={Guo, Xiaojie and Hu, Qiming}, journal={International Journal of Computer Vision}, volume={131}, pages={48--66}, year={2023}}
```

### brateanu2025lytnet
- Title: LYT-Net: Lightweight YUV Transformer-based Network for Low-Light Image Enhancement
- Authors: Alexandru Brateanu, Raul Balmez, Adrian Avram, et al.
- Venue: IEEE Signal Processing Letters, vol. 32, 2025 (Tier 2*, not in the enumerated venue list but a peer-reviewed IEEE journal; included for direct architectural relevance) — VERIFIED: yes (IEEE Xplore 10972228; ADS 2025ISPL...32.2065B)
- Link: https://arxiv.org/abs/2401.15204
- Component: two-branch
- What it establishes: Splits the input in YUV space into a luminance (Y) path and a chrominance (U,V) path, each processed by dedicated lightweight blocks (Channel-Wise Denoiser, Multi-Stage Squeeze & Excite Fusion) with multi-headed self-attention fusing the two.
- Relevance to HVI-CIDNet: The most literal luma/chroma two-branch Transformer LLIE precedent found; differs from HVI-CIDNet mainly in color space (YUV vs. HVI) and in using self-attention fusion rather than Restormer-style cross-attention blocks.
```bibtex
@article{brateanu2025lytnet, title={LYT-Net: Lightweight YUV Transformer-based Network for Low-Light Image Enhancement}, author={Brateanu, Alexandru and Balmez, Raul and Avram, Adrian and Orhei, Ciprian and Ancuti, Cosmin}, journal={IEEE Signal Processing Letters}, volume={32}, pages={2065--2069}, year={2025}}
```

### wu2022uretinexnet
- Title: URetinex-Net: Retinex-Based Deep Unfolding Network for Low-Light Image Enhancement
- Authors: Wenhui Wu, Jian Weng, Pingping Zhang, et al.
- Venue: CVPR 2022 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content/CVPR2022)
- Link: https://openaccess.thecvf.com/content/CVPR2022/papers/Wu_URetinex-Net_Retinex-Based_Deep_Unfolding_Network_for_Low-Light_Image_Enhancement_CVPR_2022_paper.pdf
- Component: two-branch
- What it establishes: Unfolds a Retinex optimization into a learnable network with separate initialization/unfolding/illumination-adjustment modules that explicitly split a low-light image into reflectance and illumination layers.
- Relevance to HVI-CIDNet: The closest architecturally-grounded Retinex two-branch (reflectance/illumination) precedent; the reflectance-illumination split is the decomposition ancestor of intensity/chroma-style dual branches in LLIE.
```bibtex
@inproceedings{wu2022uretinexnet, title={URetinex-Net: Retinex-based deep unfolding network for low-light image enhancement}, author={Wu, Wenhui and Weng, Jian and Zhang, Pingping and Wang, Xu and Yang, Wenhan and Jiang, Jianmin}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2022}}
```

### cai2023retinexformer
- Title: Retinexformer: One-Stage Retinex-Based Transformer for Low-Light Image Enhancement
- Authors: Yuanhao Cai, Hao Bian, Jing Lin, et al.
- Venue: ICCV 2023 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content/ICCV2023)
- Link: https://arxiv.org/abs/2303.06705
- Component: cross-attention
- What it establishes: A one-stage Retinex framework with an Illumination-Guided Transformer whose Illumination-Guided Multi-head Self-Attention (IG-MSA) uses illumination representations to direct non-local attention across differently-lit regions, achieving linear complexity.
- Relevance to HVI-CIDNet: Closest Retinex-based Transformer precedent for illumination-conditioned attention in LLIE, a direct point of comparison for HVI-CIDNet's Lighten Cross-Attention blocks (which instead cross-attend between intensity and chroma branches rather than gating self-attention by illumination).
```bibtex
@inproceedings{cai2023retinexformer, title={Retinexformer: One-stage Retinex-based transformer for low-light image enhancement}, author={Cai, Yuanhao and Bian, Hao and Lin, Jing and Wang, Haoqian and Timofte, Radu and Zhang, Yulun}, booktitle={IEEE/CVF International Conference on Computer Vision (ICCV)}, year={2023}}
```

### xu2022snraware
- Title: SNR-Aware Low-Light Image Enhancement
- Authors: Xiaogang Xu, Ruixing Wang, Chi-Wing Fu, Jiaya Jia
- Venue: CVPR 2022 (Tier 1) — VERIFIED: yes (openaccess.thecvf.com/content/CVPR2022)
- Link: https://openaccess.thecvf.com/content/CVPR2022/papers/Xu_SNR-Aware_Low-Light_Image_Enhancement_CVPR_2022_paper.pdf
- Component: cross-attention
- What it establishes: Fuses a CNN branch and an SNR-guided Transformer branch via spatially-varying, signal-to-noise-ratio-conditioned attention, using long-range attention only where SNR is low.
- Relevance to HVI-CIDNet: A further precedent for cross-branch, condition-guided attention fusion (two complementary processing branches combined by a learned attention gate) in LLIE, structurally adjacent to the Lighten Cross-Attention mechanism.
```bibtex
@inproceedings{xu2022snraware, title={SNR-aware low-light image enhancement}, author={Xu, Xiaogang and Wang, Ruixing and Fu, Chi-Wing and Jia, Jiaya}, booktitle={IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, year={2022}}
```

## Precedents for a loss in two color spaces at once

Direct precedents for summing a full training loss (or a substantial loss bundle) computed once in RGB and again in a second color space are scarce at top-tier venues; the clearest ones found are:

- **peng2023ushape** (U-Shape Transformer for Underwater Image Enhancement, IEEE TIP 2023, Tier 2) — trains with a multi-color-space loss that supervises the network output jointly in RGB and in Lab/LCH space (to better constrain lightness, hue and saturation), in addition to a perceptual term. This is the closest verified precedent for HVI-CIDNet's practice of duplicating L1+SSIM+edge+perceptual across RGB and a second (HVI) color space.
- **guo2022bread** and **brateanu2025lytnet** decompose the *architecture* (not just the loss) into luminance/chrominance-equivalent representations and supervise each branch's own output — a related but distinct precedent (per-branch supervision in a second color space, rather than a duplicated whole-image loss in two spaces).
- No Tier-1 CVPR/ICCV/ECCV/NeurIPS/ICLR/ICML paper was found that explicitly frames its objective as "the same composite loss computed once in RGB and once in another color space and summed," which appears to be a specific and relatively novel formulation in HVI-CIDNet relative to this literature slice. (Zhao et al. 2017's loss-function study and the exposure-correction/underwater precedents above are the nearest supporting evidence, but none matches the exact dual-space-duplication pattern at a Tier-1 venue.)
