#!/usr/bin/env python3
"""Convertit les cantiques bruts (texte) vers le format YAML structuré (D-001).

Usage :
    python scripts/convert_cantiques.py
    python scripts/convert_cantiques.py --src "stock/txt/à nettoyer" --out build/cantiques

Pour chaque `.txt` du dossier source, le script :
  1. normalise les fins de ligne (`\\r\\r\\n` / `\\r\\n` / `\\r` -> `\\n`) ;
  2. dérive `numero` du nom de fichier (cantique `NN-NN`, psaume `Ps 0NN`) ;
  3. extrait `titre`, `source`, `refrain`, `couplets`, `credits` ;
  4. écrit `<numero>.yaml` dans --out et accumule un rapport de qualité.

Stratégie « script + relecture » (D-001, axe 4) : la sortie atterrit dans
un dossier de staging (défaut `build/cantiques/`, gitignoré), JAMAIS
directement dans `stock/cantiques/`. La relecture humaine promeut ensuite
les fichiers corrects. Le rapport liste les cas à relire.

Stdlib uniquement. L'écriture YAML est faite à la main (scalaires
double-quote + blocs littéraux `|`) — pas de dépendance runtime.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --- Détection des structures -------------------------------------------------

COUPLET_RE = re.compile(r"^(\d+)\.\s*(.*)$")
REFRAIN_MARK_RE = re.compile(r"^\(?\s*refrain\s*\)?\s*:?\s*$", re.IGNORECASE)
# Trailer de fin de couplet : « Refr. », « Refrain », « Refr », « R. »…
REFR_TRAILER_RE = re.compile(r"\s*\b[Rr]efr(?:\.|ain)?\.?\s*$")
NUM_CANTIQUE_RE = re.compile(r"^(\d+-\d+)")
NUM_PSAUME_RE = re.compile(r"^Ps\s+0*(\d+)([A-Za-z]?)", re.IGNORECASE)
TITLE_PREFIX_RE = re.compile(r"^(?:\d+-\d+|Ps\s+\d+[A-Za-z]?)[.\s]*", re.IGNORECASE)
CREDIT_HINT_RE = re.compile(
    r"©|\(c\)|secli|air libre|olivétan|olivetan|fédération|federation|"
    r"fondation|auteur|\b1[5-9]\d\d\b|\b20\d\d\b",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    """Collapse toute séquence de CR avant LF, puis les CR isolés, en un LF."""
    text = text.lstrip("﻿")
    text = re.sub(r"\r+\n", "\n", text)
    text = re.sub(r"\r", "\n", text)
    return text


def derive_numero(stem: str) -> tuple[str, bool]:
    """(numero, sûr ?) à partir du nom de fichier (sans extension)."""
    m = NUM_CANTIQUE_RE.match(stem)
    if m:
        return m.group(1), True
    m = NUM_PSAUME_RE.match(stem)
    if m:
        return f"Ps {int(m.group(1)):03d}{m.group(2).upper()}", True
    # Repli : slug brut, à corriger en relecture.
    return stem.split(".")[0].strip(), False


def peel_credits(lines: list[str]) -> tuple[list[str], str | None]:
    """Détache les lignes de crédits en fin de corps (©, (c), SECLI, années…)."""
    credits: list[str] = []
    body = lines[:]
    while body:
        # Ignorer les lignes vides de queue.
        if not body[-1].strip():
            body.pop()
            continue
        if CREDIT_HINT_RE.search(body[-1]):
            credits.insert(0, body.pop().strip())
        else:
            break
    return body, (" — ".join(credits) if credits else None)


def parse_cantique(raw: str, stem: str) -> tuple[dict, str, list[str]]:
    """Retourne (cantique, catégorie, flags)."""
    flags: list[str] = []
    numero, sure = derive_numero(stem)
    if not sure:
        flags.append("numero-incertain")

    lines = [ln.rstrip() for ln in normalize(raw).split("\n")]
    # Titre = première ligne non vide.
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    title_line = lines[idx].strip() if idx < len(lines) else stem
    titre = TITLE_PREFIX_RE.sub("", title_line).strip() or title_line
    body = lines[idx + 1 :]

    # Détacher les crédits de la fin.
    body, credits = peel_credits(body)

    # Marqueurs structurels (refrain + couplets), dans l'ordre du texte. Les
    # bruts sont double-interlignés : on délimite par marqueurs, pas par lignes
    # vides, et on ignore les vides à l'intérieur d'une section.
    refrain_idx = next(
        (i for i, ln in enumerate(body) if REFRAIN_MARK_RE.match(ln.strip())), None
    )
    couplet_idxs = [i for i, ln in enumerate(body) if COUPLET_RE.match(ln.strip())]
    markers = sorted(
        ([("refrain", refrain_idx)] if refrain_idx is not None else [])
        + [("couplet", i) for i in couplet_idxs],
        key=lambda m: m[1],
    )

    def section(start: int, end: int, is_couplet: bool) -> list[str]:
        """Lignes non vides de [start, end[, hors marqueurs refrain/Refr."""
        out: list[str] = []
        for j in range(start, end):
            ln = body[j]
            if j == start and is_couplet:
                m = COUPLET_RE.match(ln.strip())
                if m and m.group(2).strip():
                    out.append(m.group(2).strip())
                continue
            if not ln.strip():
                continue
            if REFRAIN_MARK_RE.match(ln.strip()):
                continue
            if re.fullmatch(r"\s*[Rr]efr(?:\.|ain)?\.?\s*", ln):
                continue
            out.append(ln.rstrip())
        return out

    source = None
    refrain = None
    couplets: list[str] = []

    if not markers:
        # Aucune numérotation : tout le corps utile en un couplet unique.
        block = section(0, len(body), is_couplet=False)
        if block:
            block[-1] = REFR_TRAILER_RE.sub("", block[-1])
            text = "\n".join(block).strip()
            if text:
                couplets.append(text)
        category = "sans-couplets"
        flags.append("non-decoupe")
    else:
        # Source = bloc non vide entre le titre et le 1er marqueur.
        pre = [ln.strip() for ln in body[: markers[0][1]] if ln.strip()]
        if len(pre) == 1:
            source = pre[0]
        elif len(pre) > 1:
            source = " ".join(pre)
            flags.append("source-ambigue")

        bounds = [m[1] for m in markers] + [len(body)]
        for k, (kind, start) in enumerate(markers):
            end = bounds[k + 1]
            if kind == "refrain":
                refrain = "\n".join(section(start + 1, end, False)).strip() or None
                if refrain is None:
                    flags.append("refrain-vide")
            else:
                seg = section(start, end, is_couplet=True)
                if seg:
                    seg[-1] = REFR_TRAILER_RE.sub("", seg[-1])
                text = "\n".join(seg).strip()
                if text:
                    couplets.append(text)
        if not couplets and refrain:
            # Chant « refrain seul » (chœur court sans couplet) : le refrain
            # devient l'unique couplet.
            couplets = [refrain]
            refrain = None
            flags.append("refrain-seul")
            category = "refrain-seul"
        else:
            category = "ok-refrain" if refrain else "ok-sans-refrain"

    if not couplets:
        flags.append("aucun-couplet")
        category = "vide"

    cantique = {"numero": numero, "titre": titre}
    if source:
        cantique["source"] = source
    if refrain:
        cantique["refrain"] = refrain
    cantique["couplets"] = couplets
    if credits:
        cantique["credits"] = credits
    return cantique, category, flags


# --- Écriture YAML ------------------------------------------------------------

def _dq(value: str) -> str:
    """Scalaire YAML double-quoted."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _block(value: str, indent: str) -> str:
    """Bloc littéral `|` ; chaque ligne préfixée de `indent`."""
    out = ["|"]
    for line in value.split("\n"):
        out.append(f"{indent}{line}" if line else "")
    return "\n".join(out)


def to_yaml(c: dict) -> str:
    lines = [f"numero: {_dq(c['numero'])}", f"titre: {_dq(c['titre'])}"]
    if "source" in c:
        lines.append(f"source: {_dq(c['source'])}")
    if "refrain" in c:
        lines.append("refrain: " + _block(c["refrain"], "  "))
    lines.append("couplets:")
    for cp in c["couplets"]:
        lines.append("  - " + _block(cp, "    "))
    if "credits" in c:
        lines.append(f"credits: {_dq(c['credits'])}")
    return "\n".join(lines) + "\n"


# --- Pilote -------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--src", default="stock/txt/à nettoyer", type=Path)
    parser.add_argument("--out", default="build/cantiques", type=Path)
    parser.add_argument("--report", default="build/cantiques/_rapport.md", type=Path)
    args = parser.parse_args()

    if not args.src.is_dir():
        sys.exit(f"erreur : dossier source introuvable : {args.src}")
    args.out.mkdir(parents=True, exist_ok=True)

    files = sorted(args.src.glob("*.txt"))
    if not files:
        sys.exit(f"erreur : aucun .txt dans {args.src}")

    # Repartir propre : purger les .yaml d'une exécution précédente.
    for stale in args.out.glob("*.yaml"):
        stale.unlink()

    counts: dict[str, int] = {}
    to_review: list[tuple[str, list[str]]] = []
    used: dict[str, int] = {}
    written = 0
    for path in files:
        try:
            raw = path.read_text(encoding="utf-8")
            cantique, category, flags = parse_cantique(raw, path.stem)
            numero = cantique["numero"]
            if numero in used:
                # Doublon de numero dans le corpus : ne pas écraser, suffixer.
                used[numero] += 1
                fname = f"{numero}__doublon{used[numero]}"
                flags.append("collision-numero")
            else:
                used[numero] = 1
                fname = numero
            (args.out / f"{fname}.yaml").write_text(
                to_yaml(cantique), encoding="utf-8"
            )
            written += 1
        except Exception as exc:  # noqa: BLE001
            category, flags = "erreur", [str(exc)]
        counts[category] = counts.get(category, 0) + 1
        if category not in ("ok-refrain", "ok-sans-refrain") or flags:
            to_review.append((path.name, [category, *flags]))

    # Rapport.
    args.report.parent.mkdir(parents=True, exist_ok=True)
    rep = ["# Rapport de conversion des cantiques", "", f"{written} fichier(s) écrit(s).", ""]
    rep.append("## Répartition")
    rep.append("")
    for cat in sorted(counts):
        rep.append(f"- `{cat}` : {counts[cat]}")
    rep.append("")
    rep.append(f"## À relire ({len(to_review)})")
    rep.append("")
    for name, tags in to_review:
        rep.append(f"- `{name}` — {', '.join(tags)}")
    args.report.write_text("\n".join(rep) + "\n", encoding="utf-8")

    print(f"Écrits : {written}/{len(files)} dans {args.out}")
    for cat in sorted(counts):
        print(f"  {cat:18} {counts[cat]}")
    print(f"À relire : {len(to_review)} (détail : {args.report})")


if __name__ == "__main__":
    main()
