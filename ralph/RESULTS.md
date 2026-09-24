# RESULTS.md — one row per exported run (experiment appends; master and writing read)

| date | run_id | jobs complete/total | finding (no adjectives) | file |
|---|---|---|---|---|
| 2026-09-23 | baseline__smoke_v1 | 1/1 | instrument smoke, 2 of 1000 epochs, upstream protocol (batch 8, crop 256, FP32); pipeline + export green; NOT citable | ralph/results/baseline__smoke_v1.json |
| 2026-09-23 | baseline__determinism_a | 1/1 | same-seed replicate of smoke_v1 on GPU 2; epoch 1 bitwise identical, epoch 2 differs (val PSNR spread 0.042 dB over 3 replicates); NOT citable | ralph/results/baseline__determinism_a.json |
| 2026-09-23 | baseline__determinism_b | 1/1 | same-seed replicate on GPU 3; see determinism_a; NOT citable | ralph/results/baseline__determinism_b.json |
| 2026-09-23 | baseline__smoke_strict_v1 | 1/1 | strict torch.use_deterministic_algorithms smoke, 2 epochs: 40.2 s/epoch train vs 26.2 default (1.5x), peak 9.63 GiB; NOT citable | ralph/results/baseline__smoke_strict_v1.json |
| 2026-09-24 | finetune__rankcheck_v2 | 2/2 | fine-tune from released w_perc, 50 epochs, lr 3e-5, scene_v1 val: A0 best 29.14 dB (ep 9) / last 28.79; A2 (k=0) best 21.42 (ep 7) / last 21.12; A0−A2 = +7.72 (best), +7.67 (last); A2 declines after epoch 7; one seed, NOT citable | ralph/results/finetune__rankcheck_v2.json |
| 2026-09-24 | baseline__rankcheck_v2 | 0/2 (running) | from-scratch 1000-epoch pair A0 vs A2, seed 42; export refreshed at completion; one seed, NOT citable | ralph/results/baseline__rankcheck_v2.json |
