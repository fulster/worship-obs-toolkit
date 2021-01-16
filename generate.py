from obs_json_resources import Scene_Collection
from obs_json_resources import Scene
from obs_json_resources import Src_cantique_title
from obs_json_resources import Itm_cantique_title
from obs_json_resources import Src_cantique_paroles
from obs_json_resources import Itm_cantique_paroles

import json

def prepare_cantique(collec, name) :
    MyScene=Scene(name)
    MyCantique_title = Src_cantique_title(name)
    MyItemCantique_title = Itm_cantique_title(name)
    MyCantique_paroles = Src_cantique_paroles(name)
    MyItemCantique_paroles = Itm_cantique_paroles(name)


    MyScene.add_item(MyItemCantique_title.to_json())
    Mycollect.add_source(MyCantique_title.to_json())
    MyScene.add_item(MyItemCantique_paroles.to_json())
    Mycollect.add_source(MyCantique_paroles.to_json())

    Mycollect.add_source(MyScene.to_json())


def prepare_scene(data, filename) :     
    pass
    #load cantique from external file
    #head=''
    #with open(filename,"r",encoding="utf-8") as cantique :
        #head = ''.join([next(cantique) for x in range(2)])
    #    fileContents = '\n\n\n\n'+cantique.read()

    #manage title
    #cantique_title["name"]=filename+': titre'
    #cantique_title["settings"]["text"]=head
    #data["sources"].append(cantique_title)

    #title_into_scene["name"]= filename+': titre'

    #create new cantique source
    #src_txt["name"]=filename+': paroles'
    #src_txt["settings"]['text']=fileContents
    #data["sources"].append(src_txt)

    #txt_into_scene["name"]=filename+': paroles'

    #create new scene source
    #scene_item["name"] = 'scene : '+filename
    #scene_item["settings"]["items"].append(txt_into_scene)
    #scene_item["settings"]["items"].append(title_into_scene)
    #data["sources"].append(scene_item)
    #return data
    
#open template into data object
#with open('Template.json',"r",encoding="utf-8") as template:
#    data = json.load(template)

name = "Dimanche 17 janvier 2021"
Mycollect=Scene_Collection(name)

prepare_cantique(Mycollect,"Frappez dans vos mains")
prepare_cantique(Mycollect,"Viens, Saint-Esprit")
prepare_cantique(Mycollect,"Si vous saviez quel Sauveur")

with open(name+".json", 'w') as outfile:
        json.dump(Mycollect.to_json(), outfile)