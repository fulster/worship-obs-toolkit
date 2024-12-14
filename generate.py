import json
from zipfile import ZipFile
from obs_json_resources import Scene_Collection
from obs_json_resources import Tmp_scene
import unicodedata
import re
import subprocess
import sys
import os

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

# Charger la configuration
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

if len(sys.argv) < 2:
    print("Usage: script.py <name>")
    sys.exit(1)

# Concatenate all arguments to form the title
name = ' '.join(sys.argv[1:])
fname = slugify(name)

# Chemins complets pour la lecture des images
img_accueil = os.path.join(config['paths']['images'], config['images']['accueil'])
img_envoi = os.path.join(config['paths']['images'], config['images']['envoi'])

collection = Scene_Collection(name)

# Add scenes from txt directory (not ordered right now)
collection.generate_scenes_from_dir(config['paths']['txt'])

# Add intro scene
Accueil = Tmp_scene('Accueil', collection)
Accueil.add_image('fond1', img_accueil)
Accueil.add_text('bienvenue', f'{name}\nBienvenue à tous !')
Accueil.register()

# Add outro scene
Envoi = Tmp_scene('Envoi', collection)
Envoi.add_image('fond2', img_envoi)
Envoi.add_text('aurevoir', 'Bon dimanche à tous !')
Envoi.register()

# Create output zip file
output_zip = os.path.join(config['paths']['output'], f'{fname}.zip')
with ZipFile(output_zip, 'w') as myzip:
    # Écrire les images avec leurs chemins complets
    myzip.write(img_accueil, os.path.basename(img_accueil))
    myzip.write(img_envoi, os.path.basename(img_envoi))
    myzip.writestr(f'{fname}.json', json.dumps(collection.to_json()))

# Open the output directory
subprocess.Popen(f'explorer /open,"{config["paths"]["output"]}"')