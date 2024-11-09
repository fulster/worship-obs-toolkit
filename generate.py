import json
from zipfile import ZipFile
from obs_json_resources import Scene_Collection
from obs_json_resources import Tmp_scene
import unicodedata
import re
import subprocess


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


name = "L'amour divin"
fname = slugify(name)

img_accueil = 'word-light-cloud-sky-white-sunlight-688628-pxhere.com.jpg'
img_envoi = 'tree-nature-forest-horizon-light-cloud-637606-pxhere.com.jpg'

img_path = f'C:/Cultes/img/'


collection = Scene_Collection(name)


# Add scenes from ./txt directory (not ordered right now)
collection.generate_scenes_from_dir('./txt')

# Add intro scene
Accueil = Tmp_scene('Accueil',collection)
Accueil.add_image('fond1',img_path+img_accueil)
Accueil.add_text('bienvenue',f'{name}\nBienvenue à tous !')
Accueil.register()

# Add outro scene
Envoi = Tmp_scene('Envoi',collection)
Envoi.add_image('fond2',img_path+img_envoi)
Envoi.add_text('aurevoir','Bon dimanche à tous !')
Envoi.register()

# Add scenes in that order
# collection.add_scene('./txt/21-07 Qu’aujourd’hui toute la terre.txt')
# collection.add_scene('./txt/Psaume 36 O Seigneur, ta fidélité.txt')

tmp = json.dumps(collection.to_json())

with ZipFile(f'C:/Users/Etienne/Documents/Cultes/{fname}.zip', 'w') as myzip:
    myzip.write(f'img/{img_accueil}')
    myzip.write(f'img/{img_envoi}')
    myzip.writestr(f'{fname}.json',tmp)

subprocess.Popen(r'explorer /open,"C:\Users\Etienne\Documents\Cultes\"')

# with open(f'C:/Users/Etienne/Documents/Cultes/{name}.json', 'w') as outfile:
#         json.dump(collection.to_json(), outfile)