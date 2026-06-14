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
- [x] **Pipeline de lecture** (`D-001`) — fait. `Scene`
  (`obs_json_resources.py`) dispatche sur l'extension : `.yaml` →
  `load_cantique_yaml` + `expand_cantique` (refrain **expansé après
  chaque couplet**, le code remplace le nettoyage manuel) ; `.txt` →
  comportement historique inchangé. `generate.py` résout d'abord
  `stock/cantiques/<numero>.yaml`, repli sur `stock/txt/`. Dépendance
  runtime `pyyaml`. Le sélecteur de couplets (3ᵉ ligne du head
  `numero\ntitre`) reste le chantier suivant.
- [x] **Sélecteur de couplets (override par culte)** (`D-001`) — fait.
  `generate.py` lit un sélecteur `(...)` en fin de ligne (notation déjà
  en usage). Mode A : chiffres seuls (`(1,3)`) → couplets choisis,
  refrain réinséré après chaque ; mode littéral : avec `R` (`(1,R,3)`,
  `(R,1,R,2)`) → séquence exacte. Hors-limites / `R` sans refrain /
  sélecteur sur `.txt` → ignorés avec avertissement. Résolution dans
  `expand_cantique` / `parse_selection` (`obs_json_resources.py`).
  *(Résout la douleur des spontanés-extraits.)*
  - [ ] **Défaut d'ordre par cantique** (`D-001`) — reste à faire :
    qu'un cantique déclare son refrain **en intro** par défaut (sans
    avoir à écrire `R` à chaque culte). À concevoir comme un trait de la
    source (champ schéma), composé avec l'override par culte ci-dessus.
    En attendant, sans `R` explicite, le défaut est « refrain après
    chaque couplet, sans intro ».
- [ ] **Sort de `stock/txt/`** (`D-001`) — décider du devenir des 90
  fichiers nettoyés à la main vs le nouveau corpus YAML (migration,
  coexistence, ou abandon).
