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
- [ ] **Sélecteur de couplets / modèle d'ordre** (`D-001`) — dans le
  parsing de `chants.txt` / fichier de spontanés (`generate.py`) :
  syntaxe `12-13 : 1,R,3`, ordre respecté, fallback « tout » +
  avertissement si structure absente. *(Priorité opérateur — résout la
  douleur des spontanés-extraits.)*
  - **Deux portées à concevoir ensemble** (décidé en session) :
    1. *défaut par cantique* — ex. refrain chanté **en intro**
       (`R, C1, R, C2…`), trait stable de l'hymne ; à ne PAS oublier en
       repoussant l'intro-refrain ici plutôt qu'en booléen `refrain_intro`
       au schéma ;
    2. *override par culte* — l'ordre exact via le sélecteur `chants.txt`.
    En attendant, le pipeline de lecture applique le défaut « refrain
    après chaque couplet » (sans intro).
- [ ] **Sort de `stock/txt/`** (`D-001`) — décider du devenir des 90
  fichiers nettoyés à la main vs le nouveau corpus YAML (migration,
  coexistence, ou abandon).
