# E. Evaluation methodology and reproducibility (LLIE / image restoration)

Tier convention used here: Tier 1 = CVPR/ICCV/ECCV/NeurIPS/ICML, TPAMI/IJCV/JMLR; Tier 2 = TIP/TNNLS/BMVC/WACV/MLSys/ACL/EMNLP/CVPR-ECCV workshops; other = letters/magazines/colour-science journals/arXiv-only.
Note: dblp.org blocked automated access during this search, so second-source verification used CVF open access, IEEE/Springer/Wiley DOI pages, PMLR, ACL Anthology, JMLR, MLSys proceedings and PubMed.

## 1. Surveys and benchmarks of LLIE

### li2022llie
- Title: Low-Light Image and Video Enhancement Using Deep Learning: A Survey
- Authors: Chongyi Li, Chunle Guo, Linghao Han, et al.
- Venue: IEEE TPAMI 2022 (vol. 44, no. 12, pp. 9396-9416; online 2021) (Tier 1) — VERIFIED: yes (PubMed 34752382; IEEE CSDL)
- Link: https://arxiv.org/abs/2104.10729
- What it establishes: Standard taxonomy of deep LLIE; introduces the LLIV-Phone benchmark and a unified online evaluation platform; notes the weakness of full-reference metrics and the lack of a standard protocol.
- How our thesis uses it: Framing citation for LLIE as a field and for the claim that evaluation practice is not standardised.
```bibtex
@article{li2022llie, title={Low-Light Image and Video Enhancement Using Deep Learning: A Survey}, author={Li, Chongyi and Guo, Chunle and Han, Linghao and Jiang, Jun and Cheng, Ming-Ming and Gu, Jinwei and Loy, Chen Change}, journal={IEEE Transactions on Pattern Analysis and Machine Intelligence}, volume={44}, number={12}, pages={9396--9416}, year={2022}}
```

### liu2021benchmarking
- Title: Benchmarking Low-Light Image Enhancement and Beyond
- Authors: Jiaying Liu, Dejia Xu, Wenhan Yang, et al.
- Venue: IJCV 2021 (vol. 129, pp. 1153-1184) (Tier 1) — VERIFIED: yes (Springer DOI 10.1007/s11263-020-01418-8; ACM DL)
- Link: https://doi.org/10.1007/s11263-020-01418-8
- What it establishes: Systematic evaluation of LLIE algorithms (full-reference, no-reference and task-driven via face detection) and the VE-LOL dataset; shows metric rankings disagree.
- How our thesis uses it: Precedent for benchmarking under a fixed, explicit protocol and for reporting several metric families rather than PSNR alone.
```bibtex
@article{liu2021benchmarking, title={Benchmarking Low-Light Image Enhancement and Beyond}, author={Liu, Jiaying and Xu, Dejia and Yang, Wenhan and Fan, Minhao and Huang, Haofeng}, journal={International Journal of Computer Vision}, volume={129}, pages={1153--1184}, year={2021}}
```

### zhao2025lowlightvision
- Title: Deep Learning for Low-Light Vision: A Comprehensive Survey
- Authors: Q. Zhao, G. Li, B. He, et al.
- Venue: IEEE TNNLS 2025 (vol. 36, no. 9) (Tier 2) — VERIFIED: yes (DOI 10.1109/TNNLS.2025.3566647; IEEE Xplore; J-GLOBAL)
- Link: https://doi.org/10.1109/TNNLS.2025.3566647
- What it establishes: Recent (2025) survey of low-light vision covering methods, datasets and evaluation metrics for both visual-quality and recognition-driven tasks.
- How our thesis uses it: Up-to-date survey citation beside Li et al. 2022; source for the current list of datasets and metrics. (Full author list should be checked on IEEE Xplore before final bib.)
```bibtex
@article{zhao2025lowlightvision, title={Deep Learning for Low-Light Vision: A Comprehensive Survey}, author={Zhao, Q. and Li, G. and He, B. and others}, journal={IEEE Transactions on Neural Networks and Learning Systems}, volume={36}, number={9}, year={2025}}
```

