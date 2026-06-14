"""Backend Flask de l'interface de préparation des cultes (cf. D-003).

Application web **locale** (non publique) : sert une interface de composition
de culte et réutilise le pipeline existant (`generate.generer_culte`) — aucune
logique de construction de scènes n'est dupliquée ici.

Lancement (depuis n'importe où) :

    uv run python webapp/app.py        # http://127.0.0.1:5000

Le serveur se place dans la racine du dépôt pour que les chemins relatifs du
pipeline (`stock/`, `docs/`, `config.json`) résolvent.
"""

import json
import os
import re
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)   # importer generate / obs_json_resources
sys.path.insert(0, HERE)   # importer corpus_index
os.chdir(ROOT)             # chemins relatifs du pipeline (stock/, docs/, config)

from flask import Flask, request, jsonify, send_from_directory, abort  # noqa: E402

import generate  # noqa: E402
import corpus_index  # noqa: E402

DEFAULT_THEME = "nature,landscape,forest,mountains"
CULTES_DIR = os.path.join(HERE, 'cultes')
os.makedirs(CULTES_DIR, exist_ok=True)
ID_RE = re.compile(r'^[a-z0-9-]+$')

app = Flask(__name__, static_folder=os.path.join(HERE, 'static'), static_url_path='')

# Chargés une fois au démarrage. (Redémarrer le serveur pour rafraîchir l'index
# après une relecture du corpus.)
CONFIG = generate.charger_config()
INDEX = corpus_index.build_index(
    CONFIG['paths'].get('stock_cantiques', 'stock/cantiques'),
    CONFIG['paths'].get('stock_prieres', 'stock/prieres'),
    generate.load_flagged_numeros(),
)
BY_NUMERO = {e['numero']: e for e in INDEX}


def _build_entrees(data):
    """Liste `(ligne, origine)` depuis le corps JSON (entrées composées)."""
    out = []
    for e in data.get('entrees', []):
        numero = (e.get('numero') or '').strip()
        if not numero:
            continue
        selection = (e.get('selection') or '').strip()
        line = f'{numero} ({selection})' if selection else numero
        out.append((line, e.get('origin', 'cantique')))
    return out


def _images_for(data):
    """Images de fond : réutilise l'aperçu si fourni et présent, sinon télécharge."""
    theme = (data.get('theme') or DEFAULT_THEME).strip()
    imgs = data.get('images') or {}
    img_dir = Path(CONFIG['paths']['images']).resolve()
    pa, pe = img_dir / (imgs.get('accueil') or ''), img_dir / (imgs.get('envoi') or '')
    if imgs.get('accueil') and imgs.get('envoi') and pa.exists() and pe.exists():
        return pa, pe, imgs['accueil'], imgs['envoi']
    return generate.telecharger_images(CONFIG, theme)


# --- Pages ---------------------------------------------------------------------

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


# --- API : corpus --------------------------------------------------------------

@app.route('/api/cantiques')
def api_cantiques():
    """Recherche dans le corpus. `?q=` (titre/numéro), `?limit=`."""
    q = request.args.get('q', '')
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
    except ValueError:
        limit = 50
    return jsonify(corpus_index.search(INDEX, q, limit))


@app.route('/api/stats')
def api_stats():
    """Totaux du corpus (pour l'affichage)."""
    return jsonify({
        'total': len(INDEX),
        'cantiques': sum(1 for e in INDEX if e['kind'] == 'cantique'),
        'prieres': sum(1 for e in INDEX if e['kind'] == 'priere'),
    })


@app.route('/api/importer', methods=['POST'])
def api_importer():
    """Importe une liste collée (format chants.txt, en-tête [SPONTANES] géré).

    Corps : `{texte}`. Retourne des entrées enrichies (titre, couplets…) prêtes
    pour la composition ; `found:false` pour les lignes non reconnues/introuvables.
    """
    data = request.get_json(silent=True) or {}
    texte = data.get('texte', '') or ''
    out = []
    for line, origin in generate.interpreter_lignes(texte.splitlines()):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('[SPONTANES]'):
            continue
        numero, sel = generate.extraire_numero_selection(line)
        if numero is None:
            out.append({'numero': '', 'titre': line[:48], 'n_couplets': 0, 'refrain': False,
                        'a_relire': False, 'selection': '', 'origin': origin, 'found': False})
            continue
        e = BY_NUMERO.get(numero)
        if e:
            out.append({'numero': numero, 'titre': e['titre'], 'n_couplets': e['n_couplets'],
                        'refrain': e['refrain'], 'a_relire': e['a_relire'],
                        'selection': sel, 'origin': origin, 'found': True})
        else:
            out.append({'numero': numero, 'titre': '(introuvable)', 'n_couplets': 0, 'refrain': False,
                        'a_relire': False, 'selection': sel, 'origin': origin, 'found': False})
    return jsonify(out)


