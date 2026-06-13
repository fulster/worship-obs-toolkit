# Guide ADR — méthodologie opérationnelle

Ce document explique **comment ouvrir, amender et maintenir** les
décisions structurantes d'un repo (les « ADR », identifiées `D-NNN`).
Il est destiné aux contributeurs humains et aux assistants IA.

Dans le repo qui adopte la convention, les ADR vivent sous
`docs/decisions/` (chemin recommandé ; adaptez si besoin, mais un seul
dossier plat). Le `README.md` de ce dossier sert d'**index** ; le
présent fichier sert de **guide méthodologique**.

## 1. Quoi et pourquoi

Un **ADR** (Architecture Decision Record) trace une décision
structurante : son contexte, les options envisagées, le choix retenu,
les conditions de légitimité. Une décision = un fichier
`D-NNN-<kebab-titre>.md`.

**Objectif** : qu'un collègue (humain ou IA) puisse, 6 mois plus tard,
comprendre **pourquoi** une décision a été prise, **dans quelles
conditions** elle reste valide, et **quels patterns** elle pose pour
les décisions futures.

**Posture par défaut** : ouvrir un ADR est une action **fréquente et
bon marché** (~10-20 min pour un ADR léger), pas un événement
cérémoniel. Sur un projet actif, plusieurs ADR par semaine est une
cadence normale. Le réflexe sur une décision structurante doit être
*« j'ouvre un ADR »*, pas *« est-ce que ça mérite vraiment ? »*.
L'arbre de décision §2 existe pour trier les cas litigieux, **pas**
pour décourager l'ouverture.

## 2. Quand ouvrir un ADR (arbre de décision)

Cas où l'ADR est **clairement requis** (ne te pose pas la question) :

- Cadrage d'un chantier, d'une phase ou d'un jalon significatif
- Verdict empirique d'une expérimentation, d'un POC, d'un benchmark
  (concluant ou non)
- Amendement d'un ADR antérieur (un de ses axes, conditions ou
  prémisses tombe)
- Décision sur un invariant du système (sécurité, gouvernance,
  architecture, contrat de données, API publique)
- Choix d'une dépendance externe non triviale (lib, service, API)
- Pivot méthodologique en cours de route
- Bug fix qui révèle un choix de design (ex. *« pourquoi ce seuil à
  1000 et pas 2000 »* devient un mini-ADR si le seuil est load-bearing)

Cas où l'ADR est **clairement excessif** (ne le fais pas) :

- Refactor pur sans changement de comportement observable
- Choix d'une bibliothèque parfaitement standard et substituable
  (et l'application répétée d'une dépendance déjà actée par un ADR
  ne nécessite pas un nouvel ADR à chaque usage)
- Renommage de variables / fix de typo
- Modification de docstring ou de commentaire sans implication
  fonctionnelle
- Travail du type *« j'applique le pattern déjà acté par D-YYY »*

Cas litigieux — pose-toi alors ces 2 questions :

1. **Quelqu'un (toi dans 6 mois, un collègue, une IA en session
   future) aura-t-il besoin de cette décision pour comprendre une
   autre décision ?**
   - **Oui** → ouvre l'ADR.
   - **Non** → un commit bien rédigé suffit.

2. **Y a-t-il au moins 2 options sérieuses qui ont été pesées** (pas
   une option évidente + une caricature) ?
   - **Oui** → ouvre l'ADR, même léger. L'arbitrage mérite sa trace.
   - **Non** → souvent juste un commit.

**En cas de doute** : ouvre l'ADR. Le coût marginal d'un ADR léger est
négligeable vs le coût d'un arbitrage perdu qu'on doit reconstruire
3 mois plus tard.

## 3. Convention de numérotation + slug

- **ID primaire** : `D-NNN` où `NNN` est le prochain numéro libre,
  zéro-paddé sur 3 chiffres. Vérifie avec :
  ```sh
  ls docs/decisions/D-*.md | sort -V | tail -1
  ```
  et **prends NNN+1**. Les gaps sont acceptés (un D-065 manquant est
  OK) — **jamais renuméroter**.

- **Filename** : `D-NNN-<kebab-titre>.md`. Le titre kebab-case fait
  3-6 mots et porte le sujet principal. Évite les acronymes obscurs et
  les codes internes illisibles hors contexte.
  - ✅ `D-067-cadrage-durcissement-pipeline-ingestion.md`
  - ❌ `D-067-ph12b1.md` (illisible hors contexte)
  - ❌ `D-067-pipeline.md` (trop générique)

