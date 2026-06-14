#!/usr/bin/env bash
# Assemble le « kit de déploiement » (runtime) dans
# dist/worship-obs-toolkit-kit.zip : juste ce qu'il faut pour installer
# l'interface sur le poste de l'église (cf. docs/deploiement.md). Exclut le
# dev (ADR, raws de conversion, scripts de migration, config secrète).
set -euo pipefail

NAME="worship-obs-toolkit-kit"
OUT="dist"
STAGE="$OUT/$NAME"

rm -rf "$OUT"
mkdir -p "$STAGE/webapp" "$STAGE/docs" "$STAGE/stock"

# Code, interface, templates, conf d'exemple.
cp generate.py obs_json_resources.py obs_push.py pyproject.toml uv.lock README.md config.json.example "$STAGE/"
cp webapp/app.py webapp/corpus_index.py "$STAGE/webapp/"
cp -r webapp/static "$STAGE/webapp/"
cp -r tpl "$STAGE/"

# Corpus (cantiques + prières).
cp -r stock/cantiques "$STAGE/stock/"
cp -r stock/prieres "$STAGE/stock/"

# Séries de spontanés + liste d'exemple (chants.txt est exclu : fichier de travail).
cp ./*.txt "$STAGE/" 2>/dev/null || true
rm -f "$STAGE/chants.txt"

# Lanceurs + déploiement.
cp "Preparer un culte.bat" serveur.bat installer-poste-eglise.bat \
   arreter-serveur.bat desinstaller-poste-eglise.bat "$STAGE/"
cp docs/deploiement.md docs/format-cantique.md "$STAGE/docs/"
[ -f docs/relecture-corpus.md ] && cp docs/relecture-corpus.md "$STAGE/docs/" || true

( cd "$OUT" && zip -r -q "$NAME.zip" "$NAME" )
echo "Kit assemblé : $OUT/$NAME.zip"
du -h "$OUT/$NAME.zip" | cut -f1 | sed 's/^/Taille : /'