## 2. Dataset provenance, known issues and the GT-mean convention

### wei2018retinexnet
- Title: Deep Retinex Decomposition for Low-Light Enhancement
- Authors: Chen Wei, Wenjing Wang, Wenhan Yang, et al.
- Venue: BMVC 2018 (Tier 2) — VERIFIED: yes (arXiv 1808.04560; Semantic Scholar record, BMVC 2018)
- Link: https://arxiv.org/abs/1808.04560
- What it establishes: Introduces RetinexNet and the LOL (LOL-v1) dataset: 500 real low/normal-light pairs (485 train / 15 test), captured by changing exposure time and ISO.
- How our thesis uses it: Provenance of LOL-v1; source of the 485/15 split from which we carve our held-out validation subset.
```bibtex
@inproceedings{wei2018retinexnet, title={Deep Retinex Decomposition for Low-Light Enhancement}, author={Wei, Chen and Wang, Wenjing and Yang, Wenhan and Liu, Jiaying}, booktitle={British Machine Vision Conference (BMVC)}, year={2018}}
```

### yang2021sparse
- Title: Sparse Gradient Regularized Deep Retinex Network for Robust Low-Light Image Enhancement
- Authors: Wenhan Yang, Wenjing Wang, Haofeng Huang, et al.
- Venue: IEEE TIP 2021 (vol. 30, pp. 2072-2086) (Tier 2) — VERIFIED: yes (DOI 10.1109/TIP.2021.3050850; PubMed 33460379)
- Link: https://doi.org/10.1109/TIP.2021.3050850
- What it establishes: Introduces LOL-v2 (Real: 689/100; Synthetic: 900/100 pairs), the standard second LLIE benchmark.
- How our thesis uses it: Provenance of LOL-v2 real/synthetic, if used for cross-dataset checks.
```bibtex
@article{yang2021sparse, title={Sparse Gradient Regularized Deep Retinex Network for Robust Low-Light Image Enhancement}, author={Yang, Wenhan and Wang, Wenjing and Huang, Haofeng and Wang, Shiqi and Liu, Jiaying}, journal={IEEE Transactions on Image Processing}, volume={30}, pages={2072--2086}, year={2021}}
```

### nguyen2024diffusiondark
- Title: Diffusion in the Dark: A Diffusion Model for Low-Light Text Recognition
- Authors: Cindy M. Nguyen, Eric R. Chan, Alexander W. Bergman, et al.
- Venue: WACV 2024 (pp. 4146-4157) (Tier 2) — VERIFIED: yes (openaccess.thecvf.com WACV2024; ML Anthology)
- Link: https://arxiv.org/abs/2303.04291
- What it establishes: Supplementary S3.2 documents two LOL problems: scenes overlap between LOL train and test, and the well-lit test GTs are much more contrasted than the training GTs (apparently post-processed), which makes it "challenging to get an accurate sense of performance".
- How our thesis uses it: Primary citation for known LOL-v1 flaws; motivates caution with the 15 test images and explains why train-derived validation and test scores may differ systematically.
```bibtex
@inproceedings{nguyen2024diffusiondark, title={Diffusion in the Dark: A Diffusion Model for Low-Light Text Recognition}, author={Nguyen, Cindy M. and Chan, Eric R. and Bergman, Alexander W. and Wetzstein, Gordon}, booktitle={IEEE/CVF Winter Conference on Applications of Computer Vision (WACV)}, pages={4146--4157}, year={2024}}
```

