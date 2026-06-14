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
import shutil
import time
from pathlib import Path

# ANSI color codes for terminal output
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

# Enable ANSI color support on Windows
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def download_nature_image(seed=None, api_key=None, theme=None):
    """
    Télécharge une image de nature depuis l'API Unsplash officielle
    Nécessite une clé API Unsplash qui peut être fournie via le paramètre api_key
    ou dans config.json sous config["api"]["unsplash"]
    Consulter la documentation: https://unsplash.com/documentation
    """
    try:
        # Utiliser un seed aléatoire si non fourni
        if seed is None:
            seed = int(time.time() * 1000) % 1000
        
        # Si aucune clé API n'est fournie, essayer de la récupérer depuis la configuration
        if api_key is None:
            # On suppose que config est déjà chargé et disponible globalement
            if "api" in config and "unsplash" in config["api"]:
                api_key = config["api"]["unsplash"]
            else:
                print("Erreur: Aucune clé API Unsplash n'a été fournie")
                return None, None
        
        # Définir les dimensions de l'image
        width = 1920
        height = 1080
        
        # Construire l'URL de l'API Unsplash pour obtenir une image de nature aléatoire
        api_url = "https://api.unsplash.com/photos/random"
        
        # Utiliser le thème fourni ou le thème par défaut
        if theme is None:
            theme = "nature,landscape,forest,mountains"
        
        # Paramètres pour spécifier une image de nature
        params = {
            "query": theme,
            "orientation": "landscape",
            "content_filter": "high"
        }
        
        # Si un seed est fourni, l'utiliser comme paramètre
        if seed is not None:
            params["seed"] = str(seed)
        
        # En-têtes avec l'authentification
        headers = {
            "Authorization": f"Client-ID {api_key}",
            "Accept-Version": "v1"
        }
        
        print(f"Requête à l'API Unsplash avec le thème: {theme}")
        # Faire la requête à l'API
        api_response = requests.get(api_url, params=params, headers=headers)
        
        if api_response.status_code != 200:
            print(f"Erreur lors de la requête à l'API Unsplash: {api_response.status_code}")
            print(f"Message: {api_response.text}")
            return None, None
            
        # Extraire les données JSON
        photo_data = api_response.json()
        
        # Vérifier si les URLs sont présentes dans la réponse
        if "urls" not in photo_data or "raw" not in photo_data["urls"]:
            print("Erreur: Structure de réponse Unsplash inattendue, URL de l'image non trouvée")
            return None, None
            
        # Construire une URL avec les dimensions souhaitées
        img_url = f"{photo_data['urls']['raw']}&w={width}&h={height}&fit=crop"
        print(f"Téléchargement de l'image depuis: {img_url}")
        
        # Télécharger l'image
        img_response = requests.get(img_url, stream=True)
        print(f"Statut de la réponse: {img_response.status_code}")
        
        if img_response.status_code == 200:
            # Générer un nom de fichier unique avec microsecondes
            timestamp = int(time.time() * 1000000)
            img_name = f"nature_{timestamp}.jpg"
            print(f"Image téléchargée avec succès, nom du fichier: {img_name}")
            return img_response.content, img_name
        else:
            print(f"Erreur lors du téléchargement: code {img_response.status_code}")
    except Exception as e:
        print(f"Erreur lors du téléchargement de l'image: {str(e)}")
    
    return None, None

def ensure_img_directory(config):
    """
    S'assure que le répertoire des images existe et est accessible en écriture
    """
    img_path = Path(config['paths']['images'])
    try:
        img_path.mkdir(parents=True, exist_ok=True)
        print(f"Dossier des images créé/vérifié: {img_path}")
        
        # Vérifier les permissions
        test_file = img_path / "test_write.tmp"
        test_file.touch()
        test_file.unlink()
        print("Permissions d'écriture vérifiées avec succès")
        
    except Exception as e:
        print(f"Erreur lors de la création/vérification du dossier des images: {str(e)}")
        raise

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

print("Démarrage du script...")

# Charger la configuration
try:
    with open('config.json', 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)
    print("Configuration chargée avec succès")
except Exception as e:
    print(f"Erreur lors du chargement de la configuration: {str(e)}")
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: script.py <name> [--theme <theme>]")
    sys.exit(1)

# Parse arguments for name and optional theme
args = sys.argv[1:]
theme = "nature,landscape,forest,mountains"  # Default theme

# Check for --theme argument
if "--theme" in args:
    theme_index = args.index("--theme")
    if theme_index + 1 < len(args):
        theme = args[theme_index + 1]
        # Remove --theme and its value from args
        args.pop(theme_index)
        args.pop(theme_index)
    else:
        print("Erreur: --theme nécessite une valeur")
        sys.exit(1)

# Concatenate remaining arguments to form the title
name = ' '.join(args)
fname = slugify(name)
print(f"Nom du culte: {name}")
print(f"Thème des images: {theme}")

# S'assurer que le répertoire des images existe
ensure_img_directory(config)