- **Référence en texte** : `D-049` en clair fonctionne toujours. Forme
  cliquable `[D-049](D-049-<slug>.md)` quand utile dans un autre ADR
  du dossier. **Jamais renuméroter** : les références cross-doc
  accumulées dans tout le repo dépendent du préfixe numérique.

### Travail concurrent (collisions d'IDs)

Quand plusieurs contributeurs ouvrent des ADR en parallèle sur des
branches, deux ADR peuvent naître avec le même `D-NNN` (chacun a
calculé « max + 1 » localement). Les slugs différant, **git ne
signale aucun conflit sur les fichiers eux-mêmes** — c'est l'index qui
joue le rôle de point de sérialisation (décision D-002 du kit) :

- Les deux branches ajoutent leur ligne **en haut** de la table de
  l'index (tri par ID décroissant) → le second merge prend un conflit
  git sur l'index, qui révèle la collision.
- **Résolution** : le contributeur dont l'ADR n'est pas encore mergé
  renumérote (fichier, frontmatter `id:`, ligne d'index) puis merge.
- **Portée de « jamais renuméroter »** : la règle vaut pour les ADR
  **publiés** (mergés sur la branche principale). Renuméroter un ADR
  encore sur sa branche pour résoudre une collision est le geste
  normal, pas une violation.
- **Garde-fou mécanique** : `scripts/adr_check.py` (fourni par le kit,
  avec un workflow GitHub Actions exemple) échoue si deux fichiers
  partagent un préfixe `D-NNN`, si l'index et les fichiers divergent,
  ou si un frontmatter est incohérent. En CI, il rend la collision
  impossible à merger même si le conflit d'index a été mal résolu.

## 4. Les 3 types — quand utiliser lequel

| Type | Template | Cas d'usage |
|---|---|---|
| **cadrage** | `_template_cadrage.md` | Décision structurante avec **2-5 axes** indépendants à acter. Cadrage de chantier, choix d'architecture, gouvernance procédurale. Le type le plus fréquent. |
| **closure** | `_template_closure.md` | Verdict empirique d'une expérimentation, d'un POC, d'un benchmark. Inclut **`verdict`** dans le frontmatter (`ACCEPTED` / `REJECTED` / `ACCEPTED-WITH-CAVEAT` / `INCONCLUSIVE`). Les nuances vont dans le corps, pas dans l'enum. |
| **amendement** | `_template_amendement.md` | Modification ciblée d'un ADR antérieur. Inclut **`amends: D-YYY`** dans le frontmatter et ne réécrit jamais l'ADR amendé (l'historique reste lisible). |

**Règle d'or** : un amendement **ne modifie jamais le corps du fichier
amendé**. Au même commit, le frontmatter de l'ADR amendé reçoit
`amended_by: [D-XXX]` et son `status` passe à `amended` (ou
`superseded` si tout tombe). Le contenu reste verbatim ; c'est le
statut qui change.

## 5. Frontmatter — quick reference

```yaml
---
id: D-NNN                       # invariant, jamais renuméroter
title: "Titre lisible humain"   # révisable sans casser les liens préfixés D-NNN
status: accepted                # draft | accepted | amended | superseded | deprecated
type: cadrage                   # cadrage | closure | amendement
phase: "X.Y"                    # OPTIONNEL — jalon/roadmap si votre projet en a un
date: 2026-06-10                # date d'acte original (jamais révisée)
supersedes: []                  # IDs des ADR remplacés intégralement
amended_by: []                  # rempli quand un amendement arrive (mise à jour atomique)
amends: D-YYY                   # SEULEMENT pour type=amendement
verdict: ACCEPTED               # SEULEMENT pour type=closure
sources:                        # cross-refs internes, machine-readable
  - D-YYY
patterns:                       # handles kebab-case inscrits par cet ADR
  - mon-pattern-en-kebab
---
```

**Conventions** : clés YAML en `snake_case` (consommables par du
tooling), valeurs slug en `kebab-case` (patterns, IDs `D-NNN`). Le
schema de validation est fourni :
[`schemas/adr-frontmatter.schema.json`](../schemas/adr-frontmatter.schema.json)
(`closure` ⇒ `verdict` requis ; `amendement` ⇒ `amends` requis ; et
réciproquement interdits sur les autres types).

Les **patterns** sont des handles courts et mémorisables qui nomment
une règle réutilisable posée par l'ADR (ex.
*« filter-by-origin-when-table-mixes-populations »*). Ils servent de
vocabulaire commun : citables dans les ADR suivants, greppables,
indexables par tooling.

Discipline des patterns (décision D-004 du kit) :

- **Ce sont des handles maison**, forgés localement par l'ADR qui les
  inscrit — pas des références à la littérature. Quand une décision
  correspond à un pattern documenté (keyset pagination, cache-aside,
  circuit breaker…), il se cite dans les **sources externes** de
  l'ADR, sous son nom canonique avec référence — pas dans `patterns:`.
- **Réutiliser avant de forger** : grepper les frontmatters existants
  et reprendre un handle déjà posé plutôt que créer un quasi-synonyme.
- **Critère de frappe** : un ADR futur citera-t-il plausiblement ce
  handle ? Un handle qui ne fait que résumer un axe de l'ADR courant
  est décoratif — ne pas le frapper. Pas de quota : zéro pattern est
  un résultat normal.
- Quotas formels et tooling anti-doublons sont différés (D-004) :
  réexamen à la première collision de handles constatée ou à ~30
  patterns, premier des deux atteint.

## 6. Workflow de création (5 étapes)

1. **Vérifier les prémisses empiriques.** Si ton ADR s'appuie sur un
   état du code, de la base ou d'un fichier (*« on persiste déjà X »*,
   *« le service Y consomme la queue Z »*), fais un `grep` / `SELECT` /
   lecture **avant** d'écrire. Une prémisse fausse réifiée en
   condition de légitimité est un piège classique — et citer un ADR
   antérieur ne vaut pas vérification : recroise avec le code.