### pilligua2025multiintensity
- Title: Evaluating Low-Light Image Enhancement Across Multiple Intensity Levels
- Authors: Maria Pilligua, David Serrano-Lozano, Pai Peng, et al.
- Venue: arXiv 2025 (v2 April 2026; no peer-reviewed venue found) (other) — VERIFIED: no
- Link: https://arxiv.org/abs/2511.15496
- What it establishes: Independent statement that LOL-type datasets contain the same scenes in train and test and fix one brightness level per scene; proposes the MILL multi-intensity benchmark and evaluates with PSNR, SSIM, LPIPS, colour ΔE, NIQE and BRISQUE.
- How our thesis uses it: Second source for the LOL train/test scene overlap; example of a recent evaluation-focused LLIE paper that reports colour and no-reference metrics.
```bibtex
@article{pilligua2025multiintensity, title={Evaluating Low-Light Image Enhancement Across Multiple Intensity Levels}, author={Pilligua, Maria and Serrano-Lozano, David and Peng, Pai and Baldrich, Ramon and Brown, Michael S. and Vazquez-Corral, Javier}, journal={arXiv preprint arXiv:2511.15496}, year={2025}}
```

### cai2023retinexformer
- Title: Retinexformer: One-stage Retinex-based Transformer for Low-light Image Enhancement
- Authors: Yuanhao Cai, Hao Bian, Jing Lin, et al.
- Venue: ICCV 2023 (pp. 12504-12513) (Tier 1) — VERIFIED: yes (openaccess.thecvf.com ICCV2023; arXiv 2303.06705)
- Link: https://arxiv.org/abs/2303.06705
- What it establishes: Strong LLIE baseline. Its official README offers a `--GT_mean` test option "the same test setting as LLFlow, KinD, and recent diffusion models" but says the authors "do not suggest this test setting because it uses the mean of the ground truth to obtain better results".
- How our thesis uses it: The most direct statement by an upstream author against GT-mean evaluation; we cite it when explaining our GT-mean choice.
```bibtex
@inproceedings{cai2023retinexformer, title={Retinexformer: One-stage Retinex-based Transformer for Low-light Image Enhancement}, author={Cai, Yuanhao and Bian, Hao and Lin, Jing and Wang, Haoqian and Timofte, Radu and Zhang, Yulun}, booktitle={Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)}, pages={12504--12513}, year={2023}}
```

### liao2025gtmean
- Title: GT-Mean Loss: A Simple Yet Effective Solution for Brightness Mismatch in Low-Light Image Enhancement
- Authors: Jingxi Liao, Shijie Hao, Richang Hong, et al.
- Venue: ICCV 2025 (Tier 1) — VERIFIED: yes (CVF open-access PDF URL; ML Anthology; DOI 10.1109/ICCV51701.2025.00577)
- Link: https://arxiv.org/abs/2507.20148
- What it establishes: Defines "brightness mismatch" (E[f(x)] differs from E[y]) as a real, overlooked problem in supervised LLIE, and moves the GT-mean idea into training through a loss using lambda = E[y]/E[f(x)].
- How our thesis uses it: Peer-reviewed evidence that global brightness mismatch is systematic, so GT-mean evaluation removes a real error component rather than noise. Use it to argue for reporting both raw and GT-mean PSNR.
```bibtex
@inproceedings{liao2025gtmean, title={GT-Mean Loss: A Simple Yet Effective Solution for Brightness Mismatch in Low-Light Image Enhancement}, author={Liao, Jingxi and Hao, Shijie and Hong, Richang and Wang, Meng}, booktitle={Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)}, year={2025}}
```

## 3. Metrics

### wang2009mse
- Title: Mean Squared Error: Love It or Leave It? A New Look at Signal Fidelity Measures
- Authors: Zhou Wang, Alan C. Bovik
- Venue: IEEE Signal Processing Magazine 2009 (vol. 26, no. 1, pp. 98-117) (other) — VERIFIED: yes (DOI 10.1109/MSP.2008.930649; ADS)
- Link: https://doi.org/10.1109/MSP.2008.930649
- What it establishes: Canonical argument that MSE/PSNR correlate poorly with perceived quality; it is especially sensitive to global intensity shifts that people barely notice.
- How our thesis uses it: Main citation for the limits of PSNR, and for why a global brightness offset (the target of GT-mean) dominates PSNR.
```bibtex
@article{wang2009mse, title={Mean Squared Error: Love It or Leave It? A New Look at Signal Fidelity Measures}, author={Wang, Zhou and Bovik, Alan C.}, journal={IEEE Signal Processing Magazine}, volume={26}, number={1}, pages={98--117}, year={2009}}
```