print("Téléchargement des images...")
# Télécharger les images avec des seeds aléatoires
seed1 = int(time.time() * 1000) % 10000  # Utiliser les millisecondes pour plus de variété
seed2 = (seed1 + 1000) % 10000  # S'assurer d'avoir un seed différent pour la deuxième image

print(f"Utilisation des seeds {seed1} et {seed2} pour les images")
img_accueil_content, img_accueil_name = download_nature_image(seed1, theme=theme)
time.sleep(1)  # Attendre 1 seconde entre les téléchargements
img_envoi_content, img_envoi_name = download_nature_image(seed2, theme=theme)

# Essayer de télécharger et sauvegarder les nouvelles images
success = False
if img_accueil_content and img_envoi_content:
    try:
        # Préparer les chemins avec Path pour une meilleure gestion des séparateurs
        img_path = Path(config['paths']['images']).resolve()
        img_accueil = img_path / img_accueil_name
        img_envoi = img_path / img_envoi_name
        
        # Sauvegarder l'image d'accueil
        print("Sauvegarde de l'image d'accueil:", img_accueil.as_posix())
        img_accueil.write_bytes(img_accueil_content)
        
        # Sauvegarder l'image d'envoi
        print("Sauvegarde de l'image d'envoi:", img_envoi.as_posix())
        img_envoi.write_bytes(img_envoi_content)
        
        # Mettre à jour la configuration
        print("Mise à jour de la configuration...")
        config['images']['accueil'] = img_accueil_name
        config['images']['envoi'] = img_envoi_name
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print("Configuration mise à jour avec succès")
        success = True
        
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des images ou de la mise à jour de la configuration: {str(e)}")

# Si quelque chose a échoué, utiliser les images par défaut
if not success:
    print("Utilisation des images par défaut.")
    img_path = Path(config['paths']['images']).resolve()
    img_accueil = img_path / config['images']['accueil']
    img_envoi = img_path / config['images']['envoi']

collection = Scene_Collection(name)

# Numéros encore « à relire » (worklist) : on avertit s'ils sont projetés.
flagged_numeros = load_flagged_numeros()

