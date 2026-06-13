---
id: D-XXX
title: "Verdict — sujet en une ligne"
status: accepted
type: closure
# phase: "X.Y"                    # optionnel
date: AAAA-MM-JJ
verdict: ACCEPTED                 # ACCEPTED | REJECTED | ACCEPTED-WITH-CAVEAT | INCONCLUSIVE
supersedes: []
amended_by: []
sources:
  - D-YYY
patterns:
  - handle-1
---

## Contexte / déclencheur

> « Citation déclencheuse (D-003) : la phrase de l'opérateur qui a
> déclenché cet ADR, **verbatim** (extrait pertinent, élision […] si
> long) — ou référence à l'artefact déclencheur (incident, mesure,
> échéance) si non conversationnel. Ne jamais fabriquer une citation. »

Quelle hypothèse / piste / expérimentation a été testée. Comment elle
a été cadrée (ADR amont).

## Verdict

**ACCEPTED / REJECTED / ACCEPTED-WITH-CAVEAT / INCONCLUSIVE** — résumé
en 1-2 phrases. Les nuances vont ici, pas dans l'enum du frontmatter.

## Évidence empirique

Mesures, chiffres, identifiants de runs, configurations de test,
fenêtres temporelles. Tout ce qui rend le verdict reproductible.

- Métrique 1 : ...
- Métrique 2 : ...

Références : `<run-id / commit / dataset>`.

## Implications

Ce que ce verdict ouvre / ferme :

- Ouvre : nouvelle piste, nouveau chantier, nouvel ADR.
- Ferme : option écartée, candidate rejetée, ressource libérée.
- Reste ouvert : sous-questions non tranchées par ce verdict.

## Patterns inscrits

- *« handle-1 »* : explication ...

## Sources

Internes : `D-YYY`, autres docs du repo.
Externes : papiers, données externes.

## Minutes de décision

**Q1 (titre)** : *« phrase exacte posée à l'opérateur »* →
**réponse retenue**. Justification : ...
