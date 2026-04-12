# AGENTS.md — inference/

## Rôle de ce module

Configurer et gérer la couche d'inférence locale : Modelfile Ollama,
config LM Studio, et scripts de test de performance.

## Modelfile Ollama (modelfiles/Modelfile.ebios)

Le Modelfile est le fichier de configuration principal pour Ollama.
Il définit le modèle de base (GGUF), les paramètres d'inférence,
et le prompt système EBIOS RM.

Commande de création :
```bash
ollama create mistral-ebios-rm -f inference/modelfiles/Modelfile.ebios
```

## Config LM Studio (configs/lm_studio_config.json)

Fichier livrable L5. Contient :
- Chemin vers le modèle GGUF
- Paramètres d'inférence (temperature, top_p, etc.)
- Prompt système EBIOS RM
- Chemins vers les templates d'ateliers

## Paramètres d'inférence par défaut

```python
DEFAULT_PARAMS = {
    "temperature": 0.2,       # Override par atelier
    "top_p": 0.9,
    "top_k": 40,
    "max_tokens": 2048,
    "context_length": 8192,
    "repeat_penalty": 1.1,
    "stream": True,
}
```

## Configuration matérielle (inference_params.yaml)

```yaml
# Mode CPU seul (minimum viable)
cpu_only:
  gpu_layers: 0
  cpu_threads: 8
  use_mlock: true
  quantization: "Q4_K_M"

# Mode GPU recommandé
gpu_mode:
  gpu_layers: 35
  cpu_threads: 4
  use_mlock: true
  quantization: "Q5_K_M"
```

## Endpoint Ollama

URL locale : `http://localhost:11434`
Compatible OpenAI API format.
NE PAS exposer à l'extérieur (mode offline strict).
