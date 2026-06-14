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
  - [x] **Défaut d'ordre par cantique** (`D-001`) — **non retenu**
    (verdict empirique 2026-06-14) : sur les 90 fichiers nettoyés à la
    main, 28 ont un refrain mais **2 seulement ouvrent par le refrain
    (7 %)**. L'intro-refrain est minoritaire → on garde le défaut
    « refrain après chaque couplet, sans intro ». Les rares cas intro se
    font par culte via le sélecteur littéral `(R,1,R,2)`.
- [x] **Sort de `stock/txt/`** (`D-001`) — tranché : **abandon** des 90
  fichiers nettoyés à la main, désormais couverts par le corpus YAML
  (`stock/cantiques/`). Les bruts `stock/txt/à nettoyer/` restent (source
  du convertisseur). Le repli `stock/txt` de `generate.py` devient inerte
  (ne trouve plus rien) — inoffensif.

## Chantiers D-002 — Support multilingue des traductions

Issus des *Conséquences* de
[D-002](../decisions/D-002-support-multilingue-traductions.md). 83/922
fichiers embarquent des traductions (EN/DE) à isoler avant promotion.

- [x] **Schéma `traductions`** (`D-002`) — fait.
  `schemas/cantique.schema.json` : champ optionnel `traductions`, liste
  de `{langue, couplets, refrain?}` (`langue` = `^[a-z]{2,3}$`),
  `additionalProperties: false`. Le FR reste à la racine.
- [x] **Convertisseur multilingue** (`D-002`) — fait.
  `convert_cantiques.py` segmente en blocs de langue (en-tête
  `English`/`Deutsch` + renumérotation), route 1er bloc → `couplets`
  (FR), reste → `traductions` ; détection `en`/`de`, sinon `xx`. Sur les
  922 : **73 multilingues** (43 en, 59 de, 20 xx), 922/922 valides au
  schéma. Flags relecture : `langue-indeterminee`,
  `renumerotation-sans-entete`. Cas FR non numéroté + trad numérotée
  géré (le pré-bloc devient le couplet FR).
- [x] **Pipeline ignore `traductions`** (`D-002`) — fait/vérifié :
  `expand_cantique` ne lit que `couplets`/`refrain`/`source`/`credits`,
  jamais `traductions` → le FR seul est servi (vérifié sur `32-37`). Un
  sélecteur de langue reste un chantier aval hors scope.
- [x] **Promotion du corpus** (`D-002`, `D-001`) — fait via
  `scripts/promote_cantiques.py`. **883 cantiques** → `stock/cantiques/`,
  **38 prières `p####`** → `stock/prieres/` (dossier séparé, minute Q3
  D-002), 1 doublon `32-37` gardé en staging. Corpus 0 invalide au
  schéma. Stratégie « tout en baseline, raffiner en place » : worklist
  des 363 flaggés dans [`docs/relecture-corpus.md`](../relecture-corpus.md).
  - [ ] **Relecture des 363 flaggés** (`D-001`, `D-002`) — raffiner en
    place les fichiers de `docs/relecture-corpus.md` : redécouper les
    `sans-couplets` longs, vérifier les `xx`/`renumerotation-sans-entete`
    (langue), trancher le doublon `32-37`, les `source-ambigue`.

## Chantiers D-003 — Interface de préparation des cultes (app web locale)

Issus des *Conséquences* de
[D-003](../decisions/D-003-interface-de-preparation-des-cultes.md). App
web **locale** (non publique) pour des préparateurs non techniques en
rotation ; réutilise le pipeline ; `.zip` + import (D-001).

- [x] **Rendre `generate.py` appelable** (`D-003`) — fait. Module
  importable sans effet de bord ; cœur extrait en
  `generer_culte(titre, entrees, config, img_*)` (retourne un dict info :
  `zip`, `ajoutes`, `non_trouves`, `a_relire`), avec `resoudre_entrees`,
  `lire_chants_txt`, `telecharger_images`, `main()`. CLI inchangée
  (vérifiée end-to-end).
