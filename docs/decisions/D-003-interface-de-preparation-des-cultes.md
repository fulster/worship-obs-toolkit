---
id: D-003
title: "Interface de préparation des cultes (app web locale)"
status: accepted                  # validé par l'opérateur le 2026-06-14
type: cadrage
date: 2026-06-14
supersedes: []
amended_by: []
sources:
  - D-001
  - D-002
patterns:
  - preparation-web-locale-non-publique
  - interface-reutilise-le-pipeline
---

## Contexte / déclencheur

> « ma question est : comment mettre ce kit à disposition d'utilisateurs
> non informaticiens. »

Le kit atteint la **v1.0** : pipeline complet, corpus structuré peuplé,
génération de culte validée en réel. Mais son usage reste **réservé à un
profil technique** : éditer `chants.txt` (syntaxe des sélecteurs `(1,3)`,
marqueurs de spontanés `#n`) puis lancer `generate.py` en ligne de
commande. Or les **préparateurs** visés sont des bénévoles non
informaticiens, **en rotation**. Sans interface, l'adoption bute sur la
courbe d'apprentissage et la fragilité de l'édition d'un fichier texte.

État courant (pré-décision, **vérifié** le 2026-06-14) :

- Le point d'entrée `generate.py` est une **CLI procédurale** (niveau
  module) : lit `chants.txt`, résout les numéros contre
  `stock/cantiques/`, produit un `.zip` (JSON + images) à importer
  manuellement dans OBS.
- Deux **rôles distincts** : *préparer* le culte (composer la liste —
  touche au kit) vs *projeter* (basculer les scènes dans OBS — ne touche
  pas au kit). Seuls les préparateurs ont besoin d'une interface.
- Le corpus est **sous licence** : **652 / 883** cantiques (74 %) portent
  des crédits/autorisations explicites (SECLI, Olivétan, Air Libre, ©).
  Une diffusion **publique** de ces paroles serait de la distribution,
  hors du cadre de ces autorisations d'usage paroissial.
- [D-001](D-001-format-source-structure-paroles.md) a acté le modèle
  **« générer puis importer »** (robuste, hors-ligne pendant le culte ;
  minute Q1), contre un pilotage live d'OBS.

**Question centrale** : *« Sous quelle forme outiller la préparation des
cultes pour des bénévoles non techniques, sans sacrifier la robustesse
hors-ligne ni s'exposer au droit d'auteur ? »*

## Décisions actées

### Axe 1 — Une application web **locale**, non publique

L'interface est une **app web servie en local** (sur le poste de
préparation / le LAN de la paroisse), accessible au navigateur. Elle
n'est **pas** publiée sur internet.

