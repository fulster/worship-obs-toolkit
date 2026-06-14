import glob
import os
import json
import re
import copy

import yaml


def load_cantique_yaml(file):
    """Charge un cantique au format structuré (D-001) depuis un fichier YAML."""
    with open(file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_selection(text):
    """Parse le contenu d'un sélecteur `(...)` en liste de jetons.

    Jetons acceptés : un entier (couplet, 1-based) ou ``R`` (refrain). Sépara-
    teur virgule, espaces tolérés. Retourne ``None`` si vide ou si un jeton est
    non reconnu (le sélecteur est alors ignoré côté appelant).
    """
    tokens = []
    for part in text.split(","):
        p = part.strip()
        if not p:
            continue
        if p.upper() == "R":
            tokens.append("R")
        elif p.isdigit():
            tokens.append(int(p))
        else:
            return None
    return tokens or None


def _resolve_sequence(data, selection):
    """Calcule la séquence finale de jetons à projeter.

    - ``selection is None`` (pas de sélecteur) → tous les couplets dans l'ordre,
      refrain inséré après chaque (défaut historique).
    - sélecteur **sans** ``R`` (ex. ``(1,3)``) → couplets choisis dans l'ordre,
      refrain inséré après chaque (mode A : le refrain revient tout seul).
    - sélecteur **avec** ``R`` (ex. ``(1,R,3)`` ou ``(R,1,R,2)``) → séquence
      littérale, reproduite telle quelle (contrôle manuel exact).
    """
    couplets = data.get("couplets") or []
    has_refrain = bool((data.get("refrain") or "").strip())

    if selection is not None and any(t == "R" for t in selection):
        return list(selection)

    if selection is None:
        nums = list(range(1, len(couplets) + 1))
    else:
        nums = [t for t in selection if t != "R"]

    seq = []
    for num in nums:
        seq.append(num)
        if has_refrain:
            seq.append("R")
    return seq


def expand_cantique(data, selection=None):
    """Construit (head, paroles, avertissements) pour la projection.

    - head = ``numero\\ntitre`` (le template de titre affiche n° puis titre) ;
    - paroles = un bloc unique destiné au texte défilant : `source` en tête,
      les couplets/refrains selon la séquence résolue (cf. `_resolve_sequence`),
      `credits` en pied. Le refrain n'est stocké qu'une fois dans la source —
      c'est ici, couche de présentation, qu'il est expansé (cf. D-001).

    `selection` est une liste de jetons (entiers / ``"R"``) issue d'un sélecteur
    `(...)`, ou ``None`` pour le cantique entier. Les sections sont séparées par
    une ligne vide, comme dans les `.txt` nettoyés à la main.
    """
    numero = (data.get("numero") or "").strip()
    titre = (data.get("titre") or "").strip()

    couplets = data.get("couplets") or []
    refrain = (data.get("refrain") or "").strip() or None

    # Head = « numéro titre » (1re ligne) + indication des couplets joués
    # (2e ligne) : couplets sélectionnés tels qu'écrits, sinon tous.
    titre_line = f"{numero} {titre}".strip() if numero else titre
    if selection is None:
        indication = ",".join(str(i) for i in range(1, len(couplets) + 1))
    else:
        indication = ",".join(str(t) for t in selection)
    head = f"{titre_line}\n{indication}" if indication else titre_line

    warnings = []
    blocks = []
    for tok in _resolve_sequence(data, selection):
        if tok == "R":
            if refrain:
                blocks.append(refrain)
            else:
                warnings.append("refrain demandé mais le cantique n'en a pas")
        elif 1 <= tok <= len(couplets):
            blocks.append(couplets[tok - 1].rstrip())
        else:
            warnings.append(f"couplet {tok} hors limites (1..{len(couplets)})")

    sections = []
    source = (data.get("source") or "").strip()
    if source:
        sections.append(source)
    sections.extend(blocks)
    credits = (data.get("credits") or "").strip()
    if credits:
        sections.append(credits)

    return head, "\n\n".join(sections), warnings

class Obs_basic :
    def __init__(self,name) :
        class_name = self.__class__.__name__
        dir = os.path.dirname(__file__)
        tpl = os.path.abspath(dir+'/tpl/'+class_name+'.json')
        with open(tpl,"r",encoding="utf-8") as template:
            self.core = json.load(template)
        self.core["name"]=name
    def to_json(self):
        return self.core

class Cantique_lyrics_item(Obs_basic) :
    def __init__(self,name) :
        self.name=name+" : lyrics"
        super().__init__(self.name)

class Cantique_lyrics_source(Obs_basic) :
    def __init__(self,name,content) :
        self.name=name+" : lyrics"
        super().__init__(self.name)
        self.core["settings"]["text"]=content


class Cantique_title_item(Obs_basic) :
    def __init__(self,name) :
        self.name=name+" : titre"
        super().__init__(self.name)

class Cantique_title_source(Obs_basic) :
    def __init__(self,name,content) :
        self.name=name+" : titre"
        super().__init__(self.name)
        self.core["settings"]["text"]=content

class Source_image(Obs_basic) :
    def __init__(self,name,file) :
        self.name=name
        self.file = os.path.abspath(file)
        super().__init__(self.name)
        self.core["settings"]["file"]=self.file

class Source_text(Obs_basic) :
    def __init__(self,name,content) :
        self.name=name
        super().__init__(self.name)
        self.core["settings"]["text"]=content

class Item_image(Obs_basic) :
    def __init__(self,name) :
        self.name=name
        super().__init__(self.name)

class Item_text(Obs_basic) :
    def __init__(self,name) :
        self.name=name
        super().__init__(self.name)



# a reprendre sur une classe plus précise
class Scene(Obs_basic) :
    def __init__(self, file,sc,selection=None):
        self.file = os.path.abspath(file)
        if os.path.splitext(file)[1].lower() in (".yaml", ".yml"):
            # Format structuré (D-001) : le refrain est expansé après chaque
            # couplet à la lecture, le code remplace le nettoyage manuel. Un
            # sélecteur (...) choisit/réordonne les couplets (cf. expand_cantique).
            data = load_cantique_yaml(file)
            self.head, body, warnings = expand_cantique(data, selection)
            for w in warnings:
                print(f"  Attention : {os.path.basename(file)} : {w}")
            self.lyrics = '\n\n\n\n'+body
            # Nom de scène = « numéro titre » (visible dans la liste OBS).
            numero = (data.get("numero") or "").strip()
            titre = (data.get("titre") or "").strip()
            self.name = f"{numero} {titre}".strip() or os.path.splitext(os.path.basename(file))[0]
        else:
            # Format texte libre historique (stock/txt) : titre = 1re ligne non
            # vide, paroles = le reste du fichier tel quel.
            if selection is not None:
                print(f"  Attention : sélecteur ignoré, cantique non structuré : {os.path.basename(file)}")
            with open(file,"r",encoding="utf-8") as cantique :
                self.head = ""
                for line in cantique:
                    if line.strip():
                        self.head = line
                        break
                self.lyrics = '\n\n\n\n'+cantique.read()
            self.name = os.path.splitext(os.path.basename(file))[0]
        super().__init__(self.name)

        #title
        cantique_title_source=Cantique_title_source(self.name,self.head)
        cantique_title_item=Cantique_title_item(self.name)
        sc.add_source(cantique_title_source.to_json())
        self.add_item(cantique_title_item.to_json())

        #lyrics
        cantique_lyrics_source=Cantique_lyrics_source(self.name,self.lyrics)
        cantique_lyrics_item=Cantique_lyrics_item(self.name)
        sc.add_source(cantique_lyrics_source.to_json())
        self.add_item(cantique_lyrics_item.to_json())

        #the scene itself
        sc.add_source(self.to_json())

    def add_item(self,item) :
        self.core["settings"]["items"].append(item)

class Tmp_scene(Obs_basic) :
    def __init__(self, name,sc):
        self.name = name
        self.sc = sc
        super().__init__(self.name)

    def add_image(self,name,file) :
        image_source = Source_image(name,file)
        image_item = Item_image(name)
        self.sc.add_source(image_source.to_json())
        self.add_item(image_item.to_json())

    def add_text(self,name,content) :
        text_source = Source_text(name,content)
        text_item = Item_text(name)
        self.sc.add_source(text_source.to_json())
        self.add_item(text_item.to_json())
        
        #the scene itself
    def register(self) :
        self.sc.add_source(self.to_json())

    def add_item(self,item) :
        self.core["settings"]["items"].append(item)


class Scene_Collection(Obs_basic) :
    def __init__(self,name):
        super().__init__(name)
        self.scenes=[]
    def add_source(self,source) :
        self.core["sources"].append(source)
    def add_scene(self,file,selection=None) :
        self.scenes.append(Scene(file,self,selection))
    def duplicate_base(self, new_name, base_name="Base : temple"):
        """Duplique une scène existante (la « base ») sous un nouveau nom.

        Permet d'intercaler des copies de la vue de base entre les cantiques.
        Les copies partagent la même source (caméra) ; seul le nom de scène
        change (OBS impose des noms de scène uniques).
        """
        for src in self.core["sources"]:
            if src.get("id") == "scene" and src.get("name") == base_name:
                clone = copy.deepcopy(src)
                clone["name"] = new_name
                self.core["sources"].append(clone)
                return new_name
        return None
    def rename_scene(self, old, new):
        """Renomme une scène (source id « scene ») et met à jour les références.

        Les items d'une scène référencent leurs sources (titre/paroles/caméra)
        par leur propre nom, inchangé — renommer la scène ne les casse pas.
        """
        for s in self.core["sources"]:
            if s.get("id") == "scene" and s.get("name") == old:
                s["name"] = new
                break
        for key in ("current_scene", "current_program_scene"):
            if self.core.get(key) == old:
                self.core[key] = new
    def set_display_order(self, names):
        """Fixe l'ordre d'affichage des scènes dans OBS.

        Renseigne `scene_order` (mécanisme officiel) ET réordonne les scènes
        dans `sources` pour que les deux concordent. Les sources non-scène
        (caméra, textes) restent en tête ; les scènes non listées (sécurité)
        sont ajoutées à la fin.
        """
        self.core["scene_order"] = [{"name": n} for n in names]
        non_scenes = [s for s in self.core["sources"] if s.get("id") != "scene"]
        scenes = {s["name"]: s for s in self.core["sources"] if s.get("id") == "scene"}
        ordered = [scenes[n] for n in names if n in scenes]
        listed = set(names)
        ordered += [s for nm, s in scenes.items() if nm not in listed]
        self.core["sources"] = non_scenes + ordered
    def generate_scenes_from_dir(self, dir) :
        filelist = os.listdir(os.path.abspath(dir)) # returns list
        filelist.sort(reverse=True)
        for file in filelist:
            self.add_scene(os.path.abspath(dir+"/"+file))
            #  prepare_cantique(scene,os.path.abspath(dir+"/"+file))
