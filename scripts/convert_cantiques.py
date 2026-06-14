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

# Multilinguisme (D-002) : en-tête de langue + détection par mots-outils.
LANG_HEADER_RE = re.compile(
    r"^\(?\s*(english|anglais|deutsch|allemand|german|latin|"
    r"néerlandais|neerlandais|espagnol|italien)\s*\)?\s*:?\s*$",
    re.IGNORECASE,
)
LANG_CODE = {
    "english": "en", "anglais": "en",
    "deutsch": "de", "allemand": "de", "german": "de",
    "latin": "la", "néerlandais": "nl", "neerlandais": "nl",
    "espagnol": "es", "italien": "it",
}
_FR_WORDS = set(
    "le la les de des du et un une est dans tu je nous vous ton ta tes son sa ses qui "
    "que pour avec sur au aux ne pas plus mon ma mes notre votre seigneur dieu christ "
    "esprit gloire vie il elle ce ces tout tous toi".split()
)
_EN_WORDS = set(
    "the and you your are with his her our we is of to in for that this be he she they "
    "them lord shall will come holy all my me name god praise sing king love grace "
    "heaven earth let now from have thy thee thou".split()
)
_DE_WORDS = set(
    "der die das und ich du ist nicht mit ein eine wir ihr herr gott dein sein zu den "
    "dem auf von wie so auch nur noch wenn dass durch über uns mein dich".split()
)


def detect_lang(text: str) -> str | None:
    """Détecte fr/en/de par mots-outils ; None si indéterminé."""
    words = re.findall(r"[a-zà-ÿ']+", text.lower())
    if not words:
        return None
    score = {"fr": 0, "en": 0, "de": 0}
    for w in words:
        if w in _FR_WORDS:
            score["fr"] += 1
        if w in _EN_WORDS:
            score["en"] += 1
        if w in _DE_WORDS:
            score["de"] += 1
    lang = max(score, key=score.get)
    if score[lang] == 0 or score[lang] / len(words) < 0.10:
        return None
    return lang


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

    # Marqueurs structurels (couplets, refrains, en-têtes de langue), dans
    # l'ordre du texte. Les bruts sont double-interlignés : on délimite par
    # marqueurs, pas par lignes vides, et on ignore les vides dans une section.
    markers = []  # (pos, kind, payload) ; kind = couplet|refrain|header
    for i, ln in enumerate(body):
        s = ln.strip()
        mc = COUPLET_RE.match(s)
        if mc:
            markers.append((i, "couplet", int(mc.group(1))))
            continue
        if REFRAIN_MARK_RE.match(s):
            markers.append((i, "refrain", None))
            continue
        mh = LANG_HEADER_RE.match(s)
        if mh:
            markers.append((i, "header", LANG_CODE.get(mh.group(1).lower(), "xx")))

    def section(start: int, end: int, is_couplet: bool) -> list[str]:
        """Lignes non vides de [start, end[, hors marqueurs refrain/Refr/langue."""
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
            if REFRAIN_MARK_RE.match(ln.strip()) or LANG_HEADER_RE.match(ln.strip()):
                continue
            if re.fullmatch(r"\s*[Rr]efr(?:\.|ain)?\.?\s*", ln):
                continue
            out.append(ln.rstrip())
        return out

    source = None
    refrain = None
    couplets: list[str] = []
    traductions: list[dict] = []

    has_structural = any(k in ("couplet", "refrain") for _, k, _ in markers)
    if not has_structural:
        # Aucune numérotation : tout le corps utile en un couplet unique.
        # (un en-tête de langue seul ne structure rien.)
        block = section(0, len(body), is_couplet=False)
        if block:
            block[-1] = REFR_TRAILER_RE.sub("", block[-1])
            text = "\n".join(block).strip()
            if text:
                couplets.append(text)
        category = "sans-couplets"
        flags.append("non-decoupe")
    else:
        # Pré-bloc = lignes non vides entre le titre et le 1er marqueur (source
        # courte, OU paroles FR non numérotées si seule la trad est numérotée —
        # tranché après segmentation).
        pre = [ln.strip() for ln in body[: markers[0][0]] if ln.strip()]

        # Segmentation en blocs de langue (D-002). Le 1er bloc est le français ;
        # un en-tête de langue OU une renumérotation des couplets (n° qui
        # redescend) ouvre un bloc de traduction.
        blocks = [{"lang": "fr", "couplets": [], "refrain": None}]
        last_num = 0
        positions = [m[0] for m in markers] + [len(body)]
        for k, (pos, kind, payload) in enumerate(markers):
            end = positions[k + 1]
            if kind == "header":
                blocks.append({"lang": payload, "couplets": [], "refrain": None})
                last_num = 0
                continue
            if kind == "refrain":
                rtext = "\n".join(section(pos + 1, end, False)).strip() or None
                if blocks[-1]["refrain"] is None:
                    blocks[-1]["refrain"] = rtext
                continue
            # couplet
            if payload <= last_num and blocks[-1]["couplets"]:
                blocks.append({"lang": None, "couplets": [], "refrain": None})
            last_num = payload
            seg = section(pos, end, is_couplet=True)
            if seg:
                seg[-1] = REFR_TRAILER_RE.sub("", seg[-1])
            text = "\n".join(seg).strip()
            if text:
                blocks[-1]["couplets"].append(text)

        # Bloc 0 = français (racine).
        fr = blocks[0]
        refrain = fr["refrain"]
        if not fr["couplets"] and pre:
            # Seule la traduction était numérotée : le pré-bloc EST le couplet FR.
            couplets = ["\n".join(pre)]
            flags.append("non-decoupe")
        else:
            couplets = fr["couplets"]
            if len(pre) == 1:
                source = pre[0]
            elif len(pre) > 1:
                source = " ".join(pre)
                flags.append("source-ambigue")
        if refrain is None and any(m[1] == "refrain" for m in markers) and not blocks[1:]:
            flags.append("refrain-vide")

        # Blocs suivants = traductions. En-tête de langue = fiable ; bloc ouvert
        # par renumérotation seule = ambigu (2e série FR ? traduction sans
        # en-tête ?) → flag relecture. Une traduction n'est jamais « fr » : un
        # fr détecté sur un slot traduction est suspect (cf. italien lu comme fr)
        # → 'xx'.
        for b in blocks[1:]:
            if not b["couplets"]:
                continue
            lang = b["lang"]
            if lang is None:
                flags.append("renumerotation-sans-entete")
                d = detect_lang("\n".join(b["couplets"]))
                lang = d if d in ("en", "de") else "xx"
            elif lang == "xx":
                d = detect_lang("\n".join(b["couplets"]))
                lang = d if d in ("en", "de") else "xx"
            t = {"langue": lang, "couplets": b["couplets"]}
            if b["refrain"]:
                t["refrain"] = b["refrain"]
            traductions.append(t)
            if lang == "xx":
                flags.append("langue-indeterminee")
        if traductions:
            flags.append("multilingue")

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
    if traductions:
        cantique["traductions"] = traductions
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
    if c.get("traductions"):
        lines.append("traductions:")
        for t in c["traductions"]:
            lines.append(f"  - langue: {_dq(t['langue'])}")
            if t.get("refrain"):
                lines.append("    refrain: " + _block(t["refrain"], "      "))
            lines.append("    couplets:")
            for cp in t["couplets"]:
                lines.append("      - " + _block(cp, "        "))
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
