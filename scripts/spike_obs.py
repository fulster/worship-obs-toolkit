"""Spike obs-websocket (préparation de D-004) — exécuter sur le poste qui a OBS.

But : mesurer ce qu'on peut réellement faire via obs-websocket (créer une
collection isolée, des scènes, des sources texte/image, un filtre de
défilement), pour choisir l'approche d'« envoi vers OBS ».

Prérequis :
  - OBS Studio >= 28 (serveur WebSocket intégré).
  - OBS : Outils > Paramètres du serveur WebSocket > « Activer le serveur
    WebSocket », noter le port (4455 par défaut) et le mot de passe.

Lancement (dépendance éphémère, rien n'est ajouté au projet) :
  uv run --with obsws-python python scripts/spike_obs.py --password VOTRE_MDP
"""

import argparse
import sys


def step(label, fn):
    """Exécute fn() et rapporte OK / l'erreur, sans interrompre le spike."""
    try:
        res = fn()
        print(f"  [OK]   {label}" + (f" -> {res}" if res is not None else ""))
        return res
    except Exception as e:  # noqa: BLE001
        print(f"  [ECHEC] {label} : {type(e).__name__}: {e}")
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=4455)
    ap.add_argument("--password", default="")
    args = ap.parse_args()

    try:
        import obsws_python as obs
    except ImportError:
        sys.exit("Lancer avec : uv run --with obsws-python python scripts/spike_obs.py --password ...")

    print(f"Connexion à obs-websocket {args.host}:{args.port} ...")
    try:
        cl = obs.ReqClient(host=args.host, port=args.port, password=args.password, timeout=5)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"Connexion impossible : {e}\n(OBS ouvert ? serveur WebSocket activé ? bon port/mot de passe ?)")

    v = cl.get_version()
    print(f"OBS {v.obs_version} | websocket {v.obs_web_socket_version} | RPC v{v.rpc_version}")
    print("Sources d'entrée disponibles :", getattr(v, "available_requests", "?") and "(liste dispo)")

    print("\n--- Lecture ---")
    step("get_scene_collection_list",
         lambda: cl.get_scene_collection_list().scene_collections)
    step("get_scene_list",
         lambda: [s["sceneName"] for s in cl.get_scene_list().scenes])
    step("get_input_kind_list (types de sources)",
         lambda: cl.get_input_kind_list().input_kinds)

    print("\n--- Création d'une collection isolée (approche A) ---")
    made_coll = step("create_scene_collection('__wotk_test')",
                     lambda: cl.create_scene_collection("__wotk_test") or "créée + activée")

    print("\n--- Création de scènes / sources / filtre ---")
    step("create_scene('__wotk_scene')", lambda: cl.create_scene("__wotk_scene") or "ok")
    step("create_input texte (text_gdiplus_v2)",
         lambda: cl.create_input("__wotk_scene", "__wotk_txt", "text_gdiplus_v2",
                                 {"text": "Essai WOTK"}, True) or "ok")
    step("create_input image (image_source)",
         lambda: cl.create_input("__wotk_scene", "__wotk_img", "image_source",
                                 {"file": ""}, True) or "ok")
    step("create_source_filter (scroll_filter)",
         lambda: cl.create_source_filter("__wotk_txt", "Défilement", "scroll_filter",
                                         {"speed_y": 11.0}) or "ok")

    print("\n--- Nettoyage ---")
    if made_coll is not None:
        print("  (collection de test '__wotk_test' créée ; supprimez-la dans OBS :")
        print("   Scene Collection > Manage > supprimer '__wotk_test', et rebasculez sur la vôtre.)")
    else:
        step("remove_scene('__wotk_scene')", lambda: cl.remove_scene("__wotk_scene") or "ok")

    print("\nSpike terminé. Copie-colle toute cette sortie.")


if __name__ == "__main__":
    main()
