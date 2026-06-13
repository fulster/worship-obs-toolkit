# TODO

Registre des chantiers en cours. Les items issus d'une décision
structurante portent le backlink `D-NNN` de leur ADR d'origine
(greppable dans les deux sens). Les TODO sans origine décisionnelle
restent libres.

## Chantiers D-001 — Format source structuré des paroles

Issus des *Conséquences* de [D-001](../decisions/D-001-format-source-structure-paroles.md).
Ordre indicatif : le schéma fonde le reste ; le sélecteur de couplets
(priorité opérateur) dépend du schéma et de la lecture.

- [x] **Schéma YAML d'un cantique** (`D-001`) — fait. Spec
  [`docs/format-cantique.md`](../format-cantique.md), schéma de
  validation [`schemas/cantique.schema.json`](../../schemas/cantique.schema.json),
  3 fixtures de référence sous `stock/cantiques/` (12-13, Ps 008, 13-03)
  validées contre le schéma.
- [x] **Convertisseur brut → YAML** (`D-001`) — fait.
  [`scripts/convert_cantiques.py`](../../scripts/convert_cantiques.py) :
  normalise `\r\r\n → \r\n`, découpe par sections (marqueurs `N.` /
  `(Refrain)`), gère refrain-seul et collisions de numero, écrit dans le
  staging gitignoré `build/cantiques/` + `_rapport.md`. Sur les 922 :
  **677 structurés** (126 refrain, 549 sans-refrain, 2 refrain-seul),
  **245 sans-couplets** à découper à la main, 922/922 valides au schéma.
  - [ ] **Relecture des 293 cas signalés** (`D-001`) — promouvoir les
    YAML corrects de `build/cantiques/` vers `stock/cantiques/` ;
    re-découper les 245 sans-couplets ; trancher la normalisation
    apostrophes `’→'` et `(c)→©` (polish de corpus).
- [ ] **Pipeline de lecture** (`D-001`) — adapter `Scene`
  (`obs_json_resources.py`) pour consommer le format structuré et
  **expanser le refrain** après chaque couplet (remplace le nettoyage
  manuel).
- [ ] **Sélecteur de couplets** (`D-001`) — dans le parsing de
  `chants.txt` / fichier de spontanés (`generate.py`) : syntaxe
  `12-13 : 1,R,3`, ordre respecté, fallback « tout » + avertissement si
  structure absente. *(Priorité opérateur — résout la douleur des
  spontanés-extraits.)*
- [ ] **Sort de `stock/txt/`** (`D-001`) — décider du devenir des 90
  fichiers nettoyés à la main vs le nouveau corpus YAML (migration,
  coexistence, ou abandon).
