import json
from obs_json_resources import Scene_Collection

name = "Dimanche 17 janvier 2021 YESSSS"

collection = Scene_Collection(name)

# Add scenes from ./txt directory (not ordered right now)
collection.generate_scenes_from_dir('./txt')

# Add scenes in that order
# collection.add_scene('./txt/21-07 Qu’aujourd’hui toute la terre.txt')
# collection.add_scene('./txt/Psaume 36 O Seigneur, ta fidélité.txt')
# collection.add_scene('./txt/(spontané) 36-12 O notre Dieu, nous te prions.txt')
# collection.add_scene('./txt/(spontané) 42-02 Du cœur et de la voix.txt')
# collection.add_scene('./txt/(spontané) 45-01 Ta volonté, Seigneur mon Dieu.txt')
# collection.add_scene('./txt/22-05 Dans ta parole, Ô Dieu.txt')
# collection.add_scene('./txt/46-05 Mon sauveur, je voudrais être.txt')
# collection.add_scene('./txt/36-08 O Jésus, tu nous appelles.txt')

with open(name+".json", 'w') as outfile:
        json.dump(collection.to_json(), outfile)