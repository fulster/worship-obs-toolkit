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
    def add_scene(self,file) :
        self.scenes.append(Scene(file,self))
    def generate_scenes_from_dir(self, dir) :
        filelist = os.listdir(os.path.abspath(dir)) # returns list
        for file in filelist:
            self.add_scene(os.path.abspath(dir+"/"+file))
            #  prepare_cantique(scene,os.path.abspath(dir+"/"+file))