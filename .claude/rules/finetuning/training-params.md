---
paths:
  - "finetuning/**/*"
---

# Règles fine-tuning QLoRA

## Hyperparamètres LoRA — NE PAS MODIFIER sans justification explicite
```yaml
lora_r:      16    # Rang — compromis capacité/efficacité
lora_alpha:  32    # Scaling α/r = 2.0 (standard)
lora_dropout: 0.05
target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
bias: "none"
task_type: "CAUSAL_LM"
```

## Hyperparamètres training — configs/training_args.yaml
```yaml
num_train_epochs: 3
per_device_train_batch_size: 4   # A100 40 Go
gradient_accumulation_steps: 4  # effective batch = 16
learning_rate: 2.0e-4
lr_scheduler_type: "cosine"
warmup_ratio: 0.03
optim: "paged_adamw_8bit"
bf16: true
max_seq_length: 2048
eval_strategy: "epoch"
save_strategy: "epoch"
save_total_limit: 3
report_to: "none"   # OFFLINE — pas de tracking cloud
packing: false      # contextes EBIOS longs
```

## Ordre pipeline (merge-export)
1. `scripts/train_unsloth.py`  → checkpoints/
2. `scripts/merge_lora.py`     → output/mistral-ebios-rm-fp16/
3. `scripts/quantize_gguf.py`  → output/mistral-7b-ebios-rm-q4_k_m.gguf
4. `scripts/verify_model.py`   → SHA256SUMS.txt + test Ollama

## Formats GGUF à produire
- Q4_K_M (~4.1 Go) → livrable L4 principal (LM Studio CPU)
- Q5_K_M (~5.4 Go) → option GPU dédié

## Critère d'arrêt anticipé
eval_loss augmente 2 epochs consécutives → stopper le training.
eval_loss < 0.8 après epoch 2 → résultat satisfaisant.

## À ne PAS committer dans Git
- checkpoints/ (volumineux)
- output/*.gguf → utiliser Git LFS
- output/mistral-ebios-rm-fp16/ (14 Go)
