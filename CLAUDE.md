# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Vue d'ensemble

`worship-obs-toolkit` génère une **collection de scènes OBS Studio** (fichier `.zip` : JSON + images)
à partir d'une liste de cantiques (`chants.txt`), pour projeter les paroles pendant un culte. Une
scène OBS est produite par cantique, plus une scène d'accueil et une scène d'envoi.

Les paroles proviennent d'un **corpus source structuré au format YAML** (`stock/cantiques/`, un
fichier par cantique : couplets et refrain comme champs distincts), acté par les ADR
[D-001](docs/decisions/D-001-format-source-structure-paroles.md) (format structuré) et
[D-002](docs/decisions/D-002-support-multilingue-traductions.md) (traductions). Le code expanse le
refrain et sélectionne les couplets ; voir [`docs/format-cantique.md`](docs/format-cantique.md).

Le projet est en **français** (code, commentaires, docs, messages) — conservez cette langue.

## Commandes

```bash
uv sync                                              # crée .venv et installe les dépendances
uv run python generate.py "Culte du 15 juin"         # génère le .zip OBS
uv run python generate.py "Culte de Noël" --theme "winter,snow,light"   # thème d'images Unsplash

# Corpus des paroles (rarement relancé : le corpus est déjà peuplé)
uv run python scripts/convert_cantiques.py           # bruts stock/txt/à nettoyer/ → build/cantiques/ (staging)
uv run python scripts/promote_cantiques.py           # staging → stock/cantiques/ + stock/prieres/ (ÉCRASE)

python scripts/adr_check.py                          # valide les ADR (voir « ADR » ci-dessous)
python scripts/adr_new.py cadrage "Titre"            # scaffolde un nouvel ADR
```

Dépendances runtime : `requests` (Unsplash) et `pyyaml` (lecture du corpus). `convert_cantiques.py`
et `promote_cantiques.py` sont **stdlib seule**. Le convertisseur écrit dans le staging gitignoré
`build/cantiques/` + un `_rapport.md` ; `promote_cantiques.py` **écrase** les cibles — à lancer pour
peupler, pas après des relectures en place.

Il n'y a **pas de suite de tests ni de linter** configurés. La seule vérification automatisée est
`scripts/adr_check.py` (CI GitHub Actions `.github/workflows/adr-check.yml`, déclenchée uniquement
sur les changements dans `docs/decisions/**` ou le script lui-même).

Avant la première exécution : copier `config.json.example` → `config.json` et renseigner la clé API
Unsplash. **`config.json` est gitignoré** (il contient la clé API) — ne jamais le committer.

## Architecture

Deux modules au cœur du pipeline :