# Lire le fichier chants.txt et générer des scènes pour les cantiques listés
print("Lecture du fichier chants.txt...")
try:
    with open('chants.txt', 'r', encoding='utf-8') as f:
        chants_list = f.readlines()
    
    # Vérifier si la première ligne est au format [SPONTANES] XXX
    spontanes_file = None
    if chants_list and chants_list[0].strip().startswith('[SPONTANES]'):
        spontanes_marker = chants_list[0].strip()
        spontanes_file = f"{spontanes_marker}.txt"
        print(f"Détection d'un fichier de cantiques spontanés: {spontanes_file}")
        
        # Extraire les cantiques du fichier principal (sans la ligne [SPONTANES])
        main_chants = [line.strip() for line in chants_list[1:] if line.strip()]
        print(f"Fichier principal: {len(main_chants)} cantiques à intégrer")
        
        # Lire le fichier de cantiques spontanés s'il existe
        if os.path.exists(spontanes_file):
            try:
                with open(spontanes_file, 'r', encoding='utf-8') as sf:
                    spontanes_list = sf.readlines()
                print(f"Fichier de cantiques spontanés trouvé avec {len(spontanes_list)} lignes")
                
                # Créer une nouvelle liste entrelacée
                combined_list = []
                main_index = 0
                
                for line in spontanes_list:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Si la ligne est un marqueur #n, insérer un cantique du fichier principal
                    if re.match(r'^#\d+$', line):
                        marker_num = int(line[1:])
                        print(f"Marqueur {line} détecté: insertion d'un cantique principal")
                        if main_index < len(main_chants):
                            combined_list.append(main_chants[main_index])
                            main_index += 1
                        else:
                            print(f"Attention: Plus de marqueurs que de cantiques principaux, marqueur {line} ignoré")
                    else:
                        # Sinon, ajouter la ligne du fichier de cantiques spontanés
                        combined_list.append(line)
                
                # Ajouter les cantiques principaux restants s'il y en a
                if main_index < len(main_chants):
                    remaining = len(main_chants) - main_index
                    print(f"Ajout des {remaining} cantiques principaux restants")
                    combined_list.extend(main_chants[main_index:])
                
                # Remplacer la liste de cantiques par la liste entrelacée
                chants_list = combined_list
                print(f"Liste entrelacée créée avec {len(chants_list)} cantiques au total")
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier de cantiques spontanés: {str(e)}")
                # En cas d'erreur, utiliser simplement les cantiques du fichier principal
                chants_list = main_chants
        else:
            print(f"Attention: Le fichier de cantiques spontanés {spontanes_file} n'existe pas")
            # Utiliser simplement les cantiques du fichier principal
            chants_list = main_chants
    
    # Inverser l'ordre pour avoir les scènes dans le même ordre que le fichier chants.txt
    chants_list.reverse()
    
    # Parcourir chaque ligne des fichiers
    for line in chants_list:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('[SPONTANES]'):
            continue  # Ignorer les lignes vides, les commentaires et l'en-tête [SPONTANES]

        # Extraire un sélecteur de couplets en fin de ligne, ex: « (1,3) » ou
        # « (1,R,2) » — honore la notation déjà utilisée dans chants.txt.
        selection = None
        sel_match = re.search(r'\(([\d\s,Rr]+)\)\s*$', line)
        if sel_match:
            selection = parse_selection(sel_match.group(1))
            if selection is None:
                print(f"Sélecteur illisible, ignoré: {line}")

        # Extraire le numéro du cantique (format: "21-17") ou du psaume (format: "Psaume X", "Ps X" ou "Ps XXX")
        match_cantique = re.match(r'^(\d+-\d+)', line)
        match_psaume = re.match(r'^(?:Psaume|Ps)\s+(\d+)([A-Z]?)', line)
        
        if match_cantique:
            numero = match_cantique.group(1)
            print(f"Recherche du cantique {numero}...")
        elif match_psaume:
            num_psaume = int(match_psaume.group(1))
            # Récupérer le suffixe s'il existe (A, B, etc.)
            suffixe = match_psaume.group(2) if match_psaume.group(2) else ""
            numero = f"Ps {num_psaume:03d}{suffixe}"  # Format sur 3 chiffres avec zéros à gauche et suffixe si présent
            print(f"Recherche du psaume {numero}...")
        else:
            print(f"Format de ligne non reconnu: {line}")
            continue
        
        # Rechercher d'abord un cantique structuré (D-001) : stock/cantiques/<numero>.yaml
        cantique_path = None
        cantiques_dir = os.path.abspath(config['paths'].get('stock_cantiques', 'stock/cantiques'))
        yaml_candidate = os.path.join(cantiques_dir, f"{numero}.yaml")
        if os.path.exists(yaml_candidate):
            cantique_path = yaml_candidate
            print_green(f"✓ Cantique structuré trouvé: {numero}.yaml")

        # Repli : ancien format texte libre dans stock/txt (recherche par sous-chaîne)
        txt_dir = os.path.abspath(config['paths']['stock_txt'] if 'stock_txt' in config['paths'] else 'stock/txt')
        filelist = os.listdir(txt_dir) if not cantique_path and os.path.isdir(txt_dir) else []
        for file in filelist:
            # Vérifier si le fichier contient le numéro du cantique (peu importe sa position)
            if numero in file:
                cantique_path = os.path.join(txt_dir, file)
                print_green(f"✓ Cantique trouvé: {file}")
                break
        
        # Si non trouvé et que c'est un psaume avec lettre (ex: Ps 034A), essayer sans le padding (ex: Ps 34A)
        if not cantique_path and numero.startswith("Ps ") and len(numero) >= 7 and numero[-1].isalpha():
            # Extraire le numéro et la lettre
            num_part = numero[3:-1]  # "034"
            lettre = numero[-1]      # "A"
            # Créer la version sans padding
            numero_sans_padding = f"Ps {int(num_part)}{lettre}"  # "Ps 34A"
            for file in filelist:
                if numero_sans_padding in file:
                    cantique_path = os.path.join(txt_dir, file)
                    print_green(f"✓ Cantique trouvé: {file}")
                    break
        
        # Si le cantique est trouvé, l'ajouter à la collection
        if cantique_path:
            if numero in flagged_numeros:
                print_yellow(f"⚠ {numero} est marqué « à relire » (corpus non finalisé — voir docs/relecture-corpus.md)")
            collection.add_scene(cantique_path, selection)
        else:
            print_red(f"✗ Cantique {numero} non trouvé dans {txt_dir}")

    
    print(f"{len(collection.scenes)} cantiques ajoutés à la collection")
except Exception as e:
    print(f"Erreur lors de la lecture de chants.txt: {str(e)}")
    print("Utilisation de tous les fichiers du répertoire txt comme alternative...")
    collection.generate_scenes_from_dir(config['paths']['txt'])

# Add intro scene
Accueil = Tmp_scene('Accueil', collection)
Accueil.add_image('fond1', str(img_accueil))
Accueil.add_text('bienvenue', f'{name}\nBienvenue à tous !')
Accueil.register()

# Add outro scene
Envoi = Tmp_scene('Envoi', collection)
Envoi.add_image('fond2', str(img_envoi))
Envoi.add_text('aurevoir', 'Bon dimanche à tous !')
Envoi.register()

# Create output zip file
output_zip = Path(config['paths']['output']) / f'{fname}.zip'
with ZipFile(str(output_zip), 'w') as myzip:
    # Écrire les images dans le sous-répertoire img/
    myzip.write(str(img_accueil), f'img/{img_accueil_name}')
    myzip.write(str(img_envoi), f'img/{img_envoi_name}')
    # Écrire le fichier JSON à la racine
    myzip.writestr(f'{fname}.json', json.dumps(collection.to_json()))

# Open the output directory
output_dir = Path(config['paths']['output']).resolve()
subprocess.Popen(['explorer', str(output_dir)])
