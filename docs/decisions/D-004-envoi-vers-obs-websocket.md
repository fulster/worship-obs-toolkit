---
id: D-004
title: "Envoi des scènes vers OBS via obs-websocket"
status: accepted                  # validé par l'opérateur le 2026-06-14
type: cadrage
date: 2026-06-14
supersedes: []
amended_by: []
sources:
  - D-001
  - D-003
patterns:
  - envoi-obs-additif-au-zip
  - push-obs-par-rejeu-du-json
---

## Contexte / déclencheur

> « ok... on se lance dans le websocket ? »

L'interface de préparation (v1.1, [D-003](D-003-interface-de-preparation-des-cultes.md))
compose un culte et produit un `.zip` que l'opérateur **importe manuellement**
dans OBS (*Scene Collection → Import → choisir le `.json`*). C'est la dernière
friction du flux. [D-003](D-003-interface-de-preparation-des-cultes.md) (axe 4)
avait **différé** l'envoi direct via obs-websocket en notant qu'il
« rouvrira la minute Q1 de D-001 ».

Précision qui désamorce ce point : ce push se fait à la **préparation**, pas
pendant la projection. Une fois les scènes dans OBS, la projection reste
**hors-ligne** comme aujourd'hui — donc D-001 n'est pas renversé, on **ajoute
une voie d'import**.

État courant (pré-décision, **vérifié**) :

- Le pipeline produit déjà un **JSON de collection OBS complet**
  (`obs_json_resources.Scene_Collection.to_json()`), exactement le format que
  lit l'*Import* d'OBS.
- obs-websocket **ne sait pas « importer une collection »** : il faut soit la
  **recréer via l'API**, soit déposer le `.json` dans le dossier d'OBS.
- **Spike obs-websocket le 2026-06-14** (sur le poste cible, OBS **30.1.0**,
  websocket **5.4.2**) : `create_scene_collection`, `create_scene`,
  `create_input` (texte `text_gdiplus_v2` et `image_source`),
  `create_source_filter` (`scroll_filter`) **fonctionnent tous**. La
  recréation d'une collection dédiée par l'API est donc **faisable**.
- La préparation se fait **au poste de l'église, OBS ouvert** : serveur web et
  OBS sont **co-localisés** (connexion `localhost`).

**Question centrale** : *« Comment envoyer les scènes d'un culte directement
dans OBS depuis l'interface, sans sacrifier la robustesse hors-ligne ni la
préparation à l'avance ? »*

## Décisions actées

### Axe 1 — « Envoi vers OBS » **en plus** du `.zip`, jamais à la place

L'interface gagne un bouton « Envoyer vers OBS » **à côté** de « Générer le
`.zip` ». Le `.zip` reste la voie **par défaut, suffisante seule** : prépa à
l'avance, hors-ligne, depuis n'importe quel appareil, et secours si OBS est
indisponible. Le push n'est utilisable que quand OBS est **ouvert et joignable**.

Options écartées : **remplacer** le `.zip` par le push (rejeté : perd la prépa
async / hors machine OBS et la voie de secours, et créerait une dépendance là
où D-001 n'en voulait pas).

Pattern *« envoi-obs-additif-au-zip »*.

### Axe 2 — Recréer une collection OBS dédiée, par **rejeu du JSON généré**

Le push crée une **nouvelle collection de scènes** (nommée d'après le culte,
isolée — comme le fait l'import du `.zip`, sans toucher au montage de base de
l'opérateur), puis la **remplit en rejouant le JSON déjà produit** par le
pipeline : un traducteur `JSON de collection → requêtes obs-websocket` (sources,
scènes, items + transformations, filtres, ordre). **Aucune logique de
construction de scènes n'est ré-implémentée** : la génération reste l'unique
source de vérité.

Options écartées : **(B) écrire le `.json` dans le dossier des collections
d'OBS + bascule** (rejeté comme voie principale : détection « à chaud »
incertaine, et OBS réécrit les fichiers de collection à la fermeture — fragile) ;
**recréation ad-hoc** ré-implémentant les scènes côté websocket (rejeté :
duplication, divergence garantie avec `obs_json_resources`).

Pattern *« push-obs-par-rejeu-du-json »*.

### Axe 3 — Pile : obs-websocket v5, serveur local, configurable

- **obs-websocket v5** (OBS ≥ 28, serveur intégré), client Python
  **`obsws-python`** (dépendance runtime).
- Connexion **locale** (`localhost`), serveur web et OBS sur le **même poste**.
- Paramètres de connexion (`host` / `port` / `password`, activation) dans
  `config.json` (section `obs`) ; l'envoi est **désactivable**.
- Échec de joignabilité (OBS fermé, mauvais port/mot de passe) : message clair
  côté interface, sans bloquer le reste (le `.zip` reste disponible).

## Conditions de légitimité

1. **Le `.zip` reste la voie par défaut et autosuffisante.** Falsifiable : si
   projeter un culte requiert le push (OBS allumé à la prépa) plutôt que l'import.
2. **La projection reste hors-ligne** : le push est strictement prép-time, aucune
   dépendance websocket pendant le culte. Falsifiable : un besoin de connexion
   live en projetant.
3. **Le push rejoue le JSON généré**, sans logique de scène dupliquée.
   Falsifiable : du code de construction de scènes apparaît côté push, divergeant
   de `obs_json_resources`.
4. **obs-websocket v5 disponible et serveur local joignable** (OBS ≥ 28,
   co-localisé). Falsifiable : OBS plus ancien, ou OBS sur une autre machine.

## Conséquences

Chantiers aval (à matérialiser en TODO portant le backlink `D-004`) :

- Dépendance **`obsws-python`**.
- **Traducteur** `JSON de collection → obs-websocket` (créer collection, sources,
  scènes, items + transformations, filtres, ordre des scènes) — testé en direct
  contre l'OBS du poste.
- Endpoint **`/api/envoyer-obs`** (compose → génère le JSON → push) + gestion
  d'erreurs (OBS injoignable).
- **UI** : bouton « Envoyer vers OBS » à côté de « Générer », avec retour clair.
- **Config** : section `obs` dans `config.json` / `config.json.example`, +
  procédure (activer le serveur WebSocket d'OBS) dans `docs/deploiement.md`.
- Note : la source caméra est recréée avec l'`device_id` des templates `tpl/`
  (même situation qu'avec le `.zip`).

## Sources

Internes : [D-001](D-001-format-source-structure-paroles.md) (modèle « générer
puis importer », **préservé** : le push est additif et prép-time),
[D-003](D-003-interface-de-preparation-des-cultes.md) (interface, axe 4 qui
différait ce chantier). Externes : obs-websocket v5 (protocole), `obsws-python`.

## Minutes de décision

**Q1 (Périmètre)** : *« Le push WebSocket : en plus du `.zip`, ou à la place ? »*
→ **En plus**. Justification : préserve la prépa à l'avance / hors machine OBS,
le secours, et la robustesse hors-ligne de D-001.

**Q2 (Contexte de préparation)** : *« Au moment de préparer, OBS tourne-t-il sur
la même machine/réseau ? »* → **Oui, au poste de l'église**. Justification :
serveur web et OBS co-localisés → connexion `localhost`, push toujours possible.

**Q3 (Approche technique)** : recommandation **recréer via l'API en rejouant le
JSON généré** (vs déposer le fichier de collection, vs recréation ad-hoc),
**confirmée faisable par le spike** du 2026-06-14 (toutes les requêtes
nécessaires fonctionnent sur OBS 30.1) et retenue.
