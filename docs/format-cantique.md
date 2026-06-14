# Format source d'un cantique

Spécification du format **structuré** des paroles, acté par
[D-001](decisions/D-001-format-source-structure-paroles.md). Un cantique
= un fichier **YAML** sous `stock/cantiques/`. Schéma de validation
machine : [`schemas/cantique.schema.json`](../schemas/cantique.schema.json).

Ce format remplace les `.txt` en texte libre : couplets et refrain
deviennent des champs distincts, pour que le code (et non l'opérateur)
gère l'expansion du refrain et la sélection de couplets.

## Champs

| Champ | Requis | Type | Rôle |
|---|---|---|---|
| `numero` | ✅ | string | Identifiant. Cantique `"NN-NN"` (`"12-07"`), psaume `"Ps 0NN"` (`"Ps 008"`), suffixe lettre accepté (`"Ps 034A"`). **String** pour préserver zéros de tête et lettres. |
| `titre` | ✅ | string | Titre, sans le préfixe numéro. |
| `couplets` | ✅ | liste de string | Couplets dans l'ordre de chant. **Liste 1-based**. ≥ 1 élément. |
| `source` | — | string | Sous-titre / provenance (`"Psaume 34"`). Absent = aucune. |
| `refrain` | — | string | Texte du refrain, **stocké une seule fois**. Absent = pas de refrain. |
| `credits` | — | string | Auteur / éditeur / copyright. Absent = aucun. |

L'absence d'une clé optionnelle vaut « aucun » — pas de valeur vide.

## Règles

- **Multi-ligne** : chaque couplet et le refrain sont des blocs
  littéraux YAML `|` (les retours à la ligne sont préservés tels quels).
- **Refrain stocké une fois** : la source ne duplique jamais le refrain
  entre les couplets. L'insertion `couplet → refrain → couplet` à la
  projection appartient à la couche de présentation (templates `tpl/` +
  assemblage `Scene`), pas au fichier source.
- **Sélecteur de couplets** : dans `chants.txt` / fichier de spontanés,
  un cantique peut porter en **fin de ligne** un sélecteur `(...)` —
  c'est la notation déjà en usage dans `chants.txt`. Un chiffre vise
  `couplets[N-1]` ; `R` vise `refrain`. Deux modes, selon la présence
  d'un `R` :
  - **chiffres seuls** (`(1,3)`) → couplets choisis dans l'ordre, le
    **refrain est réinséré après chaque** (comme le cantique se chante) ;
  - **avec `R`** (`(1,R,3)`, `(R,1,R,2)`) → séquence **littérale**,
    reproduite telle quelle (contrôle manuel exact, refrain en intro
    ponctuel…).
  ```
  22-04 « Oh ! Parle-moi Seigneur » (1,2,3)   # couplets 1-2-3, refrain entre chaque
  35-19 « … » (2,1)                           # réordonnés, refrain entre chaque
  21-17 « … » (1,R,3)                         # littéral : couplet 1, refrain, couplet 3
  12-13 « … »                                 # sans sélecteur → tout le cantique
  ```
  Un couplet hors limites ou un `R` sans refrain est **ignoré avec un
  avertissement** ; un sélecteur sur un cantique non structuré (`.txt`)
  est ignoré (avertissement). Le défaut « refrain en intro **par
  cantique** » (sans `R` explicite) reste un chantier à venir, cf.
  [`docs/todo/README.md`](todo/README.md).
- **Non découpable** : un cantique sans numérotation exploitable est
  stocké en **un couplet unique** (cf. `13-03.yaml`) et signalé par le
  rapport du convertisseur ; la relecture humaine tranche le découpage.

## Exemples de référence

Fixtures converties à la main, couvrant les trois cas types :

- [`stock/cantiques/12-13.yaml`](../stock/cantiques/12-13.yaml) —
  refrain + 4 couplets + source + crédits.
- [`stock/cantiques/Ps 008.yaml`](../stock/cantiques/Ps%20008.yaml) —
  psaume : ni refrain ni source, 6 couplets.
- [`stock/cantiques/13-03.yaml`](../stock/cantiques/13-03.yaml) — texte
  continu non découpé, un couplet unique.

## Validation

Le format est validable contre `schemas/cantique.schema.json` (JSON
Schema draft-07). Un cantique valide a `numero`, `titre` et au moins un
`couplets`, et n'a pas de clé inconnue (`additionalProperties: false`
attrape les fautes de frappe). Un validateur outillé (parcours de
`stock/cantiques/**`) est un chantier aval du convertisseur — voir
[`docs/todo/README.md`](todo/README.md) (`D-001`).
