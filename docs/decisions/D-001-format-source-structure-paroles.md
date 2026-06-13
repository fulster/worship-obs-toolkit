---
id: D-001
title: "Format source structuré des paroles de cantiques"
status: accepted                  # validé par l'opérateur le 2026-06-13
type: cadrage
date: 2026-06-13
supersedes: []
amended_by: []
sources: []
patterns:
  - paroles-source-structuree-yaml
  - refrain-expanse-par-le-code
  - migration-scriptee-relue
---

## Contexte / déclencheur

> « Peux-être faudrait-il repartir au propre et convertir les .doc en
> .md ? »

La douleur immédiate qui ouvre le sujet : certains spontanés sont des
**extraits** de cantiques, mais le pipeline projette le chant entier ;
l'opérateur fait alors le ménage à la main après import (supprimer des
couplets, réordonner). En remontant la chaîne, on découvre que le
nettoyage manuel d'un cantique consiste essentiellement à **déplier le
refrain en toutes lettres après chaque couplet** — un geste mécanique
répété, et seulement 90 cantiques sur 922 ont été traités à ce jour.

La question dépasse donc la simple sélection de couplets : c'est le
**format source des paroles** qui détermine à la fois la qualité du
corpus, la faisabilité de la sélection/réordonnancement, et la quantité
de travail manuel restant.

État courant (pré-décision, **vérifié** par `find` / `grep` / diff le
2026-06-13) :

- Trois dépôts de paroles : `stock/doc/` = **922 `.doc`** Word
  « protégés » (originaux) ; `stock/txt/à nettoyer/` = **922 `.txt`**
  (conversion brute déjà faite) ; `stock/txt/` racine = **90 `.txt`**
  nettoyés à la main. Le pipeline ne consomme que ces 90.
- L'**extraction** `.doc → texte` est donc déjà faite : le goulot
  n'est pas le `.doc` protégé, c'est la **structuration/nettoyage**.
- Sur le corpus brut (922) : **676 (73 %)** ont des couplets numérotés
  `^N.` exploitables ; **246 (27 %)** n'en ont pas. Mention de refrain :
  134/922 (15 %), dont seulement 17 sous forme `(Refrain…`.
- **616 (66 %)** des bruts contiennent la séquence parasite `\r\r\n`
  (double CR) issue de la conversion Word — à normaliser en `\r\n`.
- Le modèle objet (`obs_json_resources.py:65`, classe `Scene`) avale
  les paroles en **un seul bloc texte** (`self.lyrics = '\n\n\n\n' +
  cantique.read()`) : aucune notion de couplet ni de refrain.
- Diff brut ↔ nettoyé (cantique 12-13) : le nettoyage = insertion du
  texte du refrain après chaque `Refr.`, **plus la normalisation des
  fins de ligne `\r\r\n → \r\n`** ; les crédits SECLI sont conservés.

**Question centrale** : *« Quel format de source pour les paroles
propres, et comment produire ce corpus à partir des 922 bruts, de façon
à rendre l'expansion du refrain et la sélection de couplets mécaniques
plutôt que manuelles ? »*

## Décisions actées

### Axe 1 — Format source = YAML / front-matter structuré

La source propre d'un cantique devient un fichier à **structure
explicite** : métadonnées en tête (numéro, titre, sous-titre/source,
auteur, copyright) et **couplets / refrain comme champs distincts**,
plutôt qu'un pavé de texte libre. Forme illustrative (non figée — le
schéma précis appartient à l'implémentation) :

```yaml
numero: "12-13"
titre: "Je chanterai le nom du Seigneur"
source: "d'après les psaumes 9, 59 et 90"
credits: "Noël Colombier (*1932) — © Air Libre, SECLI 09/002"
refrain: |
  Je chanterai le nom du Seigneur toujours et partout.
couplets:
  - |
    Oui, je veux jouer, je veux chanter pour le Seigneur
    ...
  - |
    Il est mon soutien, ma forteresse, mon appui,
    ...
```

Options écartées : **`.txt` + convention de balisage légère** (rejeté :
le balisage par regex sur du texte libre reste fragile, c'est ce qu'on
veut quitter) ; **`.md` à sections** (lisible sur GitHub, mais le
parsing des sections reste ambigu vs des champs YAML déterministes).
Le YAML donne une structure machine-déterministe tout en restant
éditable à la main.

Pattern *« paroles-source-structuree-yaml »*.

### Axe 2 — Le refrain est expansé par le code, stocké une seule fois

La source stocke le refrain **une fois** (champ `refrain`). C'est le
générateur qui l'insère après chaque couplet à la projection. Le
nettoyage manuel que l'opérateur faisait (déplier le refrain) devient
une **règle de présentation** appliquée par le code — supprimant le
geste répété sur les 832 cantiques restants.

Corollaire : la couche de présentation (templates `tpl/`, assemblage
dans `Scene`) devient responsable du rendu couplet+refrain ; la source
reste canonique et minimale.

Pattern *« refrain-expanse-par-le-code »*.

### Axe 3 — Sélection / réordonnancement de couplets dans la liste

Le format structuré rend la sélection triviale : dans `chants.txt` (ou
le fichier de spontanés), un cantique peut porter un **sélecteur** de
couplets, ordre respecté. Forme illustrative :

```
12-13 : 1,R,3      # couplet 1, refrain, couplet 3
35-19 : 2,1        # réordonnés
12-13              # sans sélecteur → comportement actuel (tout)
```

`R` désigne le refrain. Un cantique sans structure exploitable ignore
le sélecteur et projette tout, avec avertissement. Ceci **résout la
douleur déclencheuse** (extraits de spontanés) sans ménage post-import.
Le détail de la syntaxe (tokens exacts, refrain auto-inséré ou non)
est un chantier aval, pas figé ici.

### Axe 4 — Migration = script de conversion brut → YAML + relecture

Production du corpus propre par un **convertisseur** `brut → YAML`
(normalise `\r\r\n → \r\n` ; détecte titre, couplets `^N.`, refrain,
crédits), suivi d'une **relecture humaine**. Le script traite proprement les ~73 % réguliers ;
la relecture absorbe les ~27 % sans numérotation et les marquages de
refrain irréguliers. L'humain reste dans la boucle pour les cas
ambigus ; aucun big-bang automatique non relu n'est poussé en `stock`.

Options écartées : **au fil de l'eau** (ne migrer que le nécessaire —
rejeté comme stratégie *principale* car laisse le corpus durablement
hétérogène, mais reste un repli acceptable si le script déçoit) ;
**tout-script sans relecture** (rejeté : 27 % de casse silencieuse).

Pattern *« migration-scriptee-relue »*.

## Conditions de légitimité

1. **La structure couplet/refrain est dérivable** du brut pour une
   large majorité du corpus. Falsifiable : si le convertisseur produit
   un taux d'échec/ambiguïté nettement supérieur aux 27 % attendus sur
   un échantillon relu, l'axe 4 (et le coût de migration) est à revoir.
2. **L'expansion par le code reproduit fidèlement** le rendu que
   l'opérateur produisait à la main. Falsifiable : une projection
   générée diverge du nettoyage manuel de référence (ex. 12-13).
3. **Le format YAML reste éditable à la main** sans outillage dédié.
   Falsifiable : l'opérateur trouve l'édition d'un cantique plus
   pénible qu'avant.
4. **Le modèle « générer puis importer » est conservé** (cf. minutes
   Q1) : ce cadrage investit dans la source, pas dans un pilotage live
   d'OBS. Si l'architecture bascule vers WebSocket, l'axe 2 (qui
   expanse le refrain) reste valide mais sa couche d'application change.

## Conséquences

Chantiers aval (à matérialiser en TODO portant le backlink `D-001`) :

- Définir le **schéma YAML** précis d'un cantique (champs, multi-ligne,
  couplets indexés).
- Écrire le **convertisseur** `stock/txt/à nettoyer → <format propre>`
  + rapport des fichiers non auto-structurables (les ~246).
- Adapter le **pipeline de lecture** (`Scene` dans
  `obs_json_resources.py`) pour consommer le format structuré et
  expanser le refrain.
- Implémenter le **sélecteur de couplets** dans le parsing de
  `chants.txt` / fichier de spontanés (`generate.py`).
- Décider du sort du dossier `stock/txt/` actuel (90 fichiers nettoyés)
  vs le nouveau corpus.

## Sources

Internes : aucune (premier ADR du repo).
Externes : aucune.

## Minutes de décision

**Q1 (Architecture OBS)** : *« tu veux garder le modèle "générer puis
importer" (robuste, hors-ligne pendant le culte) ou basculer vers un
pilotage live d'OBS via WebSocket ? »* → **Garder génération + import**.
Justification : robustesse pendant le culte (zéro dépendance live), et
ça borne le périmètre de ce cadrage à la source des paroles.

**Q2 (Priorité immédiate)** : *« quelle douleur soulager en premier ? »*
→ **Couplets des spontanés**. Justification : douleur récurrente et
concrète ; en remontant sa cause, on a révélé le vrai sujet (format
source), d'où ce cadrage.

**Q3 (Format cible)** : *« on garde du .txt avec convention légère, ou
on passe à un vrai format structuré (.md ou .yaml/front-matter) ? »* →
**.yaml / front-matter**. Justification : structure machine-déterministe
pour l'expansion et la sélection, tout en restant éditable à la main.

**Q4 (Migration)** : *« stratégie de migration des 922 vers le format
propre ? »* → **Script + relecture**. Justification : automatise les
~73 % réguliers, garde l'humain sur les ~27 % ambigus ; pas de big-bang
non relu.
