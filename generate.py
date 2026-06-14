"""Génération d'une collection de scènes OBS pour un culte.

Deux usages (cf. D-003) :
- **CLI** : `uv run python generate.py "Titre du culte" [--theme ...]` — lit
  `chants.txt`, télécharge les images, produit le `.zip` et ouvre le dossier.
- **Bibliothèque** : `from generate import generer_culte` — le backend de
  l'interface de préparation appelle `generer_culte(titre, entrees, config, …)`
  sans dupliquer la logique de construction des scènes.

L'import du module n'a **aucun effet de bord** (toute l'exécution est sous
`main()` / `if __name__ == "__main__"`).
"""

import json
from zipfile import ZipFile
from obs_json_resources import Scene_Collection
from obs_json_resources import Tmp_scene
from obs_json_resources import parse_selection
import unicodedata
import re
import subprocess
import sys
import os
import requests
import time
from pathlib import Path


# --- Sortie terminal -----------------------------------------------------------

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_red(message):
    """Affiche un message en rouge dans le terminal"""
    print(f"{Colors.RED}{message}{Colors.RESET}")


def print_green(message):
    """Affiche un message en vert dans le terminal"""
    print(f"{Colors.GREEN}{message}{Colors.RESET}")


def print_yellow(message):
    """Affiche un message en jaune (avertissement) dans le terminal"""
    print(f"{Colors.YELLOW}{message}{Colors.RESET}")


def enable_windows_ansi():
    """Active les codes couleur ANSI sur la console Windows (no-op ailleurs)."""
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


# --- Helpers -------------------------------------------------------------------

def load_flagged_numeros(path='docs/relecture-corpus.md'):
    """Numéros encore cochés « à relire » dans la worklist (cases `- [ ]`).

    Sert à avertir, au moment de la génération, qu'un cantique du culte n'a pas
    encore été relu (corpus en baseline, cf. D-001/D-002). Cocher la case dans
    docs/relecture-corpus.md éteint l'avertissement pour ce cantique.
    """
    flagged = set()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.match(r'^- \[ \] `([^`]+)`', line)
                if m:
                    flagged.add(m.group(1))
    except OSError:
        pass
    return flagged


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def seq_label(i):
    """0 -> A, 25 -> Z, 26 -> AA, … (style colonne de tableur)."""
    s = ''
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(ord('A') + r) + s
    return s


def download_nature_image(seed=None, api_key=None, theme=None):
    """
    Télécharge une image de nature depuis l'API Unsplash officielle.
    Nécessite une clé API Unsplash fournie via `api_key`.
    Consulter la documentation: https://unsplash.com/documentation
    """
    try:
        if seed is None:
            seed = int(time.time() * 1000) % 1000

        if api_key is None:
            print("Erreur: Aucune clé API Unsplash n'a été fournie")
            return None, None

        width = 1920
        height = 1080
        api_url = "https://api.unsplash.com/photos/random"
        if theme is None:
            theme = "nature,landscape,forest,mountains"
        params = {
            "query": theme,
            "orientation": "landscape",
            "content_filter": "high",
            "seed": str(seed),
        }
        headers = {
            "Authorization": f"Client-ID {api_key}",
            "Accept-Version": "v1",
        }

        print(f"Requête à l'API Unsplash avec le thème: {theme}")
        api_response = requests.get(api_url, params=params, headers=headers)
        if api_response.status_code != 200:
            print(f"Erreur lors de la requête à l'API Unsplash: {api_response.status_code}")
            print(f"Message: {api_response.text}")
            return None, None

        photo_data = api_response.json()
        if "urls" not in photo_data or "raw" not in photo_data["urls"]:
            print("Erreur: Structure de réponse Unsplash inattendue, URL de l'image non trouvée")
            return None, None

        img_url = f"{photo_data['urls']['raw']}&w={width}&h={height}&fit=crop"
        print(f"Téléchargement de l'image depuis: {img_url}")
        img_response = requests.get(img_url, stream=True)
        print(f"Statut de la réponse: {img_response.status_code}")
        if img_response.status_code == 200:
            timestamp = int(time.time() * 1000000)
            img_name = f"nature_{timestamp}.jpg"
            print(f"Image téléchargée avec succès, nom du fichier: {img_name}")
            return img_response.content, img_name
        print(f"Erreur lors du téléchargement: code {img_response.status_code}")
    except Exception as e:
        print(f"Erreur lors du téléchargement de l'image: {str(e)}")
    return None, None


