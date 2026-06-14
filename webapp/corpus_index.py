"""Index en mémoire du corpus de cantiques, pour la recherche côté interface.

Construit une fois au démarrage du serveur (cf. D-003) : parcourt
`stock/cantiques/` (et `stock/prieres/`), extrait les métadonnées utiles à
l'affichage et à la composition, et fournit une recherche par sous-chaîne
insensible à la casse et aux accents.
"""

from __future__ import annotations

import glob
import os
import unicodedata

import yaml


def _norm(s: str) -> str:
    """Minuscule sans accents, pour une recherche tolérante."""
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii')
    return s.lower()


def build_index(cantiques_dir: str, prieres_dir: str, flagged: set | None = None) -> list[dict]:
    """Charge tout le corpus en mémoire. `flagged` = numéros « à relire »."""
    flagged = flagged or set()
    index: list[dict] = []
    for directory, kind in ((cantiques_dir, 'cantique'), (prieres_dir, 'priere')):
        if not directory or not os.path.isdir(directory):
            continue
        for path in sorted(glob.glob(os.path.join(directory, '*.yaml'))):
            try:
                with open(path, encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            numero = (data.get('numero') or '').strip()
            titre = (data.get('titre') or '').strip()
            index.append({
                'numero': numero,
                'titre': titre,
                'source': data.get('source'),
                'n_couplets': len(data.get('couplets') or []),
                'refrain': bool(data.get('refrain')),
                'langues': [t.get('langue') for t in (data.get('traductions') or [])
                            if isinstance(t, dict)],
                'kind': kind,
                'a_relire': numero in flagged,
                '_search': _norm(f"{numero} {titre}"),
            })
    return index


def search(index: list[dict], q: str = '', limit: int = 50) -> list[dict]:
    """Filtre l'index par sous-chaîne (numéro ou titre). Vide => tête de liste."""
    qn = _norm(q).strip()
    items = index if not qn else [e for e in index if qn in e['_search']]
    # Ne pas renvoyer le champ interne de recherche.
    return [{k: v for k, v in e.items() if k != '_search'} for e in items[:limit]]
