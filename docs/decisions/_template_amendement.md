---
id: D-XXX
title: "Amendement D-YYY — sujet de l'amendement"
status: accepted
type: amendement
# phase: "X.Y"                    # optionnel
date: AAAA-MM-JJ
amends: D-YYY                     # l'ADR amendé — mettre à jour son
                                  # amended_by + status au même commit
supersedes: []
amended_by: []
sources:
  - D-YYY
patterns: []
---

## Déclencheur de l'amendement

> « Citation déclencheuse (D-003) : la phrase de l'opérateur qui a
> déclenché cet amendement, **verbatim** (extrait pertinent, élision
> […] si long) — ou référence à l'artefact déclencheur (incident,
> mesure, échéance) si non conversationnel. Ne jamais fabriquer une
> citation. »

Pourquoi D-YYY doit être amendé. Quel élément nouveau (incident,
mesure empirique, retour terrain, contradiction observée) le rend
nécessaire.

## Modification actée

Ce qui change concrètement par rapport à D-YYY. Format préféré :
*« avant : ... ; après : ... »*.

### Axe N de D-YYY (impacté)

**Avant** : ...

**Après** : ...

**Justification du changement** : ...

## Sections D-YYY impactées vs préservées

- **Impacté** : Axe N (cf. ci-dessus).
- **Préservé** : les autres axes — invariants.
- **Conditions de légitimité** : inchangées / changement n°K.

## Conséquences

Chantiers / commits affectés par l'amendement.

## Sources

Internes : `D-YYY`, autres ADR amont.

## Minutes de décision

**Q1 (titre)** : *« phrase exacte posée à l'opérateur »* →
**réponse retenue**. Justification : ...
