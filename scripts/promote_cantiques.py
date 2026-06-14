#!/usr/bin/env python3
"""Promotion du staging (build/cantiques) vers le corpus versionné.

Première population du corpus (D-001 *migration-scriptee-relue*, D-002
multilinguisme) : copie les YAML validés du staging vers `stock/cantiques/`
(cantiques) et `stock/prieres/` (prières `p####`, dossier séparé — minute Q3
de D-002), puis écrit la worklist de relecture `docs/relecture-corpus.md`
depuis le rapport du convertisseur.

ATTENTION : écrase les fichiers cibles. À lancer pour la PREMIÈRE population
(ou une re-population assumée), PAS après des relectures en place — elles
seraient écrasées. Les doublons (`__doublon`) sont gardés en staging pour
arbitrage humain.

Stdlib uniquement.
"""

from __future__ import annotations

import argparse
import collections
import re
import shutil
import sys
from pathlib import Path


def write_worklist(report: Path, worklist: Path) -> int:
    lines = report.read_text(encoding="utf-8").splitlines() if report.exists() else []
    items: list[str] = []
    for k, l in enumerate(lines):
        if l.startswith("## À relire"):
            items = [x for x in lines[k + 1:] if x.startswith("- ")]
            break

    groups: dict[str, list[tuple[str, str, list[str]]]] = collections.defaultdict(list)
    for l in items:
        left, _, right = l[2:].partition("—")
        m = re.match(r"\s*`([^`]+)`", left)
        numero = m.group(1) if m else left.strip()
        mn = re.search(r"\(([^)]*)\)", left)
        name = mn.group(1) if mn else ""
        # Titre lisible : sans le préfixe numéro ni l'extension .txt.
        name = re.sub(r"^(?:\d+-\d+|Ps\s+\d+[A-Za-z]?|p\d+(?:_\d+)?)[.\s]*", "", name)
        name = name.removesuffix(".txt").strip()
        tags = [t.strip() for t in right.split(",") if t.strip()]
        cat = tags[0] if tags else "?"
        groups[cat].append((numero, name, tags))

    out = [
        "# Relecture du corpus — worklist",
        "",
        "Cantiques signalés par le convertisseur (flags de "
        "`build/cantiques/_rapport.md`), promus en baseline puis à raffiner "
        "en place — D-001 *migration-scriptee-relue*, D-002 multilinguisme.",
        "Comment relire : voir [README.md](../README.md) § « Relecture "
        "incrémentale du corpus ».",
        "",
        "Chaque entrée est **indexée par le numéro** du cantique "
        "(`stock/cantiques/<numero>.yaml`, ou `stock/prieres/` pour les "
        "`p####`). **Cocher la case éteint l'avertissement de `generate.py`** "
        "pour ce cantique.",
        "",
        "> Fichier régénéré par `scripts/promote_cantiques.py` : ne pas "
        "éditer à la main hormis cocher les cases `- [ ]` → `- [x]`.",
        "",
    ]
    for cat in sorted(groups, key=lambda c: -len(groups[c])):
        out.append(f"## {cat} ({len(groups[cat])})")
        out.append("")
        for numero, name, tags in groups[cat]:
            extra = ", ".join(tags[1:])
            desc = f" — {name}" if name else ""
            out.append(f"- [ ] `{numero}`{desc}" + (f" — _{extra}_" if extra else ""))
        out.append("")
    worklist.parent.mkdir(parents=True, exist_ok=True)
    worklist.write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(items)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--src", default="build/cantiques", type=Path)
    p.add_argument("--cantiques", default="stock/cantiques", type=Path)
    p.add_argument("--prieres", default="stock/prieres", type=Path)
    p.add_argument("--report", default="build/cantiques/_rapport.md", type=Path)
    p.add_argument("--worklist", default="docs/relecture-corpus.md", type=Path)
    args = p.parse_args()

    if not args.src.is_dir():
        sys.exit(f"erreur : staging introuvable : {args.src} (lancer convert d'abord)")
    args.cantiques.mkdir(parents=True, exist_ok=True)
    args.prieres.mkdir(parents=True, exist_ok=True)

    n_cant = n_prieres = n_hold = 0
    for f in sorted(args.src.glob("*.yaml")):
        if "__doublon" in f.name:
            n_hold += 1
            continue
        if re.match(r"^p\d", f.name):
            shutil.copy2(f, args.prieres / f.name)
            n_prieres += 1
        else:
            shutil.copy2(f, args.cantiques / f.name)
            n_cant += 1

    n_items = write_worklist(args.report, args.worklist)

    print(f"Cantiques promus : {n_cant} -> {args.cantiques}")
    print(f"Prières promues  : {n_prieres} -> {args.prieres}")
    print(f"Doublons gardés en staging : {n_hold}")
    print(f"Worklist de relecture : {args.worklist} ({n_items} entrées)")


if __name__ == "__main__":
    main()
