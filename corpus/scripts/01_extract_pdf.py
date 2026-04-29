"""
01_extract_pdf.py — Extraction de texte depuis les sources documentaires officielles.

Sources attendues dans corpus/raw/ :
  - anssi/   : guides EBIOS RM, référentiel de qualification, fiches pratiques (PDF)
  - mitre/   : ATT&CK Enterprise / ICS / Mobile (PDF + JSON par feuille produit
               par 00_extract_mitre_xlsx.py — tactics, techniques, software,
               groups, campaigns, mitigations)

Sortie : corpus/raw/anssi/*.txt  et  corpus/raw/mitre/*.txt
         + corpus/raw/index.jsonl  (métadonnées par chunk)

Pour MITRE, exécuter au préalable :
  python 00_extract_mitre_xlsx.py    # produit corpus/raw/mitre/*.json

Usage :
  python 01_extract_pdf.py --source anssi
  python 01_extract_pdf.py --source mitre
  python 01_extract_pdf.py --source all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    sys.exit("pip install pdfplumber")

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
CHUNK_SIZE = 800        # tokens approximatifs (~4 chars/token → 3 200 chars)
CHUNK_OVERLAP = 80      # chevauchement pour ne pas couper les concepts


# ---------------------------------------------------------------------------
def extract_pdf(pdf_path: Path) -> str:
    """Extrait le texte brut d'un PDF avec pdfplumber."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
    return "\n\n".join(pages)


def clean_text(text: str) -> str:
    """Nettoyage post-extraction : sauts de ligne multiples, espaces parasites."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\f', '\n\n', text)        # form feeds
    text = text.strip()
    return text


def chunk_text(text: str, doc_id: str, source: str,
               chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Découpe le texte en chunks de taille fixe avec chevauchement.
    Respecte les frontières de paragraphes autant que possible.
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk: list[str] = []
    current_len = 0
    chunk_idx = 0

    for para in paragraphs:
        para_len = len(para) // 4  # approximation tokens
        if current_len + para_len > chunk_size and current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                "id":       f"{doc_id}_chunk_{chunk_idx:04d}",
                "doc_id":   doc_id,
                "source":   source,
                "chunk_idx": chunk_idx,
                "text":     chunk_text,
                "tokens_approx": len(chunk_text) // 4,
            })
            chunk_idx += 1
            # Chevauchement : on garde les N derniers paragraphes
            overlap_chars = 0
            keep = []
            for p in reversed(current_chunk):
                overlap_chars += len(p) // 4
                keep.insert(0, p)
                if overlap_chars >= overlap:
                    break
            current_chunk = keep
            current_len = sum(len(p) // 4 for p in current_chunk)

        current_chunk.append(para)
        current_len += para_len

    # Dernier chunk
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        chunks.append({
            "id":       f"{doc_id}_chunk_{chunk_idx:04d}",
            "doc_id":   doc_id,
            "source":   source,
            "chunk_idx": chunk_idx,
            "text":     chunk_text,
            "tokens_approx": len(chunk_text) // 4,
        })

    return chunks


def process_directory(source_dir: Path, source_label: str) -> list[dict]:
    """Traite tous les PDFs d'un répertoire source."""
    all_chunks: list[dict] = []
    pdf_files = sorted(source_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"  [WARN] Aucun PDF trouvé dans {source_dir}")

    for pdf_path in pdf_files:
        doc_id = pdf_path.stem.lower().replace(" ", "_")
        print(f"  Extraction : {pdf_path.name}")

        try:
            raw_text = extract_pdf(pdf_path)
            cleaned = clean_text(raw_text)

            # Sauvegarde texte brut nettoyé
            txt_out = pdf_path.parent / f"{doc_id}.txt"
            txt_out.write_text(cleaned, encoding="utf-8")

            # Chunking
            chunks = chunk_text(cleaned, doc_id=doc_id, source=source_label)
            all_chunks.extend(chunks)
            print(f"    → {len(chunks)} chunks extraits")

        except Exception as e:
            print(f"  [ERREUR] {pdf_path.name} : {e}")

    return all_chunks


# ---------------------------------------------------------------------------
# MITRE ATT&CK — JSON produit par 00_extract_mitre_xlsx.py
# ---------------------------------------------------------------------------
# Champs textuels rendus par feuille (ordre = ordre d'apparition dans le bloc).
# Les autres champs (stix_id, dates, citations…) sont volontairement ignorés
# pour garder les chunks denses et utiles à l'atelier 4.
MITRE_RENDER_FIELDS: dict[str, list[str]] = {
    "tactics":     ["tactics", "platforms"],
    "techniques":  ["tactics", "platforms", "is_sub_technique",
                    "sub_technique_of", "supports_remote", "impact_type"],
    "software":    ["type", "platforms", "aliases"],
    "groups":      ["associated_groups"],
    "campaigns":   ["first_seen", "last_seen", "associated_campaigns"],
    "mitigations": [],
}


def _format_meta(entry: dict, fields: list[str]) -> str:
    parts = []
    for f in fields:
        v = entry.get(f)
        if v in (None, "", False):
            continue
        label = f.replace("_", " ").capitalize()
        parts.append(f"**{label}:** {v}")
    return "\n".join(parts)


def render_mitre_entry(entry: dict, sheet: str, matrix: str) -> str:
    """Rend une entrée MITRE en bloc markdown auto-suffisant pour le chunking."""
    eid = entry.get("id") or "?"
    name = entry.get("name") or "(sans nom)"
    url = entry.get("url") or ""
    description = entry.get("description") or ""

    header = f"## [{sheet.upper()}] {eid} — {name}"
    meta_lines = [f"**Matrix:** {matrix}", f"**Sheet:** {sheet}"]
    if url:
        meta_lines.append(f"**URL:** {url}")

    extra = _format_meta(entry, MITRE_RENDER_FIELDS.get(sheet, []))
    if extra:
        meta_lines.append(extra)

    body = description.strip() if description else "(no description)"
    return f"{header}\n\n" + "\n".join(meta_lines) + f"\n\n{body}"


def process_mitre_json(source_dir: Path, source_label: str) -> list[dict]:
    """
    Lit les JSON produits par 00_extract_mitre_xlsx.py
    (`{matrix}__{sheet}.json`), rend chaque entrée en markdown puis applique
    le même pipeline clean → chunk que pour les PDF.
    """
    chunks: list[dict] = []
    json_files = sorted(
        f for f in source_dir.glob("*__*.json")
        if f.name != "mitre_index.json"
    )
    if not json_files:
        print("  [INFO] Aucun JSON MITRE — exécuter 00_extract_mitre_xlsx.py d'abord")
        return []

    for jf in json_files:
        # Convention de nommage : {matrix_stem}__{sheet}.json
        stem = jf.stem
        if "__" not in stem:
            continue
        matrix, sheet = stem.split("__", 1)

        try:
            entries = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [ERREUR] {jf.name} : {e}")
            continue

        if not isinstance(entries, list) or not entries:
            print(f"  [SKIP] {jf.name} (vide ou format inattendu)")
            continue

        blocks = [
            render_mitre_entry(e, sheet=sheet, matrix=matrix)
            for e in entries if isinstance(e, dict)
        ]
        full_text = clean_text("\n\n".join(blocks))

        # Sauvegarde texte brut (auditabilité, identique au flux PDF)
        txt_out = source_dir / f"{stem}.txt"
        txt_out.write_text(full_text, encoding="utf-8")

        doc_id = stem.lower().replace(" ", "_")
        sheet_chunks = chunk_text(full_text, doc_id=doc_id, source=source_label)
        # Enrichit les métadonnées de chunk pour aiguiller la RAG vers A4
        for c in sheet_chunks:
            c["mitre_matrix"] = matrix
            c["mitre_sheet"] = sheet
            c["atelier_hint"] = "A4"
        chunks.extend(sheet_chunks)
        print(f"  MITRE {matrix}/{sheet:<12} {len(entries):>5} entrées → "
              f"{len(sheet_chunks)} chunks")

    return chunks


def write_index(chunks: list[dict], output_path: Path) -> None:
    """Écrit l'index JSONL des chunks."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"\n  Index écrit : {output_path} ({len(chunks)} chunks total)")


# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Extraction PDF corpus EBIOS RM")
    parser.add_argument("--source", choices=["anssi", "mitre", "all"],
                        default="all", help="Source à traiter")
    args = parser.parse_args()

    sources_to_process = []
    if args.source in ("anssi", "all"):
        sources_to_process.append(("anssi", RAW_DIR / "anssi"))
    if args.source in ("mitre", "all"):
        sources_to_process.append(("mitre", RAW_DIR / "mitre"))

    all_chunks: list[dict] = []
    for label, directory in sources_to_process:
        print(f"\n[{label.upper()}] Traitement de {directory}")
        if not directory.exists():
            print(f"  [WARN] Répertoire inexistant : {directory}")
            continue
        all_chunks.extend(process_directory(directory, source_label=label))
        if label == "mitre":
            all_chunks.extend(process_mitre_json(directory, source_label=label))

    if all_chunks:
        write_index(all_chunks, RAW_DIR / "index.jsonl")
        total_tokens = sum(c["tokens_approx"] for c in all_chunks)
        print(f"\nRécapitulatif : {len(all_chunks)} chunks, "
              f"~{total_tokens:,} tokens")
    else:
        print("\nAucun chunk produit.")


if __name__ == "__main__":
    main()
