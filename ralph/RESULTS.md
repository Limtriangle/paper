# RESULTS.md — one row per exported run (experiment appends; master and writing read)

| date | run_id | jobs complete/total | finding (no adjectives) | file |
|---|---|---|---|---|
| 2026-09-23 | baseline__smoke_v1 | 1/1 | instrument smoke, 2 of 1000 epochs, upstream protocol (batch 8, crop 256, FP32); pipeline + export green; NOT citable | ralph/results/baseline__smoke_v1.json |
| 2026-09-23 | baseline__determinism_a | 1/1 | same-seed replicate of smoke_v1 on GPU 2; epoch 1 bitwise identical, epoch 2 differs (val PSNR spread 0.042 dB over 3 replicates); NOT citable | ralph/results/baseline__determinism_a.json |
| 2026-09-23 | baseline__determinism_b | 1/1 | same-seed replicate on GPU 3; see determinism_a; NOT citable | ralph/results/baseline__determinism_b.json |
| 2026-09-23 | baseline__smoke_strict_v1 | 1/1 | strict torch.use_deterministic_algorithms smoke, 2 epochs: 40.2 s/epoch train vs 26.2 default (1.5x), peak 9.63 GiB; NOT citable | ralph/results/baseline__smoke_strict_v1.json |
