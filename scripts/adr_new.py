#!/usr/bin/env python3
"""Scaffolde un nouvel ADR à partir d'un template.

Usage :
    python scripts/adr_new.py cadrage "Choix du cache applicatif"
    python scripts/adr_new.py closure "Verdict benchmark pagination" --dir docs/decisions
    python scripts/adr_new.py amendement "Amendement D-001 TTL cache"

Le script :
  1. trouve le prochain identifiant libre D-NNN dans le dossier cible
     (max existant + 1 — les gaps sont préservés, jamais comblés) ;
  2. copie le template du type demandé (_template_<type>.md, attendu
     dans le dossier cible) ;
  3. pré-remplit le frontmatter : id, date du jour, title.

Le reste (contexte, axes, conditions, minutes de décision, ligne dans
l'index README.md) reste à rédiger — voir adr-guide.md.

Stdlib uniquement. Ne réécrit jamais un fichier existant.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
import unicodedata
from pathlib import Path

TYPES = ("cadrage", "closure", "amendement")
ID_RE = re.compile(r"^D-(\d+)-")


def slugify(title: str, max_words: int = 6) -> str:
    """'Choix du cache applicatif' -> 'choix-du-cache-applicatif'."""
    ascii_title = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    )
    words = re.findall(r"[a-z0-9]+", ascii_title.lower())
    if not words:
        sys.exit(f"erreur : impossible de dériver un slug de {title!r}")
    return "-".join(words[:max_words])


def next_id(decisions_dir: Path) -> int:
    numbers = [
        int(m.group(1))
        for f in decisions_dir.glob("D-*.md")
        if (m := ID_RE.match(f.name))
    ]
    return max(numbers, default=0) + 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("type", choices=TYPES, help="type d'ADR")
    parser.add_argument("title", help="titre lisible humain (sert aussi au slug)")
    parser.add_argument(
        "--dir",
        default="docs/decisions",
        type=Path,
        help="dossier des ADR (défaut : docs/decisions)",
    )
    args = parser.parse_args()

    template = args.dir / f"_template_{args.type}.md"
    if not template.is_file():
        sys.exit(f"erreur : template introuvable : {template}")

    adr_id = f"D-{next_id(args.dir):03d}"
    target = args.dir / f"{adr_id}-{slugify(args.title)}.md"
    if target.exists():
        sys.exit(f"erreur : {target} existe déjà")

    today = datetime.date.today().isoformat()
    content = template.read_text(encoding="utf-8")
    content = content.replace("id: D-XXX", f"id: {adr_id}")
    content = content.replace("date: AAAA-MM-JJ", f"date: {today}")
    # échappement YAML double-quoted ; lambda pour neutraliser les \ dans re.sub
    yaml_title = args.title.replace("\\", "\\\\").replace('"', '\\"')
    content = re.sub(
        r"^title: .*$", lambda _: f'title: "{yaml_title}"', content, count=1, flags=re.M
    )

    target.write_text(content, encoding="utf-8")
    print(f"créé : {target}")
    print("reste à faire :")
    print("  - rédiger le contenu (contexte, axes, conditions, minutes)")
    if args.type == "amendement":
        print("  - renseigner amends: D-YYY et mettre à jour le frontmatter")
        print("    de D-YYY (amended_by, status: amended) au même commit")
    if args.type == "closure":
        print("  - renseigner verdict: (ACCEPTED | REJECTED | ...)")
    print(f"  - ajouter la ligne {adr_id} dans {args.dir}/README.md (même commit)")


if __name__ == "__main__":
    main()
