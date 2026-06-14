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
        "`build/cantiques/_rapport.md`), promus « en baseline » puis à raffiner "
        "en place — D-001 *migration-scriptee-relue*, D-002 multilinguisme. "
        "Tous sont valides et projetables ; les signalements pointent une "
        "structure à confirmer, pas un fichier cassé.",
        "",
        "## Comment relire",
        "",
        "1. Prends une entrée **non cochée** ci-dessous : "
        "`` - [ ] `<numero>` — <titre> — _<flags>_ ``.",
        "2. Ouvre `stock/cantiques/<numero>.yaml` (les prières sont dans "
        "`stock/prieres/`). Au besoin, compare au brut "
        "`stock/txt/à nettoyer/`.",
        "3. Vérifie/corrige selon le(s) flag(s) — voir la légende ci-dessous. "
        "Format du fichier : [`docs/format-cantique.md`](format-cantique.md).",
        "4. **Coche la case** (`- [ ]` → `- [x]`) : ça éteint l'avertissement "
        "« à relire » de `generate.py` pour ce cantique.",
        "",
        "## Que vérifier selon le signalement",
        "",
        "| Flag | Ce que ça signifie | À vérifier / corriger |",
        "|---|---|---|",
        "| `non-decoupe` (cat. `sans-couplets`) | Aucune numérotation `N.` "
        "détectée → tout le chant tient dans un seul `couplets:`. | Si le chant "
        "a plusieurs strophes, les **redécouper** en plusieurs entrées de "
        "`couplets:`. Si c'est un chant court (refrain, alléluia), laisser tel "
        "quel. |",
        "| `multilingue` | Une/des traduction(s) ont été isolées dans "
        "`traductions:`. | Vérifier que `couplets:` (français) **ne contient "
        "aucun texte étranger** et que chaque bloc a le bon `langue:`. |",
        "| `langue-indeterminee` | Langue d'une traduction non devinée "
        "(`langue: \"xx\"`). | Mettre le bon code (`en`, `de`…). Si le bloc est "
        "en réalité **du français** (2ᵉ série), le remonter dans `couplets:` et "
        "supprimer le bloc. |",
        "| `renumerotation-sans-entete` | Bloc séparé sur une renumérotation "
        "des couplets, **sans en-tête de langue** (ambigu). | Trancher : vraie "
        "traduction (garder, fixer `langue:`) **ou** suite du français "
        "(fusionner dans `couplets:`). |",
        "| `source-ambigue` | Plusieurs lignes entre titre et 1er couplet mises "
        "dans `source:`. | Vérifier que `source:` **n'a pas avalé des paroles** "
        "; sinon les remettre en `couplets:`. |",
        "| `collision-numero` | Deux bruts portent ce numéro ; le doublon est "
        "resté en staging. | Comparer "
        "`build/cantiques/<numero>__doublon*.yaml` et **garder la bonne "
        "version**. |",
        "| `refrain-vide` | Marqueur de refrain trouvé mais sans texte. | "
        "Renseigner `refrain:` ou retirer le marqueur. |",
        "| `numero-incertain` | Numéro non dérivable du nom de fichier "
        "(typiquement les prières `p####`). | Vérifier/corriger `numero:`. |",
        "",
        "> ⚠️ Fichier **régénéré** par `scripts/promote_cantiques.py` (qui "
        "**écrase** `stock/cantiques/`). Ne **rien** éditer ici à la main "
        "hormis cocher les cases ; et ne relance pas `promote` après des "
        "relectures en place, sous peine de les perdre.",
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
