# Gestion des encodages et préservation des caractères accentués

## Problématique

Lors de la conversion des fichiers .doc en fichiers texte, les caractères accentués (é, è, ê, à, ç, etc.) pouvaient "sauter" ou être mal encodés dans le fichier texte final. Ce problème était particulièrement visible en mode traitement massif (sans argument spécifique), alors que le mode fichier unique (avec l'option `--file`) fonctionnait mieux dans certains cas.

## Analyse du problème

Le problème de perte des accents était dû à plusieurs facteurs :

1. **Différences entre les méthodes d'extraction** : La méthode utilisant le presse-papiers (`extract_text_with_com_clipboard`) préservait mieux les accents que les autres méthodes, mais n'était pas toujours utilisée systématiquement.

2. **Encodage non optimal** : Les encodages utilisés pour lire et écrire les fichiers n'étaient pas optimisés pour les caractères français.

3. **Absence de normalisation Unicode** : Le texte extrait n'était pas normalisé de manière uniforme avant d'être écrit dans le fichier de sortie.

4. **Problèmes de ressources** : En mode traitement massif, les ressources (Word, presse-papiers) n'étaient pas correctement libérées entre chaque fichier.

## Solutions implémentées

### 1. Système intelligent de détection d'encodage

Le script utilise désormais un système de score pour déterminer le meilleur encodage à utiliser lors de l'extraction du texte :

```python
# Liste plus complète d'encodages courants pour le français, dans l'ordre de priorité
encodings = ['cp1252', 'latin1', 'iso-8859-1', 'iso-8859-15', 'utf-8']

# Variables pour garder trace du meilleur encodage trouvé
best_text = ""
best_encoding = None
best_score = 0

# Essayer plusieurs encodages pour trouver celui qui préserve le mieux les accents
for encoding in encodings:
    try:
        decoded_text = clipboard_data.decode(encoding)
        
        # Compter les caractères accentués français courants pour évaluer la qualité
        accent_chars = 'éèêëàâäôöùûüçÉÈÊËÀÂÄÔÖÙÛÜÇîïÎÏ'
        score = sum(decoded_text.count(c) for c in accent_chars)
        
        # Si on trouve des accents et que le score est meilleur que le précédent
        if score > best_score:
            best_score = score
            best_encoding = encoding
            text = decoded_text
    except:
        continue
```

### 2. Priorisation des encodages Windows

L'ordre des encodages testés a été optimisé pour privilégier ceux généralement utilisés par les documents Word sous Windows :

1. **cp1252** : encodage Windows par défaut pour l'Europe occidentale, incluant les caractères français
2. **latin1** (ISO-8859-1) : encodage standard pour l'Europe occidentale
3. **iso-8859-1** : variante normalisée de latin1
4. **iso-8859-15** : version améliorée de latin1 incluant l'euro et quelques caractères français supplémentaires
5. **utf-8** : encodage Unicode universel (généralement utilisé en dernier recours car il peut mal interpréter certains textes non-Unicode)

### 3. Normalisation Unicode avant l'écriture

Avant d'écrire le texte extrait dans le fichier final, une étape de normalisation est appliquée pour garantir une représentation cohérente des caractères accentués :

```python
# S'assurer que le texte est bien encodé en UTF-8 pour l'écriture
if text:
    # Normaliser les caractères composés (combinaisons d'accents)
    import unicodedata
    text = unicodedata.normalize('NFC', text)
```

Cette normalisation utilise la forme "NFC" (Normalization Form C) qui privilégie la représentation précomposée des caractères accentués. Par exemple, le caractère "é" peut être représenté soit comme un seul caractère précomposé (U+00E9), soit comme la combinaison de "e" (U+0065) et d'un accent aigu (U+0301). La forme NFC garantit l'utilisation de la forme précomposée, ce qui améliore la compatibilité avec différents systèmes.

## Améliorations pour les différentes méthodes d'extraction

### 1. Priorisation de la méthode du presse-papiers

La méthode du presse-papiers (CTRL+A/CTRL+C) a été identifiée comme celle qui préserve le mieux les caractères accentués. Le script a été modifié pour toujours essayer cette méthode en premier, et n'utiliser les autres qu'en cas d'échec :

```python
def extract_text_from_doc(doc_path):
    # Essayer d'abord avec la méthode du presse-papiers (CTRL+A, CTRL+C)
    text = extract_text_with_com_clipboard(doc_path)
    if text and text.strip():
        print("Méthode d'extraction utilisée avec succès: Word COM Clipboard (CTRL+A/CTRL+C)")
        text = normalize_text(text)
        return text
    else:
        print(f"La méthode du presse-papiers a échoué pour {doc_path}, essai avec les méthodes alternatives")
    
    # Fallback avec les autres méthodes...
```

### 2. Amélioration des méthodes d'extraction

#### Méthode du presse-papiers (principale)

La fonction `extract_text_with_com_clipboard` a été considérablement améliorée :

- Gestion plus robuste des erreurs à chaque étape
- Délais adaptés entre les opérations critiques
- Meilleure détection des formats disponibles dans le presse-papiers
- Système de score pour déterminer le meilleur encodage

#### Méthode SaveAs (fallback)

La fonction `extract_text_with_com_save_as` a été optimisée pour préserver les caractères accentués même lorsque la méthode du presse-papiers échoue :

- Utilisation du format texte Unicode (FileFormat=7) au lieu du format texte MS-DOS (FileFormat=2)
- Système de détection d'encodage multicouche :
  ```python
  # Liste des encodages à essayer, en ordre de priorité
  encodings = ['utf-16', 'utf-8', 'cp1252', 'latin1', 'iso-8859-1', 'iso-8859-15']
  
  # Variables pour garder trace du meilleur encodage trouvé
  best_text = ""
  best_encoding = None
  best_score = 0
  
  for encoding in encodings:
      try:
          with open(temp_path, 'r', encoding=encoding, errors='replace') as f:
              text = f.read()
              
              # Compter les caractères accentués français courants pour évaluer la qualité
              accent_chars = 'éèêëàâäôöùûüçÉÈÊËÀÂÄÔÖÙÛÜÇîïÎÏœŒ'
              score = sum(text.count(c) for c in accent_chars)
              
              # Si on trouve des accents et que le score est meilleur que le précédent
              if score > best_score:
                  best_score = score
                  best_encoding = encoding
                  best_text = text
      except Exception as e:
          print(f"Erreur avec l'encodage {encoding}: {e}")
          continue
  ```
- Support explicite de l'encodage UTF-16 utilisé par Windows pour l'Unicode
- Journalisation détaillée pour faciliter le diagnostic des problèmes d'encodage

### 3. Gestion des ressources entre les fichiers

Pour éviter les problèmes lors du traitement massif, plusieurs mesures ont été implémentées :

```python
# Ajouter un délai entre chaque fichier pour éviter les problèmes de ressources
print("Pause pour libérer les ressources...")
time.sleep(3)

# Forcer le garbage collector pour libérer la mémoire
import gc
gc.collect()

# Réinitialiser explicitement le presse-papiers entre chaque fichier
try:
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.CloseClipboard()
    print("Presse-papiers vidé avec succès")
except Exception as e:
    print(f"Erreur lors du vidage du presse-papiers: {e}")
```

### 4. Vérifications explicites de la préservation des accents

Des vérifications ont été ajoutées pour confirmer la préservation des caractères accentués à chaque étape :

```python
# Vérifier la présence de caractères accentués après normalisation
accent_chars = 'éèêëàâäôöùûüçÉÈÊËÀÂÄÔÖÙÛÜÇîïÎÏ'
accent_count = sum(normalized.count(c) for c in accent_chars)

if accent_count > 0:
    print(f"Texte normalisé avec succès, {accent_count} caractères accentués préservés")
else:
    print("Attention: Aucun caractère accentué détecté après normalisation")
```

Et également lors de l'écriture du fichier :

```python
# Vérifier que les caractères accentués ont bien été écrits
with open(output_path, 'r', encoding='utf-8') as f:
    written_text = f.read()
    accent_chars = 'éèêëàâäôöùûüçÉÈÊËÀÂÄÔÖÙÛÜÇîïÎÏ'
    accent_count = sum(written_text.count(c) for c in accent_chars)
    if accent_count > 0:
        print(f"Fichier écrit avec succès, {accent_count} caractères accentués préservés")
    else:
        print("Attention: Aucun caractère accentué détecté dans le fichier écrit")
```

## Résultats concrets

Les tests effectués avec ces améliorations montrent une préservation effective des caractères accentués dans les fichiers générés :

- **Fichier 12-01.doc** : 28 caractères accentués préservés
- **Fichier 12-02.doc** : 8 caractères accentués préservés
- **Fichier 12-03.doc** : 13 caractères accentués préservés
- **Fichier 12-04.doc** : 9 caractères accentués préservés
- **Fichier 12-05.doc** : 18 caractères accentués préservés
- **Fichier 12-06.doc** : 10 caractères accentués préservés

La méthode du presse-papiers est maintenant utilisée systématiquement quand elle fonctionne, et les caractères accentués sont correctement préservés tant en mode fichier unique qu'en mode traitement massif.

## Notes techniques sur les encodages

### cp1252 (Windows-1252)

L'encodage cp1252 est une extension de l'ISO-8859-1 créée par Microsoft et utilisée par défaut dans Windows pour les langues d'Europe occidentale. Il inclut tous les caractères accentués français courants et est souvent l'encodage natif des documents Word créés sous Windows.

### ISO-8859-1 (Latin-1)

L'encodage ISO-8859-1, aussi appelé Latin-1, est un standard international pour les langues d'Europe occidentale. Il inclut la plupart des caractères accentués français, mais certains caractères comme l'euro (€) ou l'œ ligaturé ne sont pas inclus.

### ISO-8859-15

Une version améliorée de l'ISO-8859-1 qui ajoute le caractère euro (€), l'œ ligaturé et quelques autres caractères utiles pour le français.

### UTF-8

L'encodage Unicode UTF-8 est capable de représenter tous les caractères possibles, y compris tous les caractères accentués français. Cependant, lors de la lecture de fichiers binaires ou de contenus du presse-papiers qui ne sont pas en UTF-8, tenter de décoder en UTF-8 peut produire des résultats incorrects. C'est pourquoi il est utilisé en dernier recours dans notre système de détection.
