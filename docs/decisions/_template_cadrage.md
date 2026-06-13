---
id: D-XXX
title: "Cadrage — sujet en une ligne"
status: accepted                  # draft tant que non validé par l'opérateur
type: cadrage
# phase: "X.Y"                    # optionnel — jalon/roadmap si le projet en a un
date: AAAA-MM-JJ
supersedes: []
amended_by: []
sources:
  - D-YYY
patterns:
  - handle-1
  - handle-2
---

## Contexte / déclencheur

> « Citation déclencheuse (D-003) : la phrase de l'opérateur qui a
> déclenché cet ADR, **verbatim** (extrait pertinent, élision […] si
> long) — ou référence à l'artefact déclencheur (incident, mesure,
> échéance) si non conversationnel. Ne jamais fabriquer une citation. »

Pourquoi cette décision est posée maintenant. Quel état précédent l'a
rendue nécessaire (clôture d'un chantier, incident, blocage technique,
verdict empirique). Quel est l'enjeu si on ne tranche pas.

État courant (pré-décision, **vérifié** — grep / query / lecture) :

- ...
- ...

**Question centrale** : *« phrase explicite de la décision à
trancher »*.

## Décisions actées

### Axe 1 — titre court de l'axe

Justification structurée. Options écartées avec leurs raisons.

Pattern *« handle-1 »*.

### Axe 2 — titre court de l'axe

...

Pattern *« handle-2 »*.

## Conditions de légitimité

Les invariants que cette décision pose — chacun falsifiable, testable
post-hoc. Ce qu'il faudrait constater pour la remettre en cause.

1. **Condition 1** : ...
2. **Condition 2** : ...

## Conséquences

Ce que les chantiers aval doivent livrer (sans entrer dans le détail
ligne par ligne, qui appartient aux commits).

- ...
- ...

## Sources

Internes : `D-YYY`, autres docs du repo.
Externes (si applicable) : papiers, RFC, doc fournisseur.

## Minutes de décision

**Q1 (titre de la question)** : *« phrase exacte posée à
l'opérateur »* → **réponse retenue**. Justification : ...

**Q2 (titre)** : ...
