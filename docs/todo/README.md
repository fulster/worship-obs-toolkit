# TODO

Registre des chantiers en cours. Les items issus d'une décision
structurante portent le backlink `D-NNN` de leur ADR d'origine
(greppable dans les deux sens). Les TODO sans origine décisionnelle
restent libres.

## Chantiers D-001 — Format source structuré des paroles

Issus des *Conséquences* de [D-001](../decisions/D-001-format-source-structure-paroles.md).
Ordre indicatif : le schéma fonde le reste ; le sélecteur de couplets
(priorité opérateur) dépend du schéma et de la lecture.

- [ ] **Schéma YAML d'un cantique** (`D-001`) — définir les champs
  (`numero`, `titre`, `source`, `credits`, `refrain`, `couplets`),
  la gestion du multi-ligne et l'indexation des couplets, sur 2-3
  exemples réels (dont 12-13).
- [ ] **Convertisseur brut → YAML** (`D-001`) — script
  `stock/txt/à nettoyer` → format propre : normalise `\r\r\n → \r\n`,
  détecte titre / couplets `^N.` / refrain / crédits. Produit un
  **rapport** des fichiers non auto-structurables (~246 attendus).
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
