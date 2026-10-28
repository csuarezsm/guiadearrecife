#!/usr/bin/env bash
# Valida, genera y publica los cambios de la agenda hechos por una automatización.
# Respeta config.json: modo "automatico" publica en main; modo "revision" abre una propuesta.
# Uso: scripts/publicar_agenda.sh "Mensaje del commit"
set -euo pipefail
cd "$(dirname "$0")/.."

MENSAJE="${1:-Agenda: actualización automática}"
HOY="$(TZ=Atlantic/Canary date +%F)"

if [ -z "$(git status --porcelain content/agenda img/agenda)" ]; then
  echo "Sin cambios en la agenda."
  exit 0
fi

python3 scripts/validar.py
python3 build.py

git config user.name "Guía de Arrecife (automático)"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
MODO="$(python3 -c 'import json; print(json.load(open("config.json")).get("modo", "revision"))')"

if [ "$MODO" = "automatico" ]; then
  git add content/agenda img/agenda
  git commit -q -m "$MENSAJE"
  for i in 1 2 3; do
    git pull -q --rebase origin main && git push -q origin HEAD:main && break
    sleep $((i * 5))
  done
  # Lo que sube GITHUB_TOKEN no lanza otros flujos: se lanza la publicación a mano.
  gh workflow run publicar.yml --ref main
  echo "Publicado en main."
else
  RAMA="agenda-$HOY-$(date +%H%M)"
  git checkout -q -b "$RAMA"
  git add content/agenda img/agenda
  git commit -q -m "$MENSAJE"
  git push -q -u origin "$RAMA"
  gh pr create --base main --head "$RAMA" --title "$MENSAJE" \
    --body "Cambios automáticos en la agenda del $HOY. Revisa y fusiona para publicar."
  echo "Propuesta abierta en la rama $RAMA."
fi