### zhang2018lpips
- Title: The Unreasonable Effectiveness of Deep Features as a Perceptual Metric
- Authors: Richard Zhang, Phillip Isola, Alexei A. Efros, et al.
- Venue: CVPR 2018 (pp. 586-595) (Tier 1) — VERIFIED: yes (openaccess.thecvf.com CVPR2018)
- Link: https://arxiv.org/abs/1801.03924
- What it establishes: LPIPS; deep-feature distances match human similarity judgments far better than PSNR/SSIM.
- How our thesis uses it: Justifies reporting LPIPS next to PSNR/SSIM (as HVI-CIDNet and NTIRE LLIE do).
```bibtex
@inproceedings{zhang2018lpips, title={The Unreasonable Effectiveness of Deep Features as a Perceptual Metric}, author={Zhang, Richard and Isola, Phillip and Efros, Alexei A. and Shechtman, Eli and Wang, Oliver}, booktitle={Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}, pages={586--595}, year={2018}}
```

### mittal2013niqe
- Title: Making a "Completely Blind" Image Quality Analyzer
- Authors: Anish Mittal, Rajiv Soundararajan, Alan C. Bovik
- Venue: IEEE Signal Processing Letters 2013 (vol. 20, no. 3, pp. 209-212) (other) — VERIFIED: yes (Semantic Scholar; MathWorks niqe reference)
- Link: https://doi.org/10.1109/LSP.2012.2227726
- What it establishes: NIQE, an opinion-unaware no-reference quality score based on natural-scene statistics.
- How our thesis uses it: No-reference metric for unpaired LLIE sets (DICM/LIME/MEF/NPE); also part of the NTIRE 2025 ranking.
```bibtex
@article{mittal2013niqe, title={Making a ``Completely Blind'' Image Quality Analyzer}, author={Mittal, Anish and Soundararajan, Rajiv and Bovik, Alan C.}, journal={IEEE Signal Processing Letters}, volume={20}, number={3}, pages={209--212}, year={2013}}
```

### mittal2012brisque
- Title: No-Reference Image Quality Assessment in the Spatial Domain
- Authors: Anish Mittal, Anush Krishna Moorthy, Alan C. Bovik
- Venue: IEEE TIP 2012 (vol. 21, no. 12, pp. 4695-4708) (Tier 2) — VERIFIED: yes (DOI 10.1109/TIP.2012.2214050; ACM DL; ADS)
- Link: https://doi.org/10.1109/TIP.2012.2214050
- What it establishes: BRISQUE, a trained no-reference quality model on locally normalised luminance statistics.
- How our thesis uses it: Second no-reference metric (HVI-CIDNet reports BRISQUE/NIQE on unpaired sets).
```bibtex
@article{mittal2012brisque, title={No-Reference Image Quality Assessment in the Spatial Domain}, author={Mittal, Anish and Moorthy, Anush Krishna and Bovik, Alan C.}, journal={IEEE Transactions on Image Processing}, volume={21}, number={12}, pages={4695--4708}, year={2012}}
```

### blau2018pirm
- Title: The 2018 PIRM Challenge on Perceptual Image Super-resolution
- Authors: Yochai Blau, Roey Mechrez, Radu Timofte, et al.
- Venue: ECCV Workshops 2018 (Tier 2) — VERIFIED: yes (openaccess.thecvf.com ECCVW 2018; Springer LNCS chapter)
- Link: https://arxiv.org/abs/1809.07517
- What it establishes: Defines the Perceptual Index PI = ((10 - Ma) + NIQE)/2, evaluates methods on the perception-distortion plane, and analyses which IQA measures agree with human opinion.
- How our thesis uses it: Source for PI and for the perception-distortion framing (PSNR gains can cost perceptual quality).
```bibtex
@inproceedings{blau2018pirm, title={The 2018 PIRM Challenge on Perceptual Image Super-resolution}, author={Blau, Yochai and Mechrez, Roey and Timofte, Radu and Michaeli, Tomer and Zelnik-Manor, Lihi}, booktitle={Proceedings of the European Conference on Computer Vision (ECCV) Workshops}, year={2018}}
```