- **`generate.py`** — point d'entrée procédural (s'exécute au niveau module, pas de `main()`). Il :
  lit `config.json` ; télécharge 2 images de fond via l'API Unsplash ; parse `chants.txt` (numéro +
  sélecteur `(...)` éventuel) ; pour chaque ligne, résout `stock/cantiques/<numero>.yaml` **d'abord**
  (repli sur une recherche par sous-chaîne dans `stock/txt/`, aujourd'hui inerte) ; construit la
  collection ; sérialise en JSON et zippe avec les images dans `paths.output`.
- **`obs_json_resources.py`** — modèle objet OBS. Chaque classe hérite de `Obs_basic`, qui charge un
  template JSON depuis `tpl/<NomDeClasse>.json` et y injecte `name` (et `settings.text` ou
  `settings.file` selon le type). Une `Scene` dispatche sur l'extension du fichier : `.yaml` →
  `load_cantique_yaml` + `expand_cantique` (titre = `numero\ntitre`, paroles = un bloc unique pour le
  texte défilant, **refrain expansé après chaque couplet**, traductions **non servies**) ; `.txt` →
  comportement historique (1re ligne = titre, reste = paroles). `expand_cantique(data, selection)`
  applique un sélecteur de couplets ; `parse_selection` parse le `(...)`. `Scene_Collection` agrège
  sources et scènes ; `Tmp_scene` sert aux scènes accueil/envoi (image + texte).

Le flux JSON OBS est entièrement piloté par les **templates de `tpl/`** : pour modifier l'apparence
des scènes générées (police, position, taille, couleurs…), on édite ces JSON, pas le code Python.

### Pièges à connaître

- **Casse des templates** : `Obs_basic` résout `tpl/` + `self.__class__.__name__` + `.json`. Les
  noms de classes sont capitalisés (`Cantique_lyrics_item`) mais les fichiers sont en minuscules
  (`cantique_lyrics_item.json`). Cela ne fonctionne que sur un **système de fichiers insensible à la
  casse (Windows)** ; sous Linux le chargement échouerait. En tenir compte avant tout renommage ou
  exécution cross-platform.
- **`generate.py` réécrit `config.json`** à chaque exécution réussie, en y stockant les noms des
  images téléchargées (`images.accueil` / `images.envoi`).
- **Ordre des scènes** : `chants_list` est inversé (`.reverse()`) avant traitement pour que les
  scènes apparaissent dans OBS dans le même ordre que `chants.txt`.
- **Arborescence `stock/`** : `stock/cantiques/` (corpus YAML, source des paroles, résolu par
  numéro) et `stock/prieres/` (38 prières liturgiques `p####`, dossier séparé — minute Q3 de D-002)
  sont les dossiers vivants. `stock/txt/à nettoyer/` = les **922 bruts** (entrée du convertisseur,
  conservés) ; la racine `stock/txt/` est désormais **vide** (les 90 `.txt` nettoyés à la main ont
  été retirés, couverts par le corpus YAML). `stock/doc/` et `stock/arc/` = archives non utilisées.
  La relecture incrémentale du corpus se suit dans [`docs/relecture-corpus.md`](docs/relecture-corpus.md).

### Format de `chants.txt`

Une entrée par ligne ; lignes vides et lignes `#` ignorées. Résolution des numéros :

- **Cantiques** : préfixe `NN-NN` (ex. `21-17`) → `stock/cantiques/NN-NN.yaml`.
- **Psaumes** : `Psaume X` ou `Ps X` (suffixe lettre accepté, ex. `Ps 34A`) → normalisé en `Ps 0NN`
  → `stock/cantiques/Ps 0NN.yaml`.
- **Sélecteur de couplets** : un `(...)` en **fin de ligne** choisit/réordonne les couplets
  (ex. `22-04 « … » (1,2,3)`). Chiffres seuls → couplets retenus, **refrain réinséré après chaque** ;
  avec un `R` → séquence **littérale** (`(1,R,3)`, `(R,1,R,2)`). Hors-limites / `R` sans refrain /
  sélecteur sur cantique non structuré → ignorés avec avertissement. Détail :
  [`docs/format-cantique.md`](docs/format-cantique.md).
- **Spontanés** : si la 1re ligne est `[SPONTANES] XXX`, le fichier `[SPONTANES] XXX.txt` (racine)
  est chargé et ses chants sont **entrelacés** avec ceux de `chants.txt` : chaque marqueur `#n` du
  fichier de spontanés est remplacé par le cantique suivant de la liste principale.

# Snippet à coller dans les instructions IA du repo consommateur

Bloc destiné au `CLAUDE.md` (ou `.cursorrules`, ou tout fichier
d'instructions d'agent) d'un repo qui adopte la convention ADR.
Adaptez les chemins si votre guide/index vivent ailleurs.

---

## Décisions structurantes (ADR)

Les décisions structurantes du repo sont tracées en ADR sous
`docs/decisions/` : un fichier `D-NNN-<kebab-titre>.md` par décision,
frontmatter YAML obligatoire.

- **Index** : `docs/decisions/README.md` — à lire pour savoir ce qui
  est déjà acté, et à mettre à jour au même commit que tout nouvel ADR.
- **Méthodologie** : `docs/decisions/adr-guide.md` — quand ouvrir un
  ADR, workflows de création et d'amendement, anti-patterns. À lire
  avant d'ouvrir ou d'amender un ADR.
- **Templates** : `docs/decisions/_template_{cadrage,closure,amendement}.md`.
  Tout nouvel ADR part d'un de ces 3 templates, jamais d'un format
  ad-hoc.

Règles non négociables :

- **Jamais renuméroter** un ADR ; les gaps de numérotation sont
  acceptés. Prochain ID = max existant + 1.
- **Jamais réécrire le corps d'un ADR publié.** Pour le modifier :
  ADR d'amendement (`type: amendement`, `amends: D-YYY`) + mise à jour
  du frontmatter de D-YYY (`amended_by`, `status: amended`) au même
  commit.
- **Vérifier les prémisses empiriques** avant de figer un ADR : tout
  énoncé sur l'état du code/des données se vérifie par grep, query ou
  lecture — citer un ADR antérieur ne vaut pas vérification.
- **Les minutes de décision tracent les arbitrages de l'opérateur
  humain.** Pose tes questions structurantes, retranscris les
  réponses ; n'invente jamais ces minutes.
- **Citation déclencheuse** : quand l'ADR naît d'une phrase de
  l'opérateur, le déclencheur ouvre par cette phrase **verbatim**
  (extrait pertinent, élision `[…]` si long) ; sinon, par la
  référence à l'artefact déclencheur (incident, mesure, échéance).
  Ne **jamais** fabriquer une citation.
- **Un ADR = un commit**, index inclus, sans code mêlé.
- **Backlink TODO** : tout chantier issu des Conséquences d'un ADR qui
  se matérialise en TODO porte la référence `D-NNN` de son ADR
  d'origine. Les TODO sans origine décisionnelle restent libres.
- **Proactivité** : quand une décision structurante est prise en
  session (cf. arbre de décision du guide, §2), propose spontanément
  d'ouvrir un ADR — n'attends pas qu'on te le demande.
- Toujours faire **valider le contenu par l'opérateur** avant de
  committer un ADR.