def ensure_img_directory(config):
    """S'assure que le répertoire des images existe et est accessible en écriture."""
    img_path = Path(config['paths']['images'])
    try:
        img_path.mkdir(parents=True, exist_ok=True)
        print(f"Dossier des images créé/vérifié: {img_path}")
        test_file = img_path / "test_write.tmp"
        test_file.touch()
        test_file.unlink()
        print("Permissions d'écriture vérifiées avec succès")
    except Exception as e:
        print(f"Erreur lors de la création/vérification du dossier des images: {str(e)}")
        raise


# --- Cœur réutilisable (CLI + backend, cf. D-003) ------------------------------

def extraire_numero_selection(line):
    """Extrait `(numero, selecteur_str)` d'une ligne de culte.

    - `numero` : « NN-NN » (cantique) ou « Ps 0NN[A] » (psaume, depuis
      « Psaume X » / « Ps X »), `None` si non reconnu.
    - `selecteur_str` : contenu d'un « (...) » final (ex. « 1,2,3 »), '' si absent.
    """
    line = (line or '').strip()
    sel = ''
    m = re.search(r'\(([\d\s,Rr]+)\)\s*$', line)
    if m:
        sel = re.sub(r'\s+', '', m.group(1))
    mc = re.match(r'^(\d+-\d+)', line)
    if mc:
        return mc.group(1), sel
    mp = re.match(r'^(?:Psaume|Ps)\s+(\d+)([A-Za-z]?)', line)
    if mp:
        return f"Ps {int(mp.group(1)):03d}{mp.group(2).upper()}", sel
    return None, sel


def interpreter_lignes(lignes):
    """Applique l'entrelacement des spontanés à une liste de lignes brutes.

    Si la 1re ligne est `[SPONTANES] XXX`, charge `[SPONTANES] XXX.txt` et
    entrelace les chants principaux (lignes suivantes) aux marqueurs `#n`.
    Retourne une liste de `(ligne, origine)` où origine ∈ {'cantique','spontané'}.
    """
    lignes = [l.rstrip('\n') for l in lignes]
    if not (lignes and lignes[0].strip().startswith('[SPONTANES]')):
        return [(l, 'cantique') for l in lignes]

    spontanes_file = f"{lignes[0].strip()}.txt"
    main_chants = [l.strip() for l in lignes[1:] if l.strip()]
    if not os.path.exists(spontanes_file):
        print(f"Attention: Le fichier de spontanés {spontanes_file} n'existe pas")
        return [(c, 'cantique') for c in main_chants]
    try:
        with open(spontanes_file, 'r', encoding='utf-8') as sf:
            spontanes_list = sf.readlines()
        combined = []
        main_index = 0
        for line in spontanes_list:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^#\d+$', line):
                if main_index < len(main_chants):
                    combined.append((main_chants[main_index], 'cantique'))
                    main_index += 1
            else:
                combined.append((line, 'spontané'))
        combined.extend((c, 'cantique') for c in main_chants[main_index:])
        return combined
    except Exception as e:
        print(f"Erreur lecture spontanés: {e}")
        return [(c, 'cantique') for c in main_chants]


