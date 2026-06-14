"""Envoi d'une collection de scènes vers OBS via obs-websocket (D-004).

Rejoue le JSON de collection produit par `obs_json_resources` (aucune logique
de construction de scènes n'est ré-implémentée — `obs_json_resources` reste
l'unique source de vérité). Crée une **collection de scènes dédiée** dans OBS,
puis ses sources, scènes, items (+ transformations) et filtres.

Nécessite OBS >= 28 (serveur obs-websocket v5 activé) et le client
`obsws-python`. Voir D-004.
"""

from __future__ import annotations

# bounds_type (entier, JSON OBS) -> enum obs-websocket.
_BOUNDS = {
    0: 'OBS_BOUNDS_NONE', 1: 'OBS_BOUNDS_STRETCH', 2: 'OBS_BOUNDS_SCALE_INNER',
    3: 'OBS_BOUNDS_SCALE_OUTER', 4: 'OBS_BOUNDS_SCALE_TO_WIDTH',
    5: 'OBS_BOUNDS_SCALE_TO_HEIGHT', 6: 'OBS_BOUNDS_MAX_ONLY',
}


def _transform(item: dict) -> dict:
    """Item de scène (JSON OBS) -> transformation obs-websocket."""
    t = {
        'alignment': item.get('align', 5),
        'positionX': float(item.get('pos', {}).get('x', 0.0)),
        'positionY': float(item.get('pos', {}).get('y', 0.0)),
        'scaleX': float(item.get('scale', {}).get('x', 1.0)),
        'scaleY': float(item.get('scale', {}).get('y', 1.0)),
        'rotation': float(item.get('rot', 0.0)),
        'cropLeft': int(item.get('crop_left', 0)),
        'cropRight': int(item.get('crop_right', 0)),
        'cropTop': int(item.get('crop_top', 0)),
        'cropBottom': int(item.get('crop_bottom', 0)),
    }
    bt = item.get('bounds_type', 0)
    if bt:
        t['boundsType'] = _BOUNDS.get(bt, 'OBS_BOUNDS_NONE')
        t['boundsAlignment'] = item.get('bounds_align', 0)
        t['boundsWidth'] = float(item.get('bounds', {}).get('x', 0.0)) or 1.0
        t['boundsHeight'] = float(item.get('bounds', {}).get('y', 0.0)) or 1.0
    return t


def _item_id(resp):
    return getattr(resp, 'scene_item_id', None)


def push_collection(coll: dict, host='localhost', port=4455, password='',
                    name=None, timeout=10) -> dict:
    """Pousse la collection `coll` (dict `to_json()`) vers OBS.

    Retourne `{collection, scenes, sources}` (nom de collection créé + comptes).
    Lève une exception si OBS est injoignable.
    """
    import obsws_python as obs

    name = (name or coll.get('name') or 'Culte').strip() or 'Culte'
    cl = obs.ReqClient(host=host, port=port, password=password, timeout=timeout)

    sources = coll.get('sources', [])
    by_name = {s['name']: s for s in sources}
    inputs = {s['name']: s for s in sources if s.get('id') != 'scene'}
    scene_names = [s['name'] for s in sources if s.get('id') == 'scene']
    order = [e['name'] for e in coll.get('scene_order', []) if e.get('name') in by_name]
    ordered = [n for n in order if by_name[n].get('id') == 'scene']
    ordered += [n for n in scene_names if n not in ordered]

    # 1) Collection dédiée (nom unique, suffixe « N » comme OBS si déjà pris).
    existing = list(cl.get_scene_collection_list().scene_collections)
    final, i = name, 2
    while final in existing:
        final, i = f'{name} {i}', i + 1
    cl.create_scene_collection(final)

    # 2) Scènes + items + filtres, en rejouant le JSON.
    created = set()
    for scene_name in ordered:
        cl.create_scene(scene_name)
        for item in by_name[scene_name].get('settings', {}).get('items', []):
            inp = inputs.get(item.get('name'))
            if inp is None:
                continue
            iname = inp['name']
            if iname not in created:
                kind = inp.get('versioned_id') or inp.get('id')
                resp = cl.create_input(scene_name, iname, kind, inp.get('settings', {}), True)
                created.add(iname)
                for f in inp.get('filters', []):
                    cl.create_source_filter(
                        iname, f.get('name', 'filtre'),
                        f.get('versioned_id') or f.get('id'), f.get('settings', {}))
            else:
                resp = cl.create_scene_item(scene_name, iname, True)
            iid = _item_id(resp)
            if iid is not None:
                cl.set_scene_item_transform(scene_name, iid, _transform(item))

    # 3) Basculer sur la 1re scène, retirer les scènes parasites (scène par
    #    défaut créée avec la collection).
    if ordered:
        cl.set_current_program_scene(ordered[0])
    keep = set(ordered)
    for s in cl.get_scene_list().scenes:
        nm = s['sceneName']
        if nm not in keep:
            try:
                cl.remove_scene(nm)
            except Exception:
                pass

    return {'collection': final, 'scenes': len(ordered), 'sources': len(inputs)}