### sharma2005ciede2000
- Title: The CIEDE2000 Color-Difference Formula: Implementation Notes, Supplementary Test Data, and Mathematical Observations
- Authors: Gaurav Sharma, Wencheng Wu, Edul N. Dalal
- Venue: Color Research & Application 2005 (vol. 30, no. 1, pp. 21-30) (other) — VERIFIED: yes (Wiley DOI 10.1002/col.20070; author's Rochester page)
- Link: https://doi.org/10.1002/col.20070
- What it establishes: The standard reference implementation of the CIEDE2000 ΔE00 perceptual colour difference.
- How our thesis uses it: Colour-fidelity metric that fits an HVI (colour-space) study; ΔE00 depends on lightness, so we report it with and without GT-mean.
```bibtex
@article{sharma2005ciede2000, title={The CIEDE2000 Color-Difference Formula: Implementation Notes, Supplementary Test Data, and Mathematical Observations}, author={Sharma, Gaurav and Wu, Wencheng and Dalal, Edul N.}, journal={Color Research \& Application}, volume={30}, number={1}, pages={21--30}, year={2005}}
```

## 4. Reproducibility, variance, benchmark overfitting and NTIRE challenge protocols

### bouthillier2021variance
- Title: Accounting for Variance in Machine Learning Benchmarks
- Authors: Xavier Bouthillier, Pierre Delaunay, Mirko Bronzi, et al.
- Venue: MLSys 2021 (Proc. MLSys vol. 3, pp. 747-769) (Tier 2) — VERIFIED: yes (proceedings.mlsys.org; dblp record URL found via search)
- Link: https://arxiv.org/abs/2103.03098
- What it establishes: Variance from data sampling, weight initialisation and hyperparameter choice changes benchmark conclusions markedly; recommends randomising several sources of variation and using proper statistical comparisons.
- How our thesis uses it: Core justification for fixed seeds with three runs per condition and for reporting mean ± SD.
```bibtex
@inproceedings{bouthillier2021variance, title={Accounting for Variance in Machine Learning Benchmarks}, author={Bouthillier, Xavier and Delaunay, Pierre and Bronzi, Mirko and Trofimov, Assya and Nichyporuk, Brennan and Szeto, Justin and Sepahvand, Nazanin Mohammadi and Raff, Edward and Madan, Kanika and Voleti, Vikram and Kahou, Samira Ebrahimi and Michalski, Vincent and Arbel, Tal and Pal, Chris and Varoquaux, Ga{\"e}l and Vincent, Pascal}, booktitle={Proceedings of Machine Learning and Systems (MLSys)}, volume={3}, pages={747--769}, year={2021}}
```

### pineau2021reproducibility
- Title: Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program)
- Authors: Joelle Pineau, Philippe Vincent-Lamarre, Koustuv Sinha, et al.
- Venue: JMLR 2021 (vol. 22, no. 164, pp. 1-20) (Tier 1) — VERIFIED: yes (jmlr.org v22/20-303; ACM DL)
- Link: https://arxiv.org/abs/2003.12206
- What it establishes: The NeurIPS ML reproducibility checklist (seeds, number of runs, error bars, how hyperparameters and checkpoints were chosen, compute).
- How our thesis uses it: Checklist our protocol section follows; justifies documenting seeds, the validation split and the selection rule.
```bibtex
@article{pineau2021reproducibility, title={Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program)}, author={Pineau, Joelle and Vincent-Lamarre, Philippe and Sinha, Koustuv and Larivi{\`e}re, Vincent and Beygelzimer, Alina and d'Alch{\'e}-Buc, Florence and Fox, Emily and Larochelle, Hugo}, journal={Journal of Machine Learning Research}, volume={22}, number={164}, pages={1--20}, year={2021}}
```

### musgrave2020reality
- Title: A Metric Learning Reality Check
- Authors: Kevin Musgrave, Serge Belongie, Ser-Nam Lim
- Venue: ECCV 2020 (Tier 1) — VERIFIED: yes (ecva.net ECCV 2020 papers; Springer LNCS DOI 10.1007/978-3-030-58595-2_41)
- Link: https://arxiv.org/abs/2003.08505
- What it establishes: An "are we really making progress" audit in CV. Many papers select models and hyperparameters using test-set feedback (no validation set); under a fair protocol the claimed gains mostly disappear.
- How our thesis uses it: Closest top-venue precedent for our main protocol change, which moves checkpoint selection from the 15-image test split to a held-out validation subset.
```bibtex
@inproceedings{musgrave2020reality, title={A Metric Learning Reality Check}, author={Musgrave, Kevin and Belongie, Serge and Lim, Ser-Nam}, booktitle={European Conference on Computer Vision (ECCV)}, pages={681--699}, year={2020}}
```

### recht2019imagenet
- Title: Do ImageNet Classifiers Generalize to ImageNet?
- Authors: Benjamin Recht, Rebecca Roelofs, Ludwig Schmidt, et al.
- Venue: ICML 2019 (PMLR 97:5389-5400) (Tier 1) — VERIFIED: yes (proceedings.mlr.press v97; dblp record URL found via search)
- Link: https://arxiv.org/abs/1902.10811
- What it establishes: Rebuilt test sets show large accuracy drops for reused benchmarks; it is the standard reference on test-set reuse and adaptive overfitting (the authors attribute the drop mostly to distribution shift, not adaptivity).
- How our thesis uses it: General citation for the risk that repeated evaluation and selection on a tiny, fixed test set (LOL-v1: 15 images) inflates reported numbers. Cite it carefully, given its nuanced conclusion.
```bibtex
@inproceedings{recht2019imagenet, title={Do {ImageNet} Classifiers Generalize to {ImageNet}?}, author={Recht, Benjamin and Roelofs, Rebecca and Schmidt, Ludwig and Shankar, Vaishaal}, booktitle={Proceedings of the 36th International Conference on Machine Learning (ICML)}, series={PMLR}, volume={97}, pages={5389--5400}, year={2019}}
```

### shafi2026iphoneblur
- Title: iPhoneBlur: A Difficulty-Stratified Benchmark for Consumer Device Motion Deblurring
- Authors: Abdullah Al Shafi, Kazi Saeed Alam
- Venue: arXiv 2026 (no peer-reviewed venue found) (other) — VERIFIED: no
- Link: https://arxiv.org/abs/2605.05990
- What it establishes: A restoration benchmark that retrains each method three times (seeds 42/123/456) and reports mean ± SD. The seed SD is 0.2-0.4 dB PSNR, 0.004-0.012 SSIM and 0.002-0.005 LPIPS for NAFNet, Restormer and similar models.
- How our thesis uses it: Concrete (preprint) example of the same 3-seed design in image restoration, and a rough prior for expected seed SD. Cite only as supporting evidence.
```bibtex
@article{shafi2026iphoneblur, title={iPhoneBlur: A Difficulty-Stratified Benchmark for Consumer Device Motion Deblurring}, author={Shafi, Abdullah Al and Alam, Kazi Saeed}, journal={arXiv preprint arXiv:2605.05990}, year={2026}}
```

