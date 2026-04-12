---
paths:
  - "app/api/**/*"
  - "app/main.py"
---

# Sécurité API — Exigences ANSSI S1/S2/S3

## Authentification (EXI_S1_*)
- Compte administrateur DISTINCT des comptes utilisateurs (EXI_S1_01)
- Identifiants nominatifs, non génériques (EXI_S1_03)
- Authentification mot de passe minimum pour tous les profils (EXI_S1_04)
- Droits lecture/écriture paramétrables par profil ET par analyse (EXI_S1_05/06)
- Validation côté serveur obligatoire (EXI_S1_07)

## Confidentialité des données (EXI_S2_*)
- Données stockées : intégrité + confidentialité garanties (EXI_S2_01)
- Données en transit : TLS obligatoire même en local (EXI_S2_03)
- Mécanismes conformes aux guides ANSSI (TLS/IPSEC/SSH)

## Journalisation (EXI_S3_*)
Journaliser obligatoirement (EXI_S3_04) :
- Ouverture/fermeture de session
- Verrouillage de compte
- Gestion des comptes (création/suppression)
- Accès à une analyse de risques
- Manipulation des journaux
- Événements applicatifs critiques

Protection des journaux : générer un événement lors de tout effacement (EXI_S3_05).

## Headers de sécurité à inclure dans toutes les réponses API
```python
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'
```