Options écartées : **service web public** (rejeté : diffuse des paroles
sous licence à tout internet — distribution hors autorisations ; plus
coût d'hébergement et de maintenance sysadmin) ; **CLI + formation seule**
(rejeté comme cible : la difficulté n'est pas « lancer une commande »
mais *composer la liste* — numéros, sélecteurs, spontanés — qu'une
interface doit absorber ; reste un repli immédiat acceptable le temps du
développement) ; **app de bureau packagée** (`.exe`) — viable et
hors-ligne, mais moins accessible (un seul poste) qu'une page servie sur
le réseau pour des préparateurs en rotation.

Pattern *« preparation-web-locale-non-publique »*.

### Axe 2 — Stack simple, maintenable en solo

Backend **Python léger** (ex. Flask) qui **réutilise** la logique de
génération existante ; frontend **léger** (HTML/JS sans framework lourd).

Options écartées : **SPA à gros framework** (rejeté : fardeau de
maintenance disproportionné pour quelques utilisateurs sur un LAN, projet
tenu en solo par un bénévole).

### Axe 3 — L'interface réutilise le pipeline, ne le réécrit pas

La génération reste assurée par le code existant (`generate.py` /
`obs_json_resources.py`) ; l'interface l'**orchestre** (sélection des
chants → composition d'une liste → appel du pipeline → `.zip`). Une seule
source de vérité pour la logique de génération.

Corollaire : `generate.py`, aujourd'hui purement procédural au niveau
module, devra exposer une **fonction appelable** (refactor minimal) pour
être pilotable par le backend sans dupliquer la logique.

Pattern *« interface-reutilise-le-pipeline »*.

### Axe 4 — Lien OBS : `.zip` + import (WebSocket différé)

La v1 produit un `.zip` que l'utilisateur importe dans OBS, **comme
aujourd'hui** — modèle « générer puis importer » de D-001 préservé
(robuste, hors-ligne). Le **push direct via obs-websocket** est
explicitement **différé** : évolution ultérieure si le besoin se
confirme, qui rouvrira la minute Q1 de D-001.

### Axe 5 — Périmètre v1 = composer le culte ; persistance des cultes

La v1 couvre **uniquement la composition** d'un culte : chercher un
cantique (titre/numéro), l'ajouter, choisir/réordonner les couplets
(sélecteur), gérer les spontanés, générer. Les cultes préparés sont
**sauvegardés** (sauver/rouvrir/modifier — utile pour une rotation de
préparateurs).

Hors périmètre v1 : l'**édition du corpus** (relecture/correction des
YAML) reste hors interface (fichiers + `docs/relecture-corpus.md`).

## Conditions de légitimité

1. **L'interface reste d'usage local/paroissial**, jamais exposée
   publiquement. Falsifiable : un déploiement public servant le corpus
   sous licence — la condition (et le risque juridique) est violée.
2. **La génération reste hors-ligne et robuste** pendant le culte : la
   projection ne dépend pas de l'interface ni du réseau (modèle D-001).
   Falsifiable : une panne réseau/serveur empêche de projeter un culte
   déjà généré.
3. **La logique de génération n'est pas dupliquée** : l'interface appelle
   le pipeline existant. Falsifiable : du code de construction de scènes
   réapparaît côté backend, divergeant de `obs_json_resources.py`.
4. **La maintenance reste tenable en solo** : pas de dépendance lourde
   imposant un savoir-faire que l'opérateur n'a pas. Falsifiable :
   l'opérateur ne peut plus faire évoluer l'interface sans aide.

## Conséquences

Chantiers aval (à matérialiser en TODO portant le backlink `D-003`) :

- **Rendre `generate.py` appelable** : extraire une fonction
  `generer_culte(titre, entrees, ...)` réutilisable (refactor du
  procédural niveau-module), sans changer le comportement CLI.
- **Backend** (Flask) : endpoints recherche corpus / composition /
  génération du `.zip` ; stockage des cultes préparés.
- **Frontend** léger : recherche + ajout de cantiques, sélecteur de
  couplets visuel, réordonnancement, gestion des spontanés, bouton
  « Générer », téléchargement du `.zip`.
- **Sauvegarde** des cultes (format et emplacement à définir).
- **Doc de déploiement local** (lancer le serveur, accès LAN) pour des
  non-techniciens.
- Différé : **push obs-websocket** (rouvre D-001 Q1).

## Sources

Internes : [D-001](D-001-format-source-structure-paroles.md) (modèle
« générer puis importer », réutilisé), [D-002](D-002-support-multilingue-traductions.md)
(corpus servi). Externes : aucune.

## Minutes de décision

**Q1 (Forme cible)** : *« Vers quelle forme veux-tu qu'on aille —
app web locale, app de bureau, ou CLI + formation ? »* → **App web
locale**. Justification : UX accessible pour des préparateurs en
rotation, sans les coûts/risques d'un service public (droit d'auteur,
hébergement) ni la limite mono-poste d'une app de bureau.

**Q2 (Préparateurs)** : *« Qui prépare les cultes ? »* → **Quelques
personnes en rotation**. Justification : motive une interface guidée et
accessible (vs un outil mono-utilisateur), et la sauvegarde des cultes.

**Q3 (Lien OBS)** : *« Comment l'interface envoie-t-elle vers OBS ? »* →
**`.zip` + import d'abord, WebSocket plus tard**. Justification :
préserve la robustesse hors-ligne de D-001 ; le push live est une
évolution, pas un prérequis.

**Q4 (Périmètre v1)** : *« Que couvre la v1 ? »* → **Composer le culte
seulement**. Justification : livrer la valeur (composition guidée) sans
le coût/risque d'une édition de corpus en ligne.

**Q5 (Sauvegarde)** : *« L'interface sauvegarde-t-elle les cultes ? »* →
**Oui, sauver/rouvrir**. Justification : adapté à une rotation de
préparateurs (réutilisation, reprise d'un brouillon).
