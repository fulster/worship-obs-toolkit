#!/usr/bin/env python3
"""Vérifie les invariants du dossier des ADR (voir D-002).

Usage :
    python scripts/adr_check.py
    python scripts/adr_check.py --dir docs/decisions --index README.md

Checks (exit 1 au premier rapport s'il y a au moins une erreur) :
  1. unicité des préfixes D-NNN entre fichiers (collision de branches) ;
  2. synchronisation index <-> fichiers, dans les deux sens ;
  3. cohérence id: du frontmatter = préfixe du filename ;
  4. frontmatter de base : champs requis, enums status/type,
     verdict <=> type closure, amends <=> type amendement, format date ;
  5. références D-NNN des TODO (D-005) : toute occurrence D-NNN dans
     docs/todo/ et TODO.md (auto-détectés) ou les chemins --refs doit
     pointer vers un ADR existant. Périmètre volontairement explicite :
     pas de scan global (le guide/les ADR contiennent des D-NNN
     illustratifs).

Stdlib uniquement — le frontmatter est parsé par un lecteur YAML
minimal (clés scalaires + listes de scalaires), suffisant pour le
schema des ADR. Les fichiers _template_*.md et l'index sont ignorés.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ID_PREFIX_RE = re.compile(r"^(D-\d{3,})-")
REF_RE = re.compile(r"\bD-\d{3,}\b")
ADR_ID_RE = re.compile(r"^D-\d{3,}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INDEX_ROW_RE = re.compile(r"^\|\s*\[?(D-\d{3,})\]?(?:\(([^)]+)\))?\s*\|")

STATUSES = {"draft", "accepted", "amended", "superseded", "deprecated"}
TYPES = {"cadrage", "closure", "amendement"}
VERDICTS = {"ACCEPTED", "REJECTED", "ACCEPTED-WITH-CAVEAT", "INCONCLUSIVE"}
REQUIRED = ("id", "title", "status", "type", "date")


def parse_frontmatter(text: str) -> dict | None:
    """Lecteur YAML minimal : `cle: valeur`, `cle: []`, listes `- item`."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fm: dict[str, object] = {}
    list_key: str | None = None
    for line in lines[1:]:
        if line.strip() == "---":
            return fm
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and list_key:
            fm[list_key].append(_scalar(item.group(1)))
            continue
        kv = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not kv:
            continue
        key, raw = kv.group(1), kv.group(2)
        raw = re.sub(r"\s+#.*$", "", raw).strip()
        if raw in ("", "[]"):
            fm[key] = []
            list_key = key if raw == "" else None
        else:
            fm[key] = _scalar(raw)
            list_key = None
    return None  # frontmatter jamais refermé


