import json

class Src_cantique_title :
    def __init__(self,name) :
        with open('cantique_title.json',"r",encoding="utf-8") as template:
            self.core = json.load(template)
        #load cantique from external file
        head=''
        with open(name+'.txt',"r",encoding="utf-8") as cantique :
            head = ''.join([next(cantique) for x in range(2)])
            self.core["settings"]["text"]=head
        self.core["name"]=name+" : titre"

    def to_json(self):
        return self.core

class Src_cantique_paroles :
    def __init__(self,name) :
        with open('cantique_paroles.json',"r",encoding="utf-8") as template:
            self.core = json.load(template)
        #load cantique from external file
        with open(name+'.txt',"r",encoding="utf-8") as cantique :
            ''.join([next(cantique) for x in range(2)])
            data = '\n\n\n\n'+cantique.read()
            self.core["settings"]["text"]=data
        self.core["name"]=name+" : paroles"

    def to_json(self):
        return self.core        

class Itm_cantique_title :
    def __init__(self,name) :
        with open('cantique_title_item.json',"r",encoding="utf-8") as template:
            self.core = json.load(template)
        #load cantique from external file
        self.core["name"]=name+" : titre"

    def to_json(self):
        return self.core

class Itm_cantique_paroles :
    def __init__(self,name) :
        with open('cantique_paroles_item.json',"r",encoding="utf-8") as template:
            self.core = json.load(template)
        #load cantique from external file
        self.core["name"]=name+" : paroles"

    def to_json(self):
        return self.core

class Scene :
    def __init__(self,name) :
        with open('basic_scene.json',"r",encoding="utf-8") as template:
            self.core = json.load(template)
        self.core["name"]=name
    def to_json(self):
        return self.core
    def add_item(self,item) :
        self.core["settings"]["items"].append(item)


class Scene_Collection :
    def __init__(self,name) :
        with open('Template.json',"r",encoding="utf-8") as template:
            self.core = json.load(template)
        self.core["name"]=name
    def to_json(self):
        return self.core
    def add_source(self,source) :
        self.core["sources"].append(source)