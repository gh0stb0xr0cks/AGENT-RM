---
paths:
  - "inference/**/*"
---

# Règles couche inférence

## Endpoint Ollama
- URL locale uniquement : http://localhost:11434
- NE JAMAIS exposer à l'extérieur du SI (mode offline strict)
- API compatible format OpenAI

## Paramètres Modelfile (inférence production)
```
PARAMETER temperature     0.2
PARAMETER top_p           0.9
PARAMETER top_k           40
PARAMETER num_predict     2048
PARAMETER num_ctx         8192
PARAMETER repeat_penalty  1.1
PARAMETER num_thread      8
PARAMETER num_gpu         35   # 0 = CPU only
```

## Quantification par profil matériel
| Profil | Format | RAM | VRAM | Usage |
|--------|--------|-----|------|-------|
| CPU standard | Q4_K_M | 16 Go | — | LM Studio livrable |
| GPU RTX 3060+ | Q5_K_M | 16 Go | 8 Go | Qualité supérieure |
| GPU RTX 3090  | Q8_0   | 16 Go | 16 Go | Développement/éval |

## Vérifications post-quantification (verify_model.py)
1. `sha256sum` → SHA256SUMS.txt
2. Test chargement Ollama : `ollama run mistral-ebios-rm "Atelier 1 EBIOS RM :"`
3. Test chargement LM Studio (manuel, v0.3+)
4. Comparer output base vs fine-tuné sur 5 prompts de référence
