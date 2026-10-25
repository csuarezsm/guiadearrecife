#!/usr/bin/env python3
"""Comprueba el contenido antes de publicar. Si encuentra errores, sale con código 1
y la web NO se publica (así un fallo de la tarea automática nunca rompe el portal).

Uso: python3 scripts/validar.py [--solo-fecha AAAA-MM-DD]
"""
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from build import parse_file, ORDEN_SECCIONES, MUNICIPIOS  # noqa: E402
from iconos import ICONOS  # noqa: E402

errores, avisos = [], []
hoy = date.today()
solo = None
if "--solo-fecha" in sys.argv:
    solo = date.fromisoformat(sys.argv[sys.argv.index("--solo-fecha") + 1])
BLOQUES = {"diez", "empresas", "ciber", "redes"}


def err(f, msg): errores.append(f"{f}: {msg}")
def warn(f, msg): avisos.append(f"{f}: {msg}")


titulos = {}
for p in sorted((ROOT / "content" / "noticias").glob("*.md")):
    try:
        meta, body = parse_file(p)
    except SystemExit as e:
        err(p.name, str(e)); continue
    try:
        f = date.fromisoformat(meta.get("fecha", ""))
    except ValueError:
        err(p.name, "fecha no válida"); continue
    if solo and f != solo:
        continue
    if not p.stem.startswith(f.isoformat()):
        err(p.name, "el nombre del archivo debe empezar por la fecha")
    if f > hoy + timedelta(days=1):
        err(p.name, "fecha en el futuro")
    for k in ("titulo", "entradilla", "seccion", "municipios", "titulo_en", "entradilla_en"):
        if not meta.get(k):
            err(p.name, f"falta el campo '{k}'")
    if meta.get("seccion") and meta["seccion"] not in ORDEN_SECCIONES:
        err(p.name, f"sección desconocida '{meta['seccion']}'")
    for m in str(meta.get("municipios", "")).split(","):
        if m.strip() and m.strip() not in MUNICIPIOS:
            err(p.name, f"municipio desconocido '{m.strip()}'")
    if meta.get("icono") and meta["icono"] not in ICONOS:
        err(p.name, f"icono desconocido '{meta['icono']}'")
    bloque = meta.get("bloque", "diez")
    if bloque not in BLOQUES:
        err(p.name, f"bloque desconocido '{bloque}'")
    if bloque == "diez" and not str(meta.get("orden", "")).isdigit():
        err(p.name, "las noticias del bloque 'diez' necesitan 'orden'")
    fuentes = meta.get("fuentes") or []
    if not fuentes:
        err(p.name, "sin fuentes")
    for line in fuentes:
        nombre, _, url = line.partition("|")
        if not nombre.strip() or not re.match(r"https?://\S+$", url.strip()):
            err(p.name, f"fuente mal escrita: '{line}'")
    es, sep, en = body.partition("\n[en]\n")
    if not sep or len(en.strip()) < 80:
        err(p.name, "falta el texto en inglés después de [en]")
    if len(es.strip()) < 200:
        err(p.name, "texto en español demasiado corto")
    if len(es.split()) > 400:
        warn(p.name, "texto largo (>400 palabras): los resúmenes deben ser breves")
    if len(meta.get("titulo", "")) > 130:
        warn(p.name, "titular muy largo")
    clave = re.sub(r"\W+", " ", meta.get("titulo", "").lower()).strip()
    if clave in titulos:
        err(p.name, f"titular repetido con {titulos[clave]}")
    titulos[clave] = p.name

ordenes = {}
for p in (ROOT / "content" / "noticias").glob("*.md"):
    meta, _ = parse_file(p)
    if meta.get("bloque", "diez") == "diez" and str(meta.get("orden", "")).isdigit():
        k = (meta["fecha"], int(meta["orden"]))
        if k in ordenes:
            err(p.name, f"orden {k[1]} repetido el {k[0]} (también en {ordenes[k]})")
        ordenes[k] = p.name

for p in sorted((ROOT / "content" / "agenda").glob("*.md")):
    meta, _ = parse_file(p)
    for k in ("titulo", "fecha", "lugar", "municipio", "categoria", "fuente"):
        if not meta.get(k):
            err(p.name, f"falta el campo '{k}' en la agenda")
    if meta.get("municipio") and meta["municipio"] not in MUNICIPIOS:
        err(p.name, f"municipio desconocido '{meta['municipio']}'")
    if meta.get("fecha_fin") and meta.get("fecha") and str(meta["fecha_fin"]) < str(meta["fecha"]):
        err(p.name, "fecha_fin es anterior a fecha")
    if meta.get("imagen"):
        img = ROOT / meta["imagen"]
        if not str(meta["imagen"]).startswith("img/agenda/") or img.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            err(p.name, "imagen debe estar en img/agenda/ y ser .jpg, .png o .webp")
        elif not img.exists():
            err(p.name, f"no existe la imagen {meta['imagen']}")
        elif img.stat().st_size > 1_500_000:
            warn(p.name, f"imagen de {img.stat().st_size // 1024} KB: conviene que pese menos de 1,5 MB")

for p in sorted((ROOT / "content" / "dias").glob("*.md")):
    meta, _ = parse_file(p)
    if not meta.get("fecha"):
        err(p.name, "falta la fecha")

for a in avisos:
    print("AVISO  ", a)
for e in errores:
    print("ERROR  ", e)
print(f"{len(errores)} errores, {len(avisos)} avisos")
sys.exit(1 if errores else 0)
