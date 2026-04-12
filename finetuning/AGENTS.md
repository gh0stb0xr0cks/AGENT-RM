# AGENTS.md — finetuning/

## Rôle de ce module

Entraîner les adaptateurs LoRA/QLoRA sur le corpus EBIOS RM, fusionner les poids,
et exporter le modèle fine-tuné en format GGUF pour LM Studio et Ollama.

## Prérequis

- Corpus validé disponible : `../corpus/datasets/train.jsonl` et `validation.jsonl`
- GPU : NVIDIA A100 40Go (recommandé) OU 2× RTX 3090 24Go
- VRAM minimale : 24 Go (QLoRA 4-bit avec gradient checkpointing)
- Modèle base téléchargé localement (offline) : indiqué dans `configs/training_args.yaml`

## Étapes du pipeline (ordre strict)

```
1. scripts/train_unsloth.py    → checkpoints/epoch-{1,2,3}/
2. scripts/merge_lora.py       → output/mistral-ebios-rm-fp16/
3. scripts/quantize_gguf.py    → output/mistral-7b-ebios-rm-q4_k_m.gguf
                                  output/mistral-7b-ebios-rm-q5_k_m.gguf
4. scripts/verify_model.py     → output/SHA256SUMS.txt + test chargement
```

## Hyperparamètres LoRA (configs/lora_config.yaml)

```yaml
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj
bias: "none"
task_type: "CAUSAL_LM"
use_rslora: false
```

## Hyperparamètres training (configs/training_args.yaml)

```yaml
num_train_epochs: 3
per_device_train_batch_size: 4
gradient_accumulation_steps: 4   # effective batch = 16
learning_rate: 2.0e-4
lr_scheduler_type: "cosine"
warmup_ratio: 0.03
optim: "paged_adamw_8bit"
bf16: true
max_seq_length: 2048
logging_steps: 10
eval_strategy: "epoch"
save_strategy: "epoch"
save_total_limit: 3
load_best_model_at_end: true
metric_for_best_model: "eval_loss"
report_to: "none"     # OFFLINE — pas de tracking cloud
packing: false        # Ne pas packer — contextes EBIOS longs
```

## Critères d'arrêt anticipé (early stopping)

- eval_loss augmente 2 epochs consécutives → arrêt
- eval_loss < 0.8 après epoch 2 → entraînement satisfaisant
- Vérifier dans les logs : `trainer_state.json` dans le checkpoint

## Formats de sortie GGUF

| Format | Taille | Usage | Livrable |
|--------|--------|-------|----------|
| Q4_K_M | ~4.1 Go | LM Studio CPU/GPU | L4 principal |
| Q5_K_M | ~5.4 Go | GPU dédié | L4 alternatif |
| FP16   | ~14 Go  | Archivage + réentraînement | Interne |
| LoRA weights | ~180 Mo | PEFT format | Interne |

## Vérifications obligatoires après quantification

```bash
# 1. Vérification intégrité
sha256sum output/mistral-7b-ebios-rm-q4_k_m.gguf

# 2. Test chargement Ollama
ollama create mistral-ebios-rm -f ../inference/modelfiles/Modelfile.ebios
ollama run mistral-ebios-rm "Génère les valeurs métier EBIOS A1 pour un hôpital"

# 3. Test chargement llama.cpp
./llama.cpp/llama-cli -m output/mistral-7b-ebios-rm-q4_k_m.gguf \
  -p "Atelier 1 EBIOS RM :" --temp 0.2 -n 200
```

## Ne PAS committer dans Git

- `checkpoints/` (trop volumineux)
- `output/*.gguf` (utiliser Git LFS ou livraison directe)
- `output/mistral-ebios-rm-fp16/` (14 Go)