- [x] **Backend** (`D-003`) — fait. Flask (`webapp/app.py`) : recherche
  corpus (`/api/cantiques`, index en mémoire `webapp/corpus_index.py`),
  génération (`/api/generer` → `generer_culte` → info + lien), CRUD des
  cultes (`/api/cultes`). Lancement : `uv run python webapp/app.py`.
  Testé via `test_client` (recherche, CRUD, génération hors-ligne +
  téléchargement).
- [x] **Frontend** (`D-003`) — fait. `webapp/static/index.html` : Vue 3
  + Tailwind **vendored** (`webapp/static/vendor/`, no-build, offline),
  aesthetic « liturgie moderne » (Fraunces + Hanken Grotesk, parchemin /
  vert sapin / or). Recherche live, ajout, **sélecteur de couplets**
  (chips 1..N + R, champ exact), interrupteur cantique/spontané,
  réordonnancement, sauvegarde/réouverture, « Générer » + téléchargement,
  avertissements « à relire » / introuvables. Endpoint `/api/stats` pour
  le compteur. Rendu vérifié en headless.
- [x] **Sauvegarde des cultes** (`D-003`) — fait (côté backend) :
  `/api/cultes` GET/POST/GET-id/DELETE, stockés en JSON dans
  `webapp/cultes/` (gitignoré). Le frontend les exploitera.
- [x] **Lancement / déploiement local** (`D-003`) — fait.
  - Lancement simple : `Preparer un culte.bat` (serveur + navigateur).
  - **Poste de l'église (appliance)** : `installer-poste-eglise.bat`
    (raccourci Bureau + démarrage auto caché via `.vbs` dans *Démarrage*),
    `serveur.bat` (production **waitress**, `WOTK_PROD=1`),
    `arreter-serveur.bat`, `desinstaller-poste-eglise.bat`. Doc
    [`docs/deploiement.md`](../deploiement.md). Serveur sans debug par
    défaut (`WOTK_DEBUG=1` pour le dev).
- [x] **Push obs-websocket** (`D-003`) — sorti du différé : cadré par
  [D-004](../decisions/D-004-envoi-vers-obs-websocket.md), chantiers
  ci-dessous.

## Chantiers D-004 — Envoi des scènes vers OBS (obs-websocket)

Issus des *Conséquences* de
[D-004](../decisions/D-004-envoi-vers-obs-websocket.md). « Envoyer vers
OBS » **en plus** du `.zip`, par rejeu du JSON généré (collection dédiée).
Faisabilité validée par un spike (`scripts/spike_obs.py`, OBS 30.1).

- [x] **Dépendance `obsws-python`** (`D-004`) — fait.
- [x] **Traducteur `JSON de collection → obs-websocket`** (`D-004`) — fait.
  `obs_push.push_collection(coll, host, port, password, name)` : crée une
  collection dédiée (nom unique), rejoue sources / scènes / items +
  transformations (`bounds_type` → enum) / filtres, ordonne, retire la
  scène par défaut. **Validé en direct** (OBS 30.1) : 7 scènes ordonnées,
  items + `scroll_filter`/`gpu_delay` + transformations fidèles.
- [x] **Endpoint `/api/envoyer-obs`** (`D-004`) — fait. `construire_collection`
  (extrait de `generer_culte`) → `obs_push.push_collection` ; renvoie
  collection / scènes / ajoutés / non trouvés. Erreurs : OBS désactivé (400),
  injoignable (502). **Validé en direct** (collection « Test envoi OBS direct »,
  7 scènes).
- [x] **UI « Envoyer vers OBS »** (`D-004`) — fait. Bouton à côté de
  « Générer le .zip » ; panneau de résultat adaptatif (« Envoyé dans OBS —
  collection … » sans téléchargement) ; erreur affichée si OBS injoignable.
- [x] **Config `obs` + doc** (`D-004`) — fait. Section `obs`
  (enabled/host/port/password) dans `config.json.example` (défauts =
  localhost:4455 sans auth) ; activation du serveur WebSocket OBS documentée
  dans [`docs/deploiement.md`](../deploiement.md).