# --- API : génération ----------------------------------------------------------

@app.route('/api/generer', methods=['POST'])
def api_generer():
    """Génère le .zip OBS d'un culte composé.

    Corps JSON : `{titre, theme?, entrees: [{numero, selection?, origin?}]}`.
    Renvoie l'info de génération + un lien de téléchargement.
    """
    data = request.get_json(silent=True) or {}
    titre = (data.get('titre') or 'Culte').strip()
    try:
        info = generate.generer_culte(titre, _build_entrees(data), CONFIG, *_images_for(data))
    except Exception as exc:  # noqa: BLE001
        app.logger.exception('Echec de la generation')
        return jsonify({'error': f'{type(exc).__name__}: {exc}'}), 500

    return jsonify({
        'titre': titre,
        'fname': info['fname'],
        'ajoutes': info['ajoutes'],
        'non_trouves': info['non_trouves'],
        'a_relire': info['a_relire'],
        'download': f"/api/telecharger/{info['fname']}.zip",
    })


@app.route('/api/envoyer-obs', methods=['POST'])
def api_envoyer_obs():
    """Envoie le culte directement dans OBS via obs-websocket (D-004).

    Recrée une collection dédiée (en plus du `.zip`, ne le remplace pas).
    """
    import obs_push  # import paresseux (obsws-python)

    obs_cfg = CONFIG.get('obs') or {}
    if not obs_cfg.get('enabled', True):
        return jsonify({'error': "L'envoi vers OBS est désactivé (config « obs »)."}), 400

    data = request.get_json(silent=True) or {}
    titre = (data.get('titre') or 'Culte').strip()
    try:
        collection, info = generate.construire_collection(
            titre, _build_entrees(data), CONFIG, *_images_for(data))
    except Exception as exc:  # noqa: BLE001
        app.logger.exception('Echec de la construction')
        return jsonify({'error': f'{type(exc).__name__}: {exc}'}), 500

    try:
        res = obs_push.push_collection(
            collection.to_json(),
            host=obs_cfg.get('host', 'localhost'),
            port=int(obs_cfg.get('port', 4455)),
            password=obs_cfg.get('password', ''),
            name=titre)
    except Exception as exc:  # noqa: BLE001
        app.logger.exception('Echec envoi OBS')
        return jsonify({'error': f'OBS injoignable ou erreur : {exc}'}), 502

    return jsonify({
        'titre': titre,
        'collection': res['collection'],
        'scenes': res['scenes'],
        'ajoutes': info['ajoutes'],
        'non_trouves': info['non_trouves'],
        'a_relire': info['a_relire'],
    })


@app.route('/api/telecharger/<path:fname>')
def api_telecharger(fname):
    """Sert le .zip généré depuis le dossier de sortie configuré."""
    output_dir = Path(CONFIG['paths']['output']).resolve()
    return send_from_directory(output_dir, fname, as_attachment=True)


@app.route('/api/images', methods=['POST'])
def api_images():
    """Télécharge 2 images de fond (aperçu, avant génération) et renvoie leurs
    noms + URL. Les mêmes noms peuvent être passés à /api/generer pour réutiliser
    ces images au lieu d'en retélécharger."""
    data = request.get_json(silent=True) or {}
    theme = (data.get('theme') or DEFAULT_THEME).strip()
    _, _, a_name, e_name = generate.telecharger_images(CONFIG, theme)
    return jsonify({
        'accueil': a_name, 'envoi': e_name,
        'accueil_url': f'/api/image/{a_name}', 'envoi_url': f'/api/image/{e_name}',
    })


@app.route('/api/image/<path:name>')
def api_image(name):
    """Sert une image de fond depuis le dossier d'images configuré (aperçu)."""
    img_dir = Path(CONFIG['paths']['images']).resolve()
    return send_from_directory(img_dir, name)


# --- API : cultes sauvegardés --------------------------------------------------

def _culte_path(cid):
    if not ID_RE.match(cid or ''):
        abort(400, 'identifiant invalide')
    return os.path.join(CULTES_DIR, f'{cid}.json')