2. **Choisir un D-NNN et un slug** :
   ```sh
   ls docs/decisions/D-*.md | sort -V | tail -1   # prochain libre = +1
   ```

3. **Copier le template approprié** (`cadrage` / `closure` /
   `amendement`) et remplir :
   ```sh
   cp docs/decisions/_template_cadrage.md docs/decisions/D-NNN-mon-sujet.md
   ```
   (ou `scripts/adr_new.py` si le repo l'a adopté). Dans l'ordre :
   - Frontmatter (id, title, status, type, date, sources, patterns).
   - Contexte / déclencheur : en ouverture, la **citation
     déclencheuse** (décision D-003 du kit) — la phrase de l'opérateur
     qui a déclenché l'ADR, **verbatim** (extrait pertinent, élision
     `[…]` si long), ou la référence à l'artefact déclencheur
     (incident, mesure, échéance) si non conversationnel. Puis 3-10
     lignes : pourquoi *maintenant*. La citation est l'ancrage
     cognitif : c'est elle qu'on se rappelle et qu'on greppe 6 mois
     plus tard.
   - Décisions actées (axes structurés, options écartées avec raisons).
   - Conditions de légitimité (ce qui doit rester vrai pour que l'ADR
     tienne — chacune falsifiable, testable post-hoc).
   - Sources (ADR amont, références externes éventuelles).
   - **Minutes de décision** : conserve les questions structurantes
     posées à l'opérateur et ses arbitrages. Format : *« Q-N (sujet) :
     … → réponse retenue. Justification : … »*.

4. **Mettre à jour l'index** (`docs/decisions/README.md`) : ajouter
   une ligne dans la table (par ID décroissant). Si l'ADR amende ou
   supersede un autre, mettre à jour le frontmatter de l'ADR
   amendé/superseded au **même commit**.

5. **Commit unique** : un ADR = un commit, index inclus. Message du
   type `docs(decisions): <slug> (D-NNN)`. Pas de batch, pas de bundle
   avec du code. Si l'ADR ouvre des chantiers d'implémentation, ce
   sont des commits ultérieurs.

**Chantiers aval et frontière TODO/ADR** (décision D-005 du kit) : un
ADR ne se « termine » pas — son statut décrit la **validité d'une
décision**, pas l'avancement d'un travail. Les chantiers listés en
Conséquences se matérialisent en TODO in-repo (emplacement recommandé :
`docs/todo/`, registre markdown), chaque item portant la **référence
`D-NNN` de son ADR d'origine** — backlink greppable dans les deux
sens : depuis l'ADR on retrouve le travail restant, depuis le TODO on
retrouve l'arbitrage. Les TODO sans origine décisionnelle restent
libres. Test de frontière : *a-t-on pesé des options ?* → ADR ;
*faut-il « juste le faire » ?* → TODO. Un TODO qu'on re-débat à chaque
passage est une décision non prise — ouvre l'ADR.

## 7. Workflow d'amendement (3 étapes)

Quand un ADR existant cesse d'être valide (en partie ou en tout) :

