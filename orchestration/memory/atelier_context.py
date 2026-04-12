"""
atelier_context.py — Persistance du contexte inter-ateliers EBIOS RM.

Stocke les sorties de chaque atelier (A1->A5) pour maintenir la cohérence
entre les ateliers successifs. Par exemple, les valeurs métier identifiées
en A1 doivent être réutilisées dans les scénarios de risque de A3.

Structure interne :
{
    "A1": {"valeurs_metier": [...], "biens_supports": [...], ...},
    "A2": {"sources_risque": [...], "objectifs_vises": [...], ...},
    "A3": {"scenarios_strategiques": [...], ...},
    "A4": {"scenarios_operationnels": [...], ...},
    "A5": {"plan_traitement": [...], ...},
}
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Clés attendues par atelier (terminologie EBIOS RM 2024)
ATELIER_KEYS: dict[str, list[str]] = {
    "A1": [
        "valeurs_metier",
        "biens_supports",
        "perimetre",
        "evenements_redoutes",
        "echelle_gravite",
    ],
    "A2": [
        "sources_risque",
        "objectifs_vises",
        "couples_sr_ov",
        "cotation_pertinence",
    ],
    "A3": [
        "parties_prenantes",
        "ecosysteme",
        "scenarios_strategiques",
        "cotation_gravite",
        "cotation_vraisemblance",
    ],
    "A4": [
        "scenarios_operationnels",
        "actions_elementaires",
        "modes_operatoires",
        "vraisemblance_operationnelle",
    ],
    "A5": [
        "plan_traitement",
        "mesures_securite",
        "risques_residuels",
        "acceptation_risque",
    ],
}

# Ordre séquentiel des ateliers
ATELIER_ORDER = ["A1", "A2", "A3", "A4", "A5"]


class AtelierContext:
    """Gestionnaire du contexte inter-ateliers EBIOS RM.

    Persiste les résultats de chaque atelier pour assurer la cohérence
    de la démarche A1 -> A5. Supporte la sérialisation JSON pour
    la sauvegarde/restauration de session.
    """

    def __init__(self, session_dir: Optional[str] = None):
        """Initialise le contexte.

        Args:
            session_dir: Répertoire de sauvegarde optionnel.
                Si fourni, le contexte est sauvegardé automatiquement.
        """
        self._context: dict[str, dict[str, Any]] = {atelier: {} for atelier in ATELIER_ORDER}
        self._timestamps: dict[str, Optional[str]] = {atelier: None for atelier in ATELIER_ORDER}
        self._session_dir = session_dir

        if session_dir:
            Path(session_dir).mkdir(parents=True, exist_ok=True)

    def update(self, atelier: str, key: str, value: Any) -> None:
        """Met à jour une clé du contexte d'un atelier.

        Args:
            atelier: Identifiant de l'atelier (A1-A5).
            key: Clé à mettre à jour.
            value: Valeur à stocker.

        Raises:
            ValueError: Si l'atelier n'est pas valide.
        """
        if atelier not in ATELIER_ORDER:
            raise ValueError(f"Atelier invalide '{atelier}'. Valeurs acceptees: {ATELIER_ORDER}")

        self._context[atelier][key] = value
        self._timestamps[atelier] = datetime.now().isoformat()

        logger.debug(
            "Contexte mis a jour: %s.%s = %s",
            atelier,
            key,
            str(value)[:100],
        )

        if self._session_dir:
            self._save()

    def update_atelier(self, atelier: str, data: dict[str, Any]) -> None:
        """Met à jour le contexte complet d'un atelier.

        Args:
            atelier: Identifiant de l'atelier (A1-A5).
            data: Dictionnaire de données à stocker.
        """
        if atelier not in ATELIER_ORDER:
            raise ValueError(f"Atelier invalide '{atelier}'")

        self._context[atelier].update(data)
        self._timestamps[atelier] = datetime.now().isoformat()

        if self._session_dir:
            self._save()

    def get(self, atelier: str, key: Optional[str] = None) -> Any:
        """Récupère le contexte d'un atelier.

        Args:
            atelier: Identifiant de l'atelier (A1-A5).
            key: Clé spécifique (optionnel). Si None, retourne tout le contexte.

        Returns:
            Contexte complet de l'atelier ou valeur de la clé.
        """
        if atelier not in ATELIER_ORDER:
            return {} if key is None else None

        if key is None:
            return self._context.get(atelier, {})
        return self._context.get(atelier, {}).get(key)

    def get_previous_context(self, atelier: str) -> dict[str, dict]:
        """Récupère le contexte de tous les ateliers précédents.

        Utile pour injecter le contexte cumulé dans un prompt.

        Args:
            atelier: Atelier courant (le contexte de cet atelier n'est PAS inclus).

        Returns:
            Dictionnaire {atelier: contexte} des ateliers précédents.
        """
        if atelier not in ATELIER_ORDER:
            return {}

        idx = ATELIER_ORDER.index(atelier)
        previous = {}

        for prev_atelier in ATELIER_ORDER[:idx]:
            ctx = self._context.get(prev_atelier, {})
            if ctx:
                previous[prev_atelier] = ctx

        return previous

    def format_for_prompt(self, atelier: str) -> str:
        """Formate le contexte précédent pour injection dans un prompt LLM.

        Args:
            atelier: Atelier courant.

        Returns:
            Texte formaté résumant les résultats des ateliers précédents.
            Retourne une chaîne vide si aucun contexte antérieur.
        """
        previous = self.get_previous_context(atelier)
        if not previous:
            return ""

        parts = ["# Resultats des ateliers precedents\n"]

        for prev_atelier, ctx in previous.items():
            parts.append(f"\n## {prev_atelier}")

            for key, value in ctx.items():
                if isinstance(value, list):
                    items = ", ".join(str(v) for v in value[:10])
                    if len(value) > 10:
                        items += f" ... (+{len(value) - 10})"
                    parts.append(f"- {key}: [{items}]")
                elif isinstance(value, dict):
                    summary = json.dumps(value, ensure_ascii=False)[:200]
                    parts.append(f"- {key}: {summary}")
                else:
                    parts.append(f"- {key}: {value}")

        return "\n".join(parts)

    def is_complete(self, atelier: str) -> bool:
        """Vérifie si un atelier a un contexte complet.

        Vérifie la présence de toutes les clés attendues définies
        dans ATELIER_KEYS.
        """
        if atelier not in ATELIER_KEYS:
            return False

        expected_keys = ATELIER_KEYS[atelier]
        actual_keys = set(self._context.get(atelier, {}).keys())
        return all(k in actual_keys for k in expected_keys)

    def completion_status(self) -> dict[str, dict]:
        """Retourne l'état de complétion de chaque atelier.

        Returns:
            Dictionnaire {atelier: {"complete": bool, "keys_present": [...],
            "keys_missing": [...], "timestamp": str|None}}.
        """
        status = {}
        for atelier in ATELIER_ORDER:
            expected = set(ATELIER_KEYS.get(atelier, []))
            actual = set(self._context.get(atelier, {}).keys())
            status[atelier] = {
                "complete": expected.issubset(actual),
                "keys_present": sorted(actual & expected),
                "keys_missing": sorted(expected - actual),
                "timestamp": self._timestamps.get(atelier),
            }
        return status

    def reset(self, atelier: Optional[str] = None) -> None:
        """Réinitialise le contexte.

        Args:
            atelier: Si spécifié, réinitialise uniquement cet atelier.
                Sinon, réinitialise tout le contexte.
        """
        if atelier:
            if atelier in self._context:
                self._context[atelier] = {}
                self._timestamps[atelier] = None
        else:
            for a in ATELIER_ORDER:
                self._context[a] = {}
                self._timestamps[a] = None

        if self._session_dir:
            self._save()

    # ── Sérialisation ────────────────────────────────────────────────────

    def _save(self) -> None:
        """Sauvegarde le contexte dans le répertoire de session."""
        if not self._session_dir:
            return

        filepath = Path(self._session_dir) / "atelier_context.json"
        data = {
            "context": self._context,
            "timestamps": self._timestamps,
            "saved_at": datetime.now().isoformat(),
        }
        filepath.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.debug("Contexte sauvegarde: %s", filepath)

    @classmethod
    def load(cls, session_dir: str) -> "AtelierContext":
        """Charge un contexte depuis un répertoire de session.

        Args:
            session_dir: Répertoire contenant atelier_context.json.

        Returns:
            Instance AtelierContext avec le contexte restauré.
        """
        instance = cls(session_dir=session_dir)
        filepath = Path(session_dir) / "atelier_context.json"

        if filepath.exists():
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                instance._context = data.get("context", instance._context)
                instance._timestamps = data.get("timestamps", instance._timestamps)
                logger.info("Contexte restaure depuis %s", filepath)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Erreur chargement contexte %s: %s", filepath, e)

        return instance

    def to_dict(self) -> dict:
        """Exporte le contexte complet sous forme de dictionnaire."""
        return {
            "context": self._context,
            "timestamps": self._timestamps,
        }
