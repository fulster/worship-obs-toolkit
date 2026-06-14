---
id: D-002
title: "Support multilingue des traductions dans le format source"
status: accepted                  # validé par l'opérateur le 2026-06-14
type: cadrage
date: 2026-06-14
supersedes: []
amended_by: []
sources:
  - D-001
patterns:
  - langue-par-defaut-traductions-a-part
---

## Contexte / déclencheur

> « certains cantiques embarquaient aussi des traductions (anglaise,
> parfois allemande ou autres). Je pense qu'il faut classer la partie
> traduite dans une section à part et ne pas la servir par défaut. »

La remarque tombe pendant la **relecture du corpus** (chantier aval de
[D-001](D-001-format-source-structure-paroles.md)), au moment de
promouvoir les YAML convertis vers `stock/cantiques/`. Elle révèle un
angle mort de D-001 : le format structuré ne prévoit **qu'une seule
langue**. Or une part du corpus embarque, à la suite du français, une
ou deux **traductions** (anglais, allemand). Le convertisseur les a donc
versées dans `couplets`, et le pipeline de lecture les **projetterait
par défaut** — du texte étranger défilerait pendant le culte.

C'est un **prérequis à la promotion** : versionner le corpus en l'état
inscrirait des couplets pollués dans `stock/cantiques/`.

État courant (pré-décision, **vérifié** par scan du corpus converti le
2026-06-14 — heuristique de mots-outils FR/EN/DE, seuil ≥ 0,15) :

- **83 fichiers / 922** portent au moins un couplet en langue étrangère :
  **180 couplets EN** + **215 couplets DE** détectés.