def resoudre_entrees(entrees, config, flagged_numeros=None):
    """Résout une liste de `(ligne, origine)` en `(chemin_yaml, selection)`.

    `origine` ∈ {'cantique', 'spontané'} (impacte seulement le libellé du log).
    Retourne `(resolved, info)` où `info` récapitule numéros ajoutés / non
    trouvés / à relire.
    """
    if flagged_numeros is None:
        flagged_numeros = set()
    resolved = []
    info = {"ajoutes": [], "non_trouves": [], "a_relire": []}
    cantiques_dir = os.path.abspath(config['paths'].get('stock_cantiques', 'stock/cantiques'))
    txt_dir = os.path.abspath(config['paths'].get('stock_txt', 'stock/txt'))

    for entry, origin in entrees:
        line = entry.strip()
        libelle = 'Spontané' if origin == 'spontané' else 'Cantique'
        if not line or line.startswith('#') or line.startswith('[SPONTANES]'):
            continue

        # Numéro + sélecteur de couplets (ex. « 22-04 … (1,3) »).
        numero, sel_str = extraire_numero_selection(line)
        if numero is None:
            print(f"Format de ligne non reconnu: {line}")
            continue
        selection = parse_selection(sel_str) if sel_str else None
        if sel_str and selection is None:
            print(f"Sélecteur illisible, ignoré: {line}")
        print(f"Recherche de {numero}...")

        # Résolution : cantique structuré (stock/cantiques) d'abord, repli txt.
        cantique_path = None
        yaml_candidate = os.path.join(cantiques_dir, f"{numero}.yaml")
        if os.path.exists(yaml_candidate):
            cantique_path = yaml_candidate
            print_green(f"✓ {libelle} structuré trouvé: {numero}.yaml")

        filelist = os.listdir(txt_dir) if not cantique_path and os.path.isdir(txt_dir) else []
        for file in filelist:
            if numero in file:
                cantique_path = os.path.join(txt_dir, file)
                print_green(f"✓ {libelle} trouvé: {file}")
                break

        # Psaume avec lettre (ex. Ps 034A) → tenter sans le padding (Ps 34A).
        if not cantique_path and numero.startswith("Ps ") and len(numero) >= 7 and numero[-1].isalpha():
            numero_sans_padding = f"Ps {int(numero[3:-1])}{numero[-1]}"
            for file in filelist:
                if numero_sans_padding in file:
                    cantique_path = os.path.join(txt_dir, file)
                    print_green(f"✓ {libelle} trouvé: {file}")
                    break

        if cantique_path:
            if numero in flagged_numeros:
                print_yellow(f"⚠ {numero} est marqué « à relire » (corpus non finalisé — voir docs/relecture-corpus.md)")
                info["a_relire"].append(numero)
            resolved.append((cantique_path, selection))
            info["ajoutes"].append(numero)
        else:
            print_red(f"✗ {libelle} {numero} non trouvé")
            info["non_trouves"].append(numero)

    return resolved, info


def construire_collection(titre, entrees, config, img_accueil, img_envoi,
                          img_accueil_name, img_envoi_name):
    """Construit la collection OBS d'un culte **sans écrire de fichier**.

    Point d'entrée réutilisable : ne touche ni à `chants.txt`, ni à argv, ni au
    téléchargement d'images — tout lui est fourni. Sert à la fois à générer le
    `.zip` (`generer_culte`) et à l'envoi direct vers OBS (`obs_push`, D-004).

    Retourne `(collection, info)` où info = `{ajoutes, non_trouves, a_relire}`.
    """
    collection = Scene_Collection(titre)
    resolved, info = resoudre_entrees(entrees, config, load_flagged_numeros())
    # Insérer dans l'ordre des entrées ; l'affichage OBS est piloté plus bas.
    for cantique_path, selection in resolved:
        collection.add_scene(cantique_path, selection)
    print(f"{len(collection.scenes)} cantiques ajoutés à la collection")

    # Scènes d'accueil et d'envoi.
    accueil = Tmp_scene('Accueil', collection)
    accueil.add_image('fond1', str(img_accueil))
    accueil.add_text('bienvenue', f'{titre}\nBienvenue à tous !')
    accueil.register()

    envoi = Tmp_scene('Envoi', collection)
    envoi.add_image('fond2', str(img_envoi))
    envoi.add_text('aurevoir', 'Bon dimanche à tous !')
    envoi.register()

    # Séquence d'affichage : Accueil en tête, Envoi en queue, une vue « Base :
    # temple » intercalée avant chaque cantique et l'envoi ; préfixes A., B., …
    cantique_names = [s.name for s in collection.scenes]
    sequence = ['Accueil']
    base_counter = 1
    for scene_name in cantique_names + ['Envoi']:
        base_name = 'Base : temple' if base_counter == 1 else f'Base : temple {base_counter}'
        if base_counter > 1:
            collection.duplicate_base(base_name)
        sequence.append(base_name)
        sequence.append(scene_name)
        base_counter += 1

    display_order = []
    for i, current in enumerate(sequence):
        label = 'Base : temple' if current.startswith('Base : temple') else current
        final = f"{seq_label(i)}. {label}"
        collection.rename_scene(current, final)
        display_order.append(final)
    collection.set_display_order(display_order)
    print(f"Ordre des scènes : {len(display_order)} scènes (A. → …), {base_counter - 1} vues « Base »")
    return collection, info