### liu2024ntire
- Title: NTIRE 2024 Challenge on Low Light Image Enhancement: Methods and Results
- Authors: Xiaoning Liu, Zongwei Wu, Ao Li, et al.
- Venue: CVPR Workshops 2024 (Tier 2) — VERIFIED: yes (openaccess.thecvf.com CVPR2024W/NTIRE; arXiv 2404.14248)
- Link: https://arxiv.org/abs/2404.14248
- What it establishes: A challenge protocol with hidden test GT, reporting PSNR/SSIM/LPIPS; the final rank is a weighted PSNR (60%) + SSIM (40%) score.
- How our thesis uses it: Shows that community benchmarks keep test GT hidden, the opposite of selecting checkpoints on the LOL test split.
```bibtex
@inproceedings{liu2024ntire, title={NTIRE 2024 Challenge on Low Light Image Enhancement: Methods and Results}, author={Liu, Xiaoning and Wu, Zongwei and Li, Ao and others}, booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) Workshops}, year={2024}}
```

### liu2025ntire
- Title: NTIRE 2025 Challenge on Low Light Image Enhancement: Methods and Results
- Authors: Xiaoning Liu, Zongwei Wu, Florin-Alexandru Vasluianu, et al.
- Venue: CVPR Workshops 2025 (Tier 2) — VERIFIED: yes (openaccess.thecvf.com CVPR2025W/NTIRE; arXiv 2510.13670)
- Link: https://arxiv.org/abs/2510.13670
- What it establishes: 219 train pairs, 46 validation and 30 test images, with validation and test GT hidden. The composite rank weights PSNR 50%, SSIM 50%, LPIPS 40% and NIQE 20%. No GT-mean correction is mentioned. HVI-CIDNet's repository lists NTIRE 2025 participation.
- How our thesis uses it: Current community evaluation standard (hidden GT, mixed fidelity and perceptual ranking) that we compare our protocol against.
```bibtex
@inproceedings{liu2025ntire, title={NTIRE 2025 Challenge on Low Light Image Enhancement: Methods and Results}, author={Liu, Xiaoning and Wu, Zongwei and Vasluianu, Florin-Alexandru and others}, booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) Workshops}, year={2025}}
```

### ciubotariu2026ntire
- Title: Low Light Image Enhancement Challenge at NTIRE 2026
- Authors: George Ciubotariu, Sharif S M A, Abdur Rehman, et al.
- Venue: CVPR Workshops 2026 (Tier 2) — VERIFIED: yes (openaccess.thecvf.com CVPR2026W/NTIRE PDF; arXiv 2604.17669)
- Link: https://arxiv.org/abs/2604.17669
- What it establishes: Two tracks. The reference track uses min-max-normalised PSNR/SSIM/LPIPS weighted equally. The no-reference track uses MOS (50%) plus NIQE/MUSIQ/CLIP-IQA. Validation and test GT are hidden.
- How our thesis uses it: The most recent evaluation standard: fidelity and perceptual metrics combined, with human MOS where no GT exists. (A separate NTIRE 2026 Efficient LLIE report, arXiv 2605.02212, also exists.)
```bibtex
@inproceedings{ciubotariu2026ntire, title={Low Light Image Enhancement Challenge at {NTIRE} 2026}, author={Ciubotariu, George and A, Sharif S M and Rehman, Abdur and others}, booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) Workshops}, year={2026}}
```

## 5. Statistical practice for small benchmarks

### dror2018hitchhiker
- Title: The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing
- Authors: Rotem Dror, Gili Baumer, Segev Shlomov, et al.
- Venue: ACL 2018 (pp. 1383-1392) (Tier 2) — VERIFIED: yes (ACL Anthology P18-1128)
- Link: https://aclanthology.org/P18-1128/
- What it establishes: A practical guide to choosing significance tests (paired t-test, Wilcoxon signed-rank, permutation, bootstrap) based on the metric and sample size; shows these tests are often skipped or misused.
- How our thesis uses it: Justifies paired, per-image tests (Wilcoxon signed-rank or permutation) on the 15 LOL-v1 test images when comparing conditions.
```bibtex
@inproceedings{dror2018hitchhiker, title={The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing}, author={Dror, Rotem and Baumer, Gili and Shlomov, Segev and Reichart, Roi}, booktitle={Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (ACL)}, pages={1383--1392}, year={2018}}
```

