# worship-obs-toolkit

Génère automatiquement une **collection de scènes OBS Studio** à partir d'une simple liste de
cantiques, pour la projection des paroles pendant le culte.

À partir d'un fichier `chants.txt` listant les chants d'un culte, l'outil :

1. récupère les paroles correspondantes dans `stock/txt/` ;
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

`uv sync` crée l'environnement virtuel `.venv` et installe les dépendances (`requests`).

## Configuration

Copier le modèle puis l'adapter :

```bash
copy config.json.example config.json   # Windows
cp   config.json.example config.json   # Linux / macOS
```

Champs de `config.json` :

| Clé | Description |
|---|---|
| `paths.stock_txt` | Dossier des paroles (`./stock/txt`). |
| `paths.txt` | Dossier de repli scanné si `chants.txt` est illisible (`./stock/txt`). |
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
Psaume 36 « O Seigneur ta fidélité »
Ps 121
22-04 Oh ! Parle-moi Seigneur
```

- **Cantiques** : préfixe au format `NN-NN` (ex. `21-17`). Le fichier correspondant est recherché
  dans `stock/txt/` par son numéro, peu importe le reste du nom.
- **Psaumes** : `Psaume X` ou `Ps X` (un suffixe de lettre est accepté, ex. `Ps 34A`).
- Le texte libre après le numéro (titre entre guillemets, couplets…) est purement indicatif.

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
├── stock/
│   └── txt/                 # Paroles des cantiques (.txt)  ← source des paroles
└── docs/                    # Notes complémentaires
```

> `stock/doc/` (sources Word d'origine) et `stock/arc/` (archives) ne sont pas utilisés par le
> pipeline de génération ; ils sont conservés à titre d'archive.

## Fonctionnement interne

`generate.py` instancie une `Scene_Collection` (`obs_json_resources.py`). Pour chaque cantique,
une `Scene` lit le fichier `.txt` (1re ligne = titre, le reste = paroles) et assemble, à partir
des templates de `tpl/`, les sources et items OBS : titre, paroles, image de fond. Les scènes
d'accueil et d'envoi sont des `Tmp_scene` (image + texte). La collection est sérialisée en JSON et
zippée avec les images.

## Licence

GPL-3.0 — voir [LICENSE](LICENSE).