@app.route('/api/cultes', methods=['GET'])
def list_cultes():
    out = []
    for path in sorted(Path(CULTES_DIR).glob('*.json')):
        try:
            with open(path, encoding='utf-8') as f:
                c = json.load(f)
            out.append({'id': c.get('id'), 'titre': c.get('titre'),
                        'n_entrees': len(c.get('entrees') or [])})
        except Exception:
            continue
    return jsonify(out)


@app.route('/api/cultes', methods=['POST'])
def save_culte():
    data = request.get_json(silent=True) or {}
    titre = (data.get('titre') or 'Culte').strip()
    cid = generate.slugify(titre) or 'culte'
    payload = {
        'id': cid,
        'titre': titre,
        'theme': data.get('theme'),
        'entrees': data.get('entrees', []),
    }
    with open(_culte_path(cid), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return jsonify(payload)


@app.route('/api/cultes/<cid>', methods=['GET'])
def get_culte(cid):
    path = _culte_path(cid)
    if not os.path.exists(path):
        abort(404)
    with open(path, encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/cultes/<cid>', methods=['DELETE'])
def delete_culte(cid):
    path = _culte_path(cid)
    if os.path.exists(path):
        os.remove(path)
    return jsonify({'ok': True})


# --- API : séries de spontanés ([SPONTANES] *.txt) -----------------------------

SERIE_RE = re.compile(r'^[A-Z0-9_]+$')
SPONT_PREFIX = '[SPONTANES] '


def _serie_path(nom):
    if not SERIE_RE.match(nom or ''):
        abort(400, 'nom de série invalide')
    return f'{SPONT_PREFIX}{nom}.txt'


def _resoudre_ligne(line):
    """Entrée enrichie pour une ligne de spontanés (hors marqueur #n)."""
    numero, sel = generate.extraire_numero_selection(line)
    if numero is None:
        return {'placeholder': False, 'numero': '', 'titre': line[:48], 'n_couplets': 0,
                'refrain': False, 'a_relire': False, 'selection': '', 'found': False}
    e = BY_NUMERO.get(numero)
    if e:
        return {'placeholder': False, 'numero': numero, 'titre': e['titre'],
                'n_couplets': e['n_couplets'], 'refrain': e['refrain'],
                'a_relire': e['a_relire'], 'selection': sel, 'found': True}
    return {'placeholder': False, 'numero': numero, 'titre': '(introuvable)', 'n_couplets': 0,
            'refrain': False, 'a_relire': False, 'selection': sel, 'found': False}


@app.route('/api/spontanes')
def list_spontanes():
    noms = sorted(f[len(SPONT_PREFIX):-4] for f in os.listdir('.')
                  if f.startswith(SPONT_PREFIX) and f.endswith('.txt'))
    return jsonify(noms)


@app.route('/api/spontanes/<nom>')
def get_serie(nom):
    path = _serie_path(nom)
    if not os.path.exists(path):
        abort(404)
    entrees = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^#\d+$', line):
                entrees.append({'placeholder': True})
            else:
                entrees.append(_resoudre_ligne(line))
    return jsonify({'nom': nom, 'entrees': entrees})


@app.route('/api/spontanes/<nom>', methods=['POST'])
def save_serie(nom):
    path = _serie_path(nom)
    data = request.get_json(silent=True) or {}
    lines, ph = [], 0
    for e in data.get('entrees', []):
        if e.get('placeholder'):
            ph += 1
            lines.append(f'#{ph}')
            continue
        numero = (e.get('numero') or '').strip()
        if not numero:
            continue
        titre = (e.get('titre') or '').strip()
        sel = (e.get('selection') or '').strip()
        line = f'{numero} {titre}' if (titre and not titre.startswith('(')) else numero
        if sel:
            line += f' ({sel})'
        lines.append(line)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return jsonify({'nom': nom, 'count': len(lines)})


@app.route('/api/spontanes/<nom>', methods=['DELETE'])
def delete_serie(nom):
    path = _serie_path(nom)
    if os.path.exists(path):
        os.remove(path)
    return jsonify({'ok': True})


if __name__ == '__main__':
    host, port = '127.0.0.1', 5000
    if os.environ.get('WOTK_PROD') == '1':
        # Production (machine d'église, toujours allumé) : serveur WSGI waitress.
        from waitress import serve
        print(f'Serveur (waitress) sur http://{host}:{port}')
        serve(app, host=host, port=port)
    else:
        # Développement / lancement simple. WOTK_DEBUG=1 pour le rechargement auto.
        app.run(host=host, port=port, debug=os.environ.get('WOTK_DEBUG') == '1')