1. **Identifier ce qui tombe** : un axe ? une condition ? une prémisse
   empirique ? Tout l'ADR ? Si tout tombe, c'est une **supersession**
   (`supersedes: [D-YYY]` sur le nouvel ADR, `status: superseded` sur
   l'ancien), pas un amendement.

2. **Ouvrir un ADR d'amendement** (type=amendement, `amends: D-YYY`).
   Il contient :
   - Le déclencheur (incident, mesure empirique, retour terrain,
     contradiction observée).
   - La modification actée, au format *« avant : … ; après : … »*.
   - Les sections de D-YYY impactées vs préservées.

3. **Mettre à jour D-YYY au même commit** :
   - `amended_by: [D-XXX]` ajouté à son frontmatter (jamais réécrire
     le corps).
   - `status:` passe à `amended`.
   - Optionnellement, une note inline en tête de la section concernée :
     *« Amendement D-XXX (date) : voir D-XXX. »*

## 8. Cross-références

- **Préfixe numérique invariant** : `D-049` reste `D-049` à
  perpétuité. Une réorganisation du dossier ne casse jamais une
  référence textuelle.
- **Liens cliquables** : `[D-049](D-049-<slug>.md)` entre ADR du même
  dossier. Si tu ne connais pas le slug exact, le texte plein `D-NNN`
  suffit — ne devine pas un lien.
- **Title révisable, slug stable** : le `title:` du frontmatter peut
  être reformulé ; le filename ne change pas sans `git mv` documenté
  dans un ADR d'amendement.

## 9. Travailler avec une IA

### Pourquoi pas de commande / skill dédiée ?

Ouvrir un ADR est un processus **multi-étapes interactif** (lire le
contexte, proposer des axes, poser des questions structurantes,
drafter, valider). Une commande qui wrappe ce workflow serait soit
trop rigide, soit exploserait en arbre de branches. Le bon découpage :
la méthodologie vit dans ce guide (lu par l'IA et par les collègues),
et le scaffolding mécanique (nouveau fichier + ID + date) tient dans
un petit script optionnel. Avantage : tout contributeur, quel que soit
son outillage (Claude Code, Cursor, vim, GitHub web), accède aux mêmes
outils.

### Comment l'IA découvre la convention

Le fichier d'instructions du repo (`CLAUDE.md`, `.cursorrules`,
équivalent) pointe vers ce guide et vers l'index — voir le snippet
fourni par le kit (`snippets/CLAUDE.md`). L'IA lit ensuite
naturellement l'index et le guide quand la conversation touche aux
décisions structurantes.

### Prompts types

**Drafter un nouvel ADR** :

> « Propose un cadrage pour \<sujet\>. Lis D-YYY comme exemple de
> format. Utilise le template cadrage. Vérifie les prémisses
> empiriques avant de figer les conditions de légitimité. »

Une bonne IA posera 3-5 questions structurantes avant de rédiger.
C'est attendu — les minutes de décision sont **load-bearing**.

**Amender un ADR existant** :

> « D-049 a une condition #2 qui ne tient plus parce que \<constat\>.
> Lis D-049, identifie l'axe ou la condition impactée, propose un
> amendement. »

L'IA lit D-049 entier, propose l'amendement au format *« avant /
après »*, et met à jour `amended_by` dans D-049 au même commit.

**Auditer un brouillon avant publication** :

> « Lis le brouillon D-XXX. Vérifie : frontmatter complet et cohérent ;
> conditions de légitimité falsifiables (chacune testable post-hoc) ;
> prémisses empiriques vérifiées (cite les lignes de code ou les
> queries) ; chaque D-YYY cité existe ; patterns kebab-case présents
> dans le frontmatter et inscrits inline. »

**Vérifier les références** :

> « Vérifie que les références D-049, D-053, D-067 dans \<doc\>
> pointent toutes vers un fichier existant de docs/decisions/. »

### Anti-patterns IA

- ❌ **Ne demande pas à l'IA d'inventer les minutes de décision.**
  Les minutes représentent **tes** arbitrages, pas ceux de l'IA. Si tu
  veux l'IA comme contradicteur pour préparer un cadrage, fais une
  session de débat avant la rédaction, puis fournis-lui tes réponses
  pour qu'elle les retranscrive.
- ❌ **Ne laisse pas l'IA batcher plusieurs ADR dans un commit.**
  Un ADR = un commit reste la règle (exception : migrations massives
  explicitement cadrées).
- ❌ **Ne laisse pas l'IA citer un ADR antérieur comme preuve d'un
  état du code.** L'état du code se vérifie dans le code.
- ❌ **Ne laisse pas l'IA fabriquer une citation déclencheuse.** Si
  l'ADR ne naît pas d'une phrase de l'opérateur, son déclencheur cite
  l'artefact (incident, mesure, échéance) — une pseudo-citation est de
  même gravité que des minutes inventées.

## 10. Anti-patterns généraux

- **Renuméroter** : jamais pour un ADR publié (mergé), sous aucun
  prétexte. Les gaps sont OK. Seule exception : renuméroter un ADR
  encore sur sa branche pour résoudre une collision d'IDs — voir §3
  « Travail concurrent ».
- **Modifier un ADR publié** : sauf mise à jour de `amended_by` /
  `status` dans le frontmatter lors d'un amendement. Le corps reste
  verbatim.
- **Citer un ADR antérieur sans recroiser le code** : cause classique
  de chaîne d'erreurs — une prémisse fausse se propage d'ADR en ADR
  jusqu'à ce qu'un incident la révèle. Pattern :
  *« pre-commit-adr-must-verify-its-premises-against-code-not-just-prior-adr »*.
- **Ouvrir un ADR pour une décision triviale** : si tu hésites
  longtemps à savoir si ça mérite un ADR, c'est probablement non.
  Cherche des décisions structurantes, pas des notes de design.
- **Critères relaxables post-hoc** : si tu rédiges un critère strict
  (clôture AND, gate chiffré), sois prêt à le tenir. Un critère qu'on
  assouplit après coup vaut moins que pas de critère.
- **Spécifier au-delà de l'horizon d'évidence** : ne cadre pas en
  détail un chantier dépendant d'un verdict pas encore observé.
  Pattern *« no-spec-ahead-beyond-evidence-horizon »*.

## 11. Index et maintenance

- **Index `README.md`** : une ligne par ADR (ID décroissant), mis à
  jour au même commit que chaque nouvel ADR. Squelette fourni :
  `templates/README_index.md`.
- **Statuts à jour** : quand un ADR amende ou supersede, le statut de
  la cible change au même commit. Pas de drift toléré.
- **Hygiène trimestrielle suggérée** (étendue par D-005) : parcourir
  l'index, vérifier que les statuts reflètent la réalité (ADR
  superseded silencieusement ? drafts jamais finalisés ?) ; grepper
  les backlinks `D-NNN` encore ouverts dans `docs/todo/` (chantier
  enlisé ou ADR jamais implémenté ?) ; vérifier les seuils des
  décisions différées actées (un différé dont le déclencheur est
  atteint se rouvre, il ne s'enterre pas).
- **Tooling différé** : l'index hand-maintained est acceptable
  jusqu'à ~80-100 ADR. Au-delà, un script qui régénère l'index (et un
  `PATTERNS.md` handle → liste d'ADR) depuis les frontmatters devient
  rentable — le frontmatter a été conçu pour ça. Pas de `CHANGELOG.md`
  hand-maintained : c'est le pire pattern pour les conflits merge, et
  le frontmatter porte déjà `date` et `status`.
- **Scaffolder** : `scripts/adr_new.py` (fourni, optionnel) trouve le
  prochain ID, copie le template, pré-remplit le frontmatter. La
  routine manuelle `cp _template_*.md` reste valable et porte la
  discipline du choix conscient du type.
- **Vérificateur** : `scripts/adr_check.py` (fourni, optionnel —
  décisions D-002 et D-005 du kit) contrôle l'unicité des IDs, la
  synchronisation index ↔ fichiers, la cohérence du frontmatter, et
  les références `D-NNN` des TODO (`docs/todo/` et `TODO.md`
  auto-détectés, `--refs` pour le reste). À brancher en CI (workflow
  GitHub Actions exemple fourni) ou en pre-commit ; voir §3 « Travail
  concurrent ».

## 12. Récap rapide

| Tu veux… | Action |
|---|---|
| Ouvrir un cadrage structurant | Template `_template_cadrage.md` + `type: cadrage` |
| Acter un verdict empirique | Template `_template_closure.md` + `type: closure` + `verdict:` |
| Amender un ADR | Template `_template_amendement.md` + `type: amendement` + `amends: D-YYY` + mise à jour atomique de D-YYY |
| Remplacer intégralement un ADR | Nouvel ADR avec `supersedes: [D-YYY]` + `status: superseded` sur D-YYY |
| Référencer un ADR | `D-NNN` en texte plein (toujours valide) ou `[D-NNN](D-NNN-<slug>.md)` |
| Trouver le prochain ID | `ls docs/decisions/D-*.md \| sort -V \| tail -1` puis +1 |
| Faire drafter par une IA | Fournir le template cible + 1-2 ADR exemples + tes arbitrages |
