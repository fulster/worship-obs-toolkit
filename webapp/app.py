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
    theme = (data.get('theme') or DEFAULT_THEME).strip()

    entrees = []
    for e in data.get('entrees', []):
        numero = (e.get('numero') or '').strip()
        if not numero:
            continue
        selection = (e.get('selection') or '').strip()
        line = f"{numero} ({selection})" if selection else numero
        entrees.append((line, e.get('origin', 'cantique')))

    images = generate.telecharger_images(CONFIG, theme)
    info = generate.generer_culte(titre, entrees, CONFIG, *images)

    return jsonify({
        'titre': titre,
        'fname': info['fname'],
        'ajoutes': info['ajoutes'],
        'non_trouves': info['non_trouves'],
        'a_relire': info['a_relire'],
        'download': f"/api/telecharger/{info['fname']}.zip",
    })


@app.route('/api/telecharger/<path:fname>')
def api_telecharger(fname):
    """Sert le .zip généré depuis le dossier de sortie configuré."""
    output_dir = Path(CONFIG['paths']['output']).resolve()
    return send_from_directory(output_dir, fname, as_attachment=True)


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


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