def generer_culte(titre, entrees, config, img_accueil, img_envoi,
                  img_accueil_name, img_envoi_name):
    """Construit la collection et écrit le `.zip` (JSON + images).

    Retourne un dict d'info : `zip` (Path), `fname`, `ajoutes`, `non_trouves`,
    `a_relire`.
    """
    collection, info = construire_collection(
        titre, entrees, config, img_accueil, img_envoi, img_accueil_name, img_envoi_name)

    # Écriture du .zip. On crée le dossier de sortie au besoin, et on n'ajoute
    # que les images réellement présentes (une image manquante ne doit pas faire
    # échouer toute la génération).
    fname = slugify(titre)
    output_dir = Path(config['paths']['output'])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_zip = output_dir / f'{fname}.zip'
    with ZipFile(str(output_zip), 'w') as myzip:
        for img_path, img_name in ((img_accueil, img_accueil_name), (img_envoi, img_envoi_name)):
            if img_path and Path(img_path).exists():
                myzip.write(str(img_path), f'img/{img_name}')
        myzip.writestr(f'{fname}.json', json.dumps(collection.to_json()))

    info["zip"] = output_zip
    info["fname"] = fname
    return info


# --- Étapes spécifiques à la CLI -----------------------------------------------

def charger_config(path='config.json'):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def lire_chants_txt(path='chants.txt'):
    """Lit `chants.txt` et applique l'entrelacement des spontanés.

    Retourne une liste de `(ligne, origine)` prête pour `generer_culte`.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return interpreter_lignes(f.readlines())


def telecharger_images(config, theme):
    """Télécharge 2 images de fond (Unsplash) avec repli ; met à jour `config.json`.

    Retourne `(img_accueil, img_envoi, img_accueil_name, img_envoi_name)`.
    """
    ensure_img_directory(config)
    api_key = config.get('api', {}).get('unsplash')
    print("Téléchargement des images...")
    seed1 = int(time.time() * 1000) % 10000
    seed2 = (seed1 + 1000) % 10000
    print(f"Utilisation des seeds {seed1} et {seed2} pour les images")
    a_content, a_name = download_nature_image(seed1, api_key=api_key, theme=theme)
    time.sleep(1)
    e_content, e_name = download_nature_image(seed2, api_key=api_key, theme=theme)

    img_path = Path(config['paths']['images']).resolve()
    if a_content and e_content:
        try:
            img_accueil = img_path / a_name
            img_envoi = img_path / e_name
            print("Sauvegarde de l'image d'accueil:", img_accueil.as_posix())
            img_accueil.write_bytes(a_content)
            print("Sauvegarde de l'image d'envoi:", img_envoi.as_posix())
            img_envoi.write_bytes(e_content)
            config['images']['accueil'] = a_name
            config['images']['envoi'] = e_name
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            print("Configuration mise à jour avec succès")
            return img_accueil, img_envoi, a_name, e_name
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des images ou de la mise à jour de la configuration: {str(e)}")

    print("Utilisation des images par défaut.")
    a_name = config['images']['accueil']
    e_name = config['images']['envoi']
    return img_path / a_name, img_path / e_name, a_name, e_name


def main(argv=None):
    enable_windows_ansi()
    print("Démarrage du script...")

    try:
        config = charger_config()
        print("Configuration chargée avec succès")
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration: {str(e)}")
        sys.exit(1)

    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("Usage: generate.py <name> [--theme <theme>]")
        sys.exit(1)

    theme = "nature,landscape,forest,mountains"
    if "--theme" in argv:
        i = argv.index("--theme")
        if i + 1 < len(argv):
            theme = argv[i + 1]
            argv.pop(i)
            argv.pop(i)
        else:
            print("Erreur: --theme nécessite une valeur")
            sys.exit(1)

    titre = ' '.join(argv)
    print(f"Nom du culte: {titre}")
    print(f"Thème des images: {theme}")

    images = telecharger_images(config, theme)

    print("Lecture du fichier chants.txt...")
    try:
        entrees = lire_chants_txt('chants.txt')
    except Exception as e:
        print(f"Erreur lors de la lecture de chants.txt: {str(e)}")
        entrees = []

    generer_culte(titre, entrees, config, *images)

    # Ouvrir le dossier de sortie (Windows).
    output_dir = Path(config['paths']['output']).resolve()
    try:
        subprocess.Popen(['explorer', str(output_dir)])
    except Exception:
        pass


if __name__ == "__main__":
    main()
