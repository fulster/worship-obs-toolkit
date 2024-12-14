# Worship OBS Toolkit

Un outil pour générer automatiquement des scènes OBS Studio pour les cultes.

## Description

Cet outil permet de :
- Générer une collection de scènes OBS pour les cultes
- Créer automatiquement une scène d'accueil et d'envoi
- Intégrer les cantiques à partir de fichiers texte
- Produire un fichier ZIP contenant toutes les ressources nécessaires

## Configuration

Le fichier `config.json` permet de personnaliser les chemins et les images utilisés :

```json
{
    "paths": {
        "images": "C:/Cultes/img/",        // Dossier contenant les images
        "output": "C:/Users/.../Cultes",   // Dossier de sortie des fichiers ZIP
        "txt": "./txt"                     // Dossier contenant les fichiers texte des cantiques
    },
    "images": {
        "accueil": "image-accueil.jpg",    // Image pour la scène d'accueil
        "envoi": "image-envoi.jpg"         // Image pour la scène d'envoi
    }
}
```

## Structure des fichiers

```
worship-obs-toolkit/
├── config.json          # Configuration de l'application
├── generate.py          # Script principal
├── obs_json_resources.py# Classes et ressources OBS
├── img/                 # Images utilisées dans les scènes
├── txt/                 # Fichiers texte des cantiques
└── tpl/                 # Templates JSON pour OBS
```

## Utilisation

1. Configurez les chemins dans `config.json`
2. Placez les fichiers des cantiques dans le dossier `txt/`
3. Exécutez le script avec le nom du culte :

```bash
python generate.py "Nom du Culte"
```

Le script générera un fichier ZIP dans le dossier de sortie configuré, contenant :
- La collection de scènes OBS
- Les images nécessaires
- Les configurations des sources

## Format des fichiers de cantiques

Les fichiers texte des cantiques doivent suivre ce format :
```
Titre du cantique
Auteur / Source
Paroles du cantique...
```

## Dépendances

- Python 3.6+
- OBS Studio