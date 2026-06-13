# Utilisation du fichier chants.txt

## Présentation

Le script `generate2.py` a été modifié pour accepter un fichier `chants.txt` en entrée. Ce fichier contient une liste de cantiques et de psaumes à rechercher spécifiquement dans le dossier `stock/txt`, plutôt que d'utiliser tous les fichiers du répertoire configuré dans `config.json`.

## Fonctionnalité spéciale pour les cantiques spontanés

Si la première ligne du fichier `chants.txt` est au format `[SPONTANES] XXX` (où XXX est une chaîne de caractères), le script considère que:
1. Un fichier supplémentaire nommé `[SPONTANES] XXX.txt` existe à la racine du projet
2. Ce fichier contient des cantiques complémentaires à inclure dans la collection

Par exemple, si la première ligne est `[SPONTANES] ASCENSION_PENTECOTE`, le script inclura également les cantiques listés dans le fichier `[SPONTANES] ASCENSION_PENTECOTE.txt`.

Cette fonctionnalité est utile pour inclure rapidement un ensemble de cantiques spécifiques à un temps liturgique ou à un thème particulier.

## Format des fichiers

### Format du fichier chants.txt

Le format du fichier principal `chants.txt` est le suivant :

```
21-17 « Nous voici rassemblé en ton nom » (1)
35-19 « Pour que le jour qui se léve» (1,2,3)
35-11 « Souffle du Dieu vivant » (1,2)
Psaume 8 « Ton nom, Seigneur, est un nom magnifique » (1,2,3)
...
```

Chaque ligne peut contenir soit :

### Pour les cantiques standard :
- Le numéro du cantique (ex: "21-17")
- Le titre entre guillemets (optionnel pour la recherche)
- Les numéros de couplets entre parenthèses (optionnel pour la recherche)

**Note importante :** Seul le numéro du cantique (au format "XX-XX") est utilisé pour rechercher le fichier correspondant dans le dossier `stock/txt`. Le script extrait automatiquement ce numéro au début de chaque ligne, même s'il n'est pas suivi d'un espace, puis recherche les fichiers contenant ce numéro.

### Pour les psaumes :
- Le mot "Psaume" suivi d'un numéro, éventuellement avec un suffixe alphabétique (ex: "Psaume 8" ou "Psaume 47A")
- Le titre entre guillemets (optionnel pour la recherche)
- Les numéros de couplets entre parenthèses (optionnel pour la recherche)

**Note sur les psaumes :** Lorsque le script détecte une ligne commençant par "Psaume X", il convertit ce format en "Ps XXX" (où XXX est le numéro formaté sur 3 chiffres avec des zéros à gauche). Par exemple, "Psaume 8" sera recherché comme "Ps 008" dans le dossier `stock/txt`. Pour les psaumes avec un suffixe alphabétique (comme "Psaume 47A"), le script préserve le suffixe et recherche "Ps 047A".

## Configuration

Par défaut, le script recherche les cantiques dans le dossier `stock/txt`. Vous pouvez personnaliser ce chemin en ajoutant une clé `stock_txt` dans la section `paths` de votre fichier `config.json` :

```json
{
    "paths": {
        "images": "/chemin/vers/dossier/images",
        "output": "/chemin/vers/dossier/output",
        "txt": "./txt",
        "stock_txt": "./stock/txt"
    },
    ...
}
```

## Fonctionnement

Le script :
1. Lit le fichier `chants.txt`
2. Pour chaque ligne :
   - Si elle commence par un format "XX-XX", extrait ce numéro de cantique
   - Si elle commence par "Psaume X", convertit en format "Ps XXX" (avec zéros de remplissage)
3. Recherche un fichier contenant ce numéro dans le dossier `stock/txt`
4. Si trouvé, ajoute ce cantique ou psaume à la collection de scènes
5. Si une erreur se produit ou si aucun cantique n'est trouvé, utilise le comportement par défaut (tous les fichiers du répertoire `txt`)

### Format du fichier de cantiques spontanés

Le fichier de cantiques spontanés (exemple: `[SPONTANES] ASCENSION_PENTECOTE.txt`) suit un format similaire à `chants.txt`, mais comprend une fonctionnalité spéciale. Chaque ligne peut contenir:
- Le numéro du cantique (ex: "35-01")
- Le titre du cantique (sans guillemets)
- Des marqueurs spéciaux (#1, #2, etc.) qui indiquent où insérer les cantiques du fichier principal

**Fonctionnalité d'entrelacement**: Les marqueurs #n dans le fichier de cantiques spontanés servent de points d'insertion pour les cantiques du fichier principal `chants.txt`. Par exemple, le marqueur `#1` indique d'insérer le premier cantique du fichier principal à cet emplacement.

Exemple de fichier spontanés:
```
35-01 Viens, Saint-Esprit, Dieu créateur
#1
43-03 - Du fond de ma souffrance
#2
51-13 - Dieu ma joie
#3
36-24 - Tous unis dans l'Esprit
```

Si le fichier `chants.txt` contient:
```
[SPONTANES] ASCENSION_PENTECOTE
21-17 « Nous voici rassemblé en ton nom »
Psaume 8 « Ton nom, Seigneur, est un nom magnifique »
35-11 « Souffle du Dieu vivant »
```

Le résultat final après entrelacement sera:
```
35-01 Viens, Saint-Esprit, Dieu créateur
21-17 « Nous voici rassemblé en ton nom »
43-03 - Du fond de ma souffrance
Psaume 8 « Ton nom, Seigneur, est un nom magnifique »
51-13 - Dieu ma joie
35-11 « Souffle du Dieu vivant »
36-24 - Tous unis dans l'Esprit
```

## Exemple d'utilisation

1. Créez un fichier `chants.txt` à la racine du projet
2. Si vous souhaitez inclure des cantiques spontanés avec entrelacement, commencez par une ligne spéciale:
   ```
   [SPONTANES] ASCENSION_PENTECOTE
   21-17 « Nous voici rassemblé en ton nom » (1)
   Psaume 8 « Ton nom, Seigneur, est un nom magnifique » (1,2,3)
   35-11 « Souffle du Dieu vivant » (1,2)
   ```
3. Créez le fichier correspondant `[SPONTANES] ASCENSION_PENTECOTE.txt` à la racine avec des marqueurs #n pour indiquer où insérer les cantiques principaux:
   ```
   35-01 Viens, Saint-Esprit, Dieu créateur
   #1
   43-03 - Du fond de ma souffrance
   #2
   51-13 - Dieu ma joie
   #3
   36-24 - Tous unis dans l'Esprit
   ```
4. Exécutez le script :
   ```
   python generate2.py "Nom du culte"
   ```

Le script générera un fichier ZIP contenant les cantiques entrelacés selon l'ordre défini par les marqueurs dans le fichier de spontanés, ainsi que les scènes d'accueil et d'envoi habituelles.

**Note:** Si le fichier spontanés contient plus de marqueurs #n que de cantiques dans le fichier principal, les marqueurs excédentaires seront ignorés. À l'inverse, si le fichier principal contient plus de cantiques que de marqueurs dans le fichier spontanés, les cantiques restants seront ajoutés à la fin de la liste.