def _scalar(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def check_file(path: Path, errors: list[str]) -> str | None:
    """Vérifie un ADR ; retourne son ID (préfixe filename) si lisible."""
    prefix = ID_PREFIX_RE.match(path.name)
    if not prefix:
        errors.append(f"{path.name}: filename sans préfixe D-NNN- valide")
        return None
    file_id = prefix.group(1)

    fm = parse_frontmatter(path.read_text(encoding="utf-8"))
    if fm is None:
        errors.append(f"{path.name}: frontmatter YAML absent ou non refermé")
        return file_id

    for key in REQUIRED:
        if key not in fm or fm[key] in ("", []):
            errors.append(f"{path.name}: champ requis manquant : {key}")
    if "id" in fm and fm["id"] != file_id:
        errors.append(
            f"{path.name}: id frontmatter ({fm['id']}) != préfixe filename ({file_id})"
        )
    if "status" in fm and fm["status"] not in STATUSES:
        errors.append(f"{path.name}: status invalide : {fm['status']!r}")
    if "date" in fm and not DATE_RE.match(str(fm["date"])):
        errors.append(f"{path.name}: date invalide (attendu AAAA-MM-JJ) : {fm['date']!r}")

    adr_type = fm.get("type")
    if adr_type not in TYPES:
        errors.append(f"{path.name}: type invalide : {adr_type!r}")
        return file_id
    if adr_type == "closure":
        if fm.get("verdict") not in VERDICTS:
            errors.append(f"{path.name}: closure sans verdict valide : {fm.get('verdict')!r}")
    elif "verdict" in fm:
        errors.append(f"{path.name}: verdict interdit pour type={adr_type}")
    if adr_type == "amendement":
        if not ADR_ID_RE.match(str(fm.get("amends", ""))):
            errors.append(f"{path.name}: amendement sans amends D-NNN valide")
    elif "amends" in fm:
        errors.append(f"{path.name}: amends interdit pour type={adr_type}")
    return file_id


def check_index(index_path: Path, files_by_id: dict[str, Path], errors: list[str]) -> None:
    if not index_path.is_file():
        errors.append(f"index introuvable : {index_path}")
        return
    indexed: dict[str, str | None] = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        row = INDEX_ROW_RE.match(line.strip())
        if not row:
            continue
        adr_id, target = row.group(1), row.group(2)
        if adr_id in indexed:
            errors.append(f"index: ID en double dans la table : {adr_id}")
        indexed[adr_id] = target
        if target and not (index_path.parent / target).is_file():
            errors.append(f"index: lien cassé pour {adr_id} : {target}")
    for adr_id in files_by_id:
        if adr_id not in indexed:
            errors.append(f"index: ligne manquante pour {adr_id}")
    for adr_id in indexed:
        if adr_id not in files_by_id:
            errors.append(f"index: ligne {adr_id} sans fichier correspondant")


def check_refs(paths: list[Path], files_by_id: dict[str, Path], errors: list[str]) -> int:
    """Vérifie que les D-NNN cités dans `paths` existent. Retourne le nb de fichiers scannés."""
    scanned = 0
    for root in paths:
        files = sorted(root.rglob("*.md")) if root.is_dir() else [root]
        for path in files:
            scanned += 1
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for ref in REF_RE.findall(line):
                    if ref not in files_by_id:
                        errors.append(
                            f"{path}:{lineno}: référence orpheline {ref} "
                            f"(aucun ADR correspondant)"
                        )
    return scanned


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", default="docs/decisions", type=Path,
                        help="dossier des ADR (défaut : docs/decisions)")
    parser.add_argument("--index", default="README.md",
                        help="index, relatif à --dir (défaut : README.md)")
    parser.add_argument("--refs", nargs="*", default=[], type=Path,
                        help="fichiers/dossiers supplémentaires où vérifier les "
                             "références D-NNN (docs/todo/ et TODO.md sont "
                             "auto-détectés)")
    args = parser.parse_args()

    if not args.dir.is_dir():
        sys.exit(f"erreur : dossier introuvable : {args.dir}")

    errors: list[str] = []
    files_by_id: dict[str, Path] = {}
    for path in sorted(args.dir.glob("D-*.md")):
        if path.name.startswith("_template_"):
            continue
        file_id = check_file(path, errors)
        if file_id is None:
            continue
        if file_id in files_by_id:
            errors.append(
                f"COLLISION {file_id} : {files_by_id[file_id].name} et {path.name} "
                f"(renuméroter le second avant merge — guide §3 Travail concurrent)"
            )
        else:
            files_by_id[file_id] = path

    check_index(args.dir / args.index, files_by_id, errors)

    ref_paths = [p for p in (Path("docs/todo"), Path("TODO.md")) if p.exists()]
    for extra in args.refs:
        if not extra.exists():
            sys.exit(f"erreur : chemin --refs introuvable : {extra}")
        ref_paths.append(extra)
    scanned = check_refs(ref_paths, files_by_id, errors)

    if errors:
        print(f"adr_check : {len(errors)} erreur(s)", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
    refs_note = f", {scanned} fichier(s) de refs" if scanned else ""
    print(f"adr_check : OK ({len(files_by_id)} ADR, index synchronisé{refs_note})")


if __name__ == "__main__":
    main()
