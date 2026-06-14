# Decision Records (ADR)

Index des décisions structurantes du repo. Une décision = un fichier
`D-NNN-<kebab-titre>.md`.

Guide méthodologique (quand ouvrir un ADR, workflows, anti-patterns) :
[adr-guide.md](adr-guide.md) *(adaptez ce lien à l'emplacement du
guide dans votre repo)*.

## Conventions

- **Filename** : `D-NNN-<kebab-titre>.md`. Le numéro `D-NNN` est
  l'identifiant primaire, invariant à perpétuité — jamais de
  renumérotation, les gaps sont acceptés.
- **Frontmatter YAML obligatoire** : `id`, `title`, `status`, `type`,
  `date`, `supersedes`, `amended_by`, `sources`, `patterns`
  (+ `verdict` pour les closures, `amends` pour les amendements,
  `phase` optionnel). Schema : `adr-frontmatter.schema.json`.
- **3 templates** : `_template_cadrage.md` (axes structurés),
  `_template_closure.md` (verdict empirique),
  `_template_amendement.md` (modification ciblée d'un ADR antérieur).
- **Statuts** : `draft` | `accepted` | `amended` | `superseded` |
  `deprecated`.
- **Types** : `cadrage` | `closure` | `amendement`.
- **Discipline** : un ADR = un commit, cette table mise à jour au même
  commit. Un amendement met à jour le frontmatter de l'ADR amendé
  (`amended_by`, `status`) au même commit, sans toucher son corps.

## Index

Triées par ID décroissant (le plus récent en haut).

| ID | Titre | Status | Type | Date |
|---|---|---|---|---|
| [D-002](D-002-support-multilingue-traductions.md) | Support multilingue des traductions dans le format source | accepted | cadrage | 2026-06-14 |
| [D-001](D-001-format-source-structure-paroles.md) | Format source structuré des paroles de cantiques | accepted | cadrage | 2026-06-13 |
