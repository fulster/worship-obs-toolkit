# worship-obs-toolkit

Génère automatiquement une **collection de scènes OBS Studio** à partir d'une simple liste de
cantiques, pour la projection des paroles pendant le culte.

À partir d'un fichier `chants.txt` listant les chants d'un culte, l'outil :

1. récupère les paroles dans le corpus structuré `stock/cantiques/` (un YAML par cantique) ;
2. télécharge deux images de fond (accueil / envoi) via l'API Unsplash ;
3. construit une scène OBS par cantique (titre + paroles), plus une scène d'accueil et une scène
   d'envoi ;
4. exporte le tout dans un fichier `.zip` (JSON de collection + images) prêt à être importé dans
   OBS Studio.

## Prérequis

- [uv](https://docs.astral.sh/uv/) (gestion de l'environnement et des dépendances)
- Python ≥ 3.10 (installé automatiquement par uv si besoin)
- [OBS Studio](https://obsproject.com/) pour importer la collection générée
- Une clé API [Unsplash](https://unsplash.com/documentation) (gratuite) pour les images de fond

## Installation

```bash
# Cloner / copier le projet, puis :
uv sync
```

`uv sync` crée l'environnement virtuel `.venv` et installe les dépendances (`requests`, `pyyaml`).

## Configuration

Copier le modèle puis l'adapter :

```bash
copy config.json.example config.json   # Windows
cp   config.json.example config.json   # Linux / macOS
```

Champs de `config.json` :

| Clé | Description |
|---|---|
| `paths.stock_cantiques` | Corpus YAML des paroles (`./stock/cantiques`, défaut si absent). |
| `paths.stock_txt` | Ancien dossier `.txt` (repli historique, aujourd'hui inerte). |
| `paths.txt` | Dossier de repli scanné si `chants.txt` est illisible. |
| `paths.images` | Dossier où sont écrites les images de fond téléchargées. |
| `paths.output` | Dossier où est écrit le `.zip` final. |
| `images.accueil` / `images.envoi` | Images de repli utilisées si le téléchargement Unsplash échoue. |
| `api.unsplash` | Votre clé API Unsplash (Access Key). |

> ⚠️ `config.json` contient votre clé API : il est ignoré par git (voir `.gitignore`).
> Ne committez jamais votre clé.

## Utilisation

1. **Composer la liste du culte** dans `chants.txt` (voir le format ci-dessous).
2. **Lancer la génération** :

```bash
uv run python generate.py "Culte du 15 juin"
```

Avec un thème d'images personnalisé pour Unsplash :

```bash
uv run python generate.py "Culte de Noël" --theme "winter,snow,light"
```

Le `.zip` est écrit dans `paths.output` et le dossier de sortie s'ouvre automatiquement
(Windows). Dans OBS Studio : **Scene Collection → Import**, puis sélectionner le `.json`
contenu dans l'archive.

## Format de `chants.txt`

Une entrée par ligne. Les lignes vides et celles commençant par `#` sont ignorées.

```text
21-17 « Nous voici rassemblés en ton nom »
Psaume 36 « O Seigneur ta fidélité » (1,2,3)
Ps 121
22-04 Oh ! Parle-moi Seigneur (1,R,3)
```

- **Cantiques** : préfixe `NN-NN` (ex. `21-17`) → `stock/cantiques/NN-NN.yaml`.
- **Psaumes** : `Psaume X` ou `Ps X` (suffixe lettre accepté, ex. `Ps 34A`) → `stock/cantiques/Ps 0NN.yaml`.
- **Sélecteur de couplets** : un `(...)` en **fin de ligne** choisit/réordonne les couplets. Chiffres
  seuls (`(1,3)`) → couplets retenus, **refrain réinséré après chaque** ; avec un `R` (`(1,R,3)`,
  `(R,1,R,2)`) → séquence **littérale**. Détail : [`docs/format-cantique.md`](docs/format-cantique.md).
- Le texte libre après le numéro (titre entre guillemets) est purement indicatif.

### Cantiques spontanés

Si la **première ligne** de `chants.txt` est un marqueur `[SPONTANES] XXX`, l'outil charge le
fichier `[SPONTANES] XXX.txt` correspondant et **entrelace** ses chants spontanés avec les
cantiques de `chants.txt` : chaque marqueur `#n` dans le fichier de spontanés est remplacé par le
cantique suivant de la liste principale.

```text
[SPONTANES] TEMPS_EGLISE
21-17 Nous voici rassemblés
22-04 Oh ! Parle-moi Seigneur
```

Quatre listes de spontanés sont fournies à la racine (`[SPONTANES] *.txt`).

## Structure du projet

```
worship-obs-toolkit/
├── generate.py              # Point d'entrée : lit chants.txt → produit le .zip OBS
├── obs_json_resources.py    # Modèle objet OBS (collection, scènes, sources, items)
├── config.json(.example)    # Configuration (chemins, images, clé Unsplash)
├── chants.txt               # Liste du culte à générer
├── chants.sample.txt        # Exemple de liste
├── [SPONTANES] *.txt        # Listes de cantiques spontanés
├── tpl/                     # Templates JSON des objets OBS
├── schemas/                 # cantique.schema.json (validation du format)
├── scripts/                 # convert_cantiques.py, promote_cantiques.py, adr_*.py
├── stock/
│   ├── cantiques/           # Corpus YAML des paroles  ← source des paroles
│   ├── prieres/             # Prières liturgiques (p####)
│   └── txt/à nettoyer/      # 922 bruts (entrée du convertisseur)
└── docs/                    # format-cantique.md, relecture-corpus.md, decisions/ (ADR), todo/
```

> `stock/doc/` (sources Word d'origine) et `stock/arc/` (archives) ne sont pas utilisés par le
> pipeline ; la racine `stock/txt/` est vide (les `.txt` nettoyés à la main ont été retirés, couverts
> par le corpus YAML).

## Fonctionnement interne

`generate.py` instancie une `Scene_Collection` (`obs_json_resources.py`). Pour chaque cantique,
une `Scene` lit le fichier `stock/cantiques/<numero>.yaml`, **expanse le refrain** après chaque
couplet et applique le sélecteur `(...)` éventuel (les traductions ne sont **pas** projetées par
défaut), puis assemble, à partir des templates de `tpl/`, les sources et items OBS : titre, paroles,
image de fond. Les scènes d'accueil et d'envoi sont des `Tmp_scene` (image + texte). La collection
est sérialisée en JSON et zippée avec les images.

Le format du corpus et sa genèse sont décrits dans [`docs/format-cantique.md`](docs/format-cantique.md)
et les ADR [D-001](docs/decisions/D-001-format-source-structure-paroles.md) /
[D-002](docs/decisions/D-002-support-multilingue-traductions.md).

## Relecture incrémentale du corpus

Le corpus `stock/cantiques/` a été produit par **conversion automatique** des 922 cantiques bruts,
puis promu « en baseline » : tous les fichiers sont valides et projetables, mais **363 portent un
signalement** du convertisseur (structure incertaine, langue à confirmer…). Ils sont listés dans
[`docs/relecture-corpus.md`](docs/relecture-corpus.md), à raffiner à ton rythme.

Au moment de la génération, `generate.py` **affiche un avertissement** quand un cantique du culte est
encore marqué « à relire » — un rappel qu'il mérite peut-être un coup d'œil avant la projection.

Pour relire un cantique :

1. Dans [`docs/relecture-corpus.md`](docs/relecture-corpus.md), repère une entrée non cochée
   `` - [ ] `<numero>` — <titre> — _<flag>_ ``.
2. Ouvre `stock/cantiques/<numero>.yaml` (au besoin, compare au brut `stock/txt/à nettoyer/`). Selon
   le flag :
   - `sans-couplets` / `non-decoupe` : chant stocké en **un seul couplet** (aucune numérotation
     détectée). Le redécouper en `couplets:` pour pouvoir en sélectionner les strophes ; sinon, OK tel quel.
   - `multilingue`, `langue-indeterminee`, `renumerotation-sans-entete` : vérifier la séparation
     français / `traductions` et le code `langue:`.
   - `source-ambigue` : vérifier que `source:` n'a pas avalé des paroles.
   - `collision-numero` : deux bruts partagent ce numéro ; le doublon est resté en staging
     (`build/cantiques/<numero>__doublon*.yaml`) — choisir la bonne version.
3. Corrige directement le `.yaml` (format : [`docs/format-cantique.md`](docs/format-cantique.md)).
4. **Coche la case** (`- [ ]` → `- [x]`) : l'avertissement de `generate.py` s'éteint pour ce cantique.

> ⚠️ Ne relance pas `scripts/promote_cantiques.py` après des corrections en place : il **écrase**
> `stock/cantiques/` depuis le staging et perdrait tes relectures.

## Licence

GPL-3.0 — voir [LICENSE](LICENSE).