### koehn2004bootstrap
- Title: Statistical Significance Tests for Machine Translation Evaluation
- Authors: Philipp Koehn
- Venue: EMNLP 2004 (pp. 388-395) (Tier 2) — VERIFIED: yes (ACL Anthology W04-3250; dblp record URL found via search)
- Link: https://aclanthology.org/W04-3250/
- What it establishes: The paired bootstrap resampling test for corpus-level metrics on small test sets.
- How our thesis uses it: Method reference for paired-bootstrap confidence intervals on mean PSNR/SSIM differences, resampling the 15 test images (and the 3 seeds).
```bibtex
@inproceedings{koehn2004bootstrap, title={Statistical Significance Tests for Machine Translation Evaluation}, author={Koehn, Philipp}, booktitle={Proceedings of the 2004 Conference on Empirical Methods in Natural Language Processing (EMNLP)}, pages={388--395}, year={2004}}
```

---

## GT-mean convention: what I found
- **Who uses it:** GT-mean scales the output so its mean matches the GT mean before PSNR/SSIM, so it needs paired data. The Retinexformer and HVI-CIDNet READMEs both attribute it to LLFlow and KinD. Retinexformer [cai2023retinexformer] offers `--GT_mean` as an option. HVI-CIDNet reports GT-mean numbers on LOL-v1/v2, SICE and FiveK behind `--use_GT_mean`: LOL-v1 PSNR goes from 23.81 to 27.71 dB (its README says it is "following LLFlow, KinD, and Retinexformer"). Neither the LLFlow README nor the GT-mean-loss paper names who first introduced it, so the origin is uncited folklore.
- **Who criticises it:** Retinexformer's own README advises against it because "it uses the mean of the ground truth to obtain better results", which amounts to test-time GT leakage. Han et al. (arXiv 2603.25296, preprint) call it post-hoc scaling that many SOTA methods "necessitate" and aim to reduce reliance on it. Li et al. (arXiv 2604.08172, preprint) likewise treat global photometric mismatch as a training-side problem.
- **What it hides:** Liao et al. (ICCV 2025) [liao2025gtmean] show that brightness mismatch is systematic and fix it in training rather than evaluation. Wang & Bovik [wang2009mse] explain why a global offset dominates PSNR.
- **Implication:** GT-mean PSNR measures structure and colour fidelity with exposure factored out, but it is not a deployable number. Report both raw and GT-mean metrics, clearly labelled. None of the NTIRE 2024/2025/2026 reports mentions a GT-mean correction, so challenge evaluation appears to use raw outputs (not stated explicitly).

## Seed/variance reporting in LLIE: what I found
- I found no top-venue LLIE paper that reports mean ± SD over several training seeds. HVI-CIDNet, Retinexformer and the NTIRE 2024-2026 reports all present single-run or single-submission numbers.
- Upstream LOL-v1 practice selects the checkpoint with the best score on the same 15 test images it then reports. This matches the flaw Musgrave et al. [musgrave2020reality] identified in metric learning ("no validation set; model selection with test-set feedback"). NTIRE avoids it by hiding test GT [liu2024ntire, liu2025ntire, ciubotariu2026ntire]. LOL-v1 has two further problems: train/test scene overlap and contrast-boosted test GTs [nguyen2024diffusiondark, pilligua2025multiintensity].
- General ML support for multi-seed reporting and error bars: Bouthillier et al. [bouthillier2021variance] and the NeurIPS checklist [pineau2021reproducibility]. For restoration, the only concrete 3-seed example I found is a 2026 deblurring preprint [shafi2026iphoneblur], which reports seed SD of about 0.2-0.4 dB PSNR. That is the same size as many claimed LLIE improvements, so it is a useful point of comparison.
- For 15 paired test images: use paired per-image tests (Wilcoxon or permutation) [dror2018hitchhiker] and paired-bootstrap CIs [koehn2004bootstrap], and report SD across the 3 seeds separately from per-image spread.