- Les traductions sont **toujours après** la version française (ex.
  `21-20` : 7 couplets FR, puis 7 EN, puis 7 DE = 21 couplets, tous
  servis aujourd'hui). Exception relevée : de rares chants **entièrement**
  en langue non-française (ex. `12-14` « Laudate, omnes gentes », latin
  Taizé) — sans version FR à isoler.
- Deux délimiteurs **fiables** du bloc traduit dans le brut :
  **renumérotation** des couplets (le n° redescend : `[1,2,3,4,1,2,3,4]`
  pour `32-37`) et/ou **en-tête de langue** en clair (`English`,
  `Deutsch` — présents sur `32-37`, `14-09`).
- Le convertisseur actuel (`scripts/convert_cantiques.py`) collecte tous
  les `^N.` dans `couplets` sans tenir compte de la langue ni de la
  renumérotation ; le schéma (`schemas/cantique.schema.json`) n'a aucun
  champ pour une autre langue ; `expand_cantique`
  (`obs_json_resources.py`) sert **tous** les couplets.

**Question centrale** : *« Comment le format source représente-t-il un
cantique multilingue, de façon à servir le français par défaut et à
garder les traductions disponibles mais hors projection courante ? »*

## Décisions actées

### Axe 1 — Le français est la langue servie par défaut ; les traductions sont stockées à part et hors service

La version **française** reste au niveau racine du cantique (`couplets`,
`refrain`) — inchangée vs D-001. Les traductions vivent dans un champ
**séparé et optionnel** ; le pipeline de lecture les **ignore par
défaut**. Aucune traduction ne défile sans demande explicite (un
sélecteur de langue est un chantier aval, hors de ce cadrage).

Options écartées : **un fichier par langue** (`31-30.en.yaml` — rejeté :
disperse un même cantique sur plusieurs fichiers, complique la
résolution et l'édition, alors que les langues partagent numéro/titre) ;
**servir tout, trier à la projection** (rejeté : remet le tri manuel
post-import que D-001 supprime).

Pattern *« langue-par-defaut-traductions-a-part »*.

### Axe 2 — Stockage : champ `traductions`, liste de blocs par langue

Le schéma gagne un champ optionnel `traductions` : une **liste** de blocs,
chacun portant `langue` (code court : `en`, `de`…) et ses `couplets`
(plus un `refrain` optionnel). Le français racine n'est pas dupliqué ;
l'absence de `traductions` vaut « monolingue » (cas majoritaire). Forme
illustrative :

```yaml
numero: "21-20"
titre: "Que ma bouche chante ta louange"
couplets: [ ... ]          # FR — servi par défaut
refrain: |
  ...
traductions:
  - langue: en
    couplets: [ ... ]
  - langue: de
    couplets: [ ... ]
```

Ce choix préserve la compatibilité D-001 (un cantique monolingue est
identique à aujourd'hui) et reste éditable à la main.

### Axe 3 — Extraction : détection mécanique + relecture des cas ambigus

Le convertisseur sépare les blocs par **en-tête de langue** et/ou
**renumérotation** : le premier bloc → `couplets` (français), les
suivants → `traductions[langue]`, la langue venant de l'en-tête sinon
d'une détection par mots-outils. Les cas ambigus (chant entièrement
non-français, langue indéterminée, renumérotation sans en-tête) sont
**signalés au rapport** pour relecture humaine — réemploi du pattern
*« migration-scriptee-relue »* (D-001), aucun routage incertain poussé
en `stock` sans relecture.

## Conditions de légitimité

1. **Les blocs traduits sont détectables mécaniquement** (en-tête +
   renumérotation) sur une large majorité des 83 fichiers. Falsifiable :
   si la détection laisse passer beaucoup de traductions dans `couplets`
   (texte étranger projeté) ou découpe à tort des cantiques FR longs.
2. **Le français vient toujours en premier** dans les fichiers
   bilingues/trilingues. Falsifiable : un cantique où la traduction
   précède la version FR (le routage « 1er bloc = FR » casserait).
3. **Servir le français par défaut reproduit le comportement attendu** :
   aucune traduction ne défile sans demande. Falsifiable : une
   projection générée affiche de l'anglais/allemand non sollicité.
4. **Le champ `traductions` reste éditable à la main** sans outillage
   dédié (cohérent avec la condition 3 de D-001).

## Conséquences

Chantiers aval (à matérialiser en TODO portant le backlink `D-002`) :

- Étendre `schemas/cantique.schema.json` avec `traductions`
  (liste de `{langue, couplets, refrain?}`, `additionalProperties: false`).
- Adapter `scripts/convert_cantiques.py` : détection en-tête/renumérotation,
  routage FR → `couplets` / reste → `traductions`, signalement des
  ambigus au rapport.
- Confirmer que le pipeline de lecture (`expand_cantique`) **ignore**
  `traductions` par défaut (déjà le cas en ne lisant que `couplets`,
  une fois la séparation faite à la conversion).
- Hors scope ici (horizon d'évidence) : un **sélecteur de langue** à la
  projection (servir une traduction sur demande).
- Re-trancher la **promotion du corpus** vers `stock/cantiques/` une
  fois les traductions séparées (la décision de périmètre était suspendue
  à ce cadrage).

## Sources

Internes : [D-001](D-001-format-source-structure-paroles.md) (format
source qu'on étend ; réemploi du pattern *« migration-scriptee-relue »*).
Externes : aucune.

## Minutes de décision

**Q1 (Procédure)** : *« Comment procède-t-on sur le multilinguisme
(traductions) — ouvrir un ADR D-002, amender D-001, ou coder
directement ? »* → **Ouvrir D-002 puis coder**. Justification :
multilinguisme est une **question nouvelle** (nouvelle dimension du
format + politique de service), pas une correction de D-001 → ADR cadrage
neuf, lié à D-001, plutôt qu'un amendement.

**Q2 (Politique de service — arbitrage spontané de l'opérateur)** :
*« classer la partie traduite dans une section à part et ne pas la servir
par défaut »* → **traductions stockées à part, hors service par défaut**.
Justification : pendant le culte, on projette le français ; la traduction
est une ressource disponible, pas le rendu courant.

**Q3 (Sort des prières `p####`)** : *« Que faire des 38 prières
liturgiques `p####` ? »* → **Dossier séparé** (hors `stock/cantiques/`).
Note : décision de **classement de corpus**, distincte du multilinguisme ;
tracée ici car surgie dans la même session de relecture, à matérialiser
en TODO de promotion (pas un axe de ce cadrage).
