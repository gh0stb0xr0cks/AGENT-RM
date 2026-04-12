---
paths:
  - "app/ui/**/*"
---

# Interface Streamlit — EBIOS RM

## Structure attendue par atelier
Chaque atelier est une page Streamlit distincte :
```
app/ui/pages/
├── 1_Cadrage.py
├── 2_Sources.py
├── 3_Strategique.py
├── 4_Operationnel.py
└── 5_Traitement.py
```

## Comportement streaming
- Utiliser `st.write_stream()` pour afficher les réponses LLM en temps réel
- Ne jamais bloquer l'UI pendant une inférence — toujours streamer
- Afficher un spinner `st.spinner("Génération en cours…")` pendant le retrieval RAG

## Gestion de session
```python
# Persister le contexte entre ateliers dans st.session_state
st.session_state["atelier_context"]  # Dict A1→A5
st.session_state["current_atelier"]  # Atelier actif
```

## Export des livrables
Chaque atelier doit proposer un bouton d'export :
- Format Markdown (`.md`) — minimal, toujours disponible
- Format DOCX (`.docx`) — via python-docx, optionnel
- Le nom du fichier inclut la date : `ebios_A1_cadrage_20250601.md`

## UX offline — pas d'appel réseau
- Aucune icône CDN, aucune font Google chargée à l'exécution
- Tous les assets sont servis depuis `app/static/`
