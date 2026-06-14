# Déploiement sur le poste de l'église

Installer l'interface de préparation des cultes sur le **PC de retransmission**
(machine dédiée/partagée), de façon à ce qu'elle soit **toujours disponible** :
serveur démarré automatiquement (caché) à l'ouverture de session, et un raccourci
Bureau qui ouvre l'interface.

> Le développement se fait sur un autre poste. Ce document concerne **le poste
> de l'église**. L'interface reste **locale** (jamais exposée sur internet),
> cf. [D-003](decisions/D-003-interface-de-preparation-des-cultes.md).

## Prérequis (une fois)

1. Installer **[uv](https://docs.astral.sh/uv/)** (gestion de l'environnement Python).
2. Copier le dépôt sur le poste (ex. `C:\worship-obs-toolkit`).
3. Créer `config.json` à partir de `config.json.example` et renseigner la clé
   API Unsplash (cf. [README](../README.md) § Configuration).

## Installation

Double-cliquer **`installer-poste-eglise.bat`**. Il :

- crée un raccourci **« Préparer un culte »** sur le Bureau (ouvre
  `http://127.0.0.1:5000`) ;
- active le **démarrage automatique** du serveur (fenêtre cachée) à chaque
  ouverture de session (via un `.vbs` dans le dossier *Démarrage*) ;
- prépare l'environnement (`uv sync`) et **démarre le serveur immédiatement**.

C'est tout : double-cliquer le raccourci Bureau ouvre l'interface, et le serveur
sera relancé tout seul à chaque session.

## Utilisation quotidienne

- **Ouvrir l'interface** : double-clic sur **« Préparer un culte »** (Bureau).
- Le serveur tourne en arrière-plan (aucune fenêtre visible).

## Mises à jour

1. Lancer **`arreter-serveur.bat`** (arrête le serveur).
2. Mettre à jour les fichiers du dépôt (copie / `git pull`).
3. Relancer **`serveur.bat`** *(ou simplement rouvrir une session Windows)*.

> Après une modification du corpus (`stock/cantiques/`), un redémarrage du
> serveur est nécessaire : l'index est chargé en mémoire au démarrage.

## Désinstallation

Double-cliquer **`desinstaller-poste-eglise.bat`** : retire le démarrage
automatique et le raccourci Bureau (le dépôt et le corpus restent en place).

## Scripts fournis

| Fichier | Rôle |
|---|---|
| `installer-poste-eglise.bat` | Installation sur le poste (à lancer une fois). |
| `serveur.bat` | Démarre le serveur en mode production (waitress), sans navigateur. |
| `arreter-serveur.bat` | Arrête le serveur (avant une mise à jour). |
| `desinstaller-poste-eglise.bat` | Retire démarrage auto + raccourci Bureau. |
| `Preparer un culte.bat` | Lancement manuel **avec** ouverture du navigateur (dépannage / dev). |

## Détails techniques

- Le serveur de production est **waitress** (WSGI pur Python, sans compilation),
  activé par la variable d'environnement `WOTK_PROD=1` (positionnée par
  `serveur.bat`). En développement, `uv run python webapp/app.py` lance le
  serveur Flask intégré (`WOTK_DEBUG=1` pour le rechargement automatique).
- Le démarrage caché passe par un `.vbs`
  (`WScript.Shell.Run "... serveur.bat", 0, False`) déposé dans le dossier
  *Démarrage* de l'utilisateur — pas de droits administrateur requis.
