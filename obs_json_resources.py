import os
import json

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


# a reprendre sur une classe plus précise
class Scene(Obs_basic) :
    def __init__(self, file,sc):
        self.file = os.path.abspath(file)
        with open(file,"r",encoding="utf-8") as cantique :
            self.head = ''.join([next(cantique) for x in range(2)])
            self.lyrics = '\n\n\n\n'+cantique.read()    
        base=os.path.basename(file)
        self.name = os.path.splitext(base)[0]
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


class Scene_Collection(Obs_basic) :
    def __init__(self,name):
        super().__init__(name)
        self.scenes=[]
    def add_source(self,source) :
        self.core["sources"].append(source)
    def add_scene(self,file) :
        self.scenes.append(Scene(file,self))
    def generate_scenes_from_dir(self, dir) :
        filelist = os.listdir(os.path.abspath(dir)) # returns list
        for file in filelist:
            self.add_scene(os.path.abspath(dir+"/"+file))
            #  prepare_cantique(scene,os.path.abspath(dir+"/"+file))