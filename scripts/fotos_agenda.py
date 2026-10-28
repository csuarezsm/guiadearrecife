#!/usr/bin/env python3
"""Añade la foto o cartel oficial a los actos de la agenda que aún no la tienen.

Para cada content/agenda/*.md sin `imagen:`, abre la URL de su `fuente`, busca la
imagen principal de la ficha (og:image o twitter:image), la descarga en
img/agenda/<nombre del .md>.<jpg|png|webp>, comprueba que es una imagen de menos
de 1,5 MB y añade `imagen:` y `credito:` al .md.

Nunca usa fotos de medios de comunicación: si la fuente es un medio, salta el acto.
Solo usa la biblioteca estándar de Python.

Uso: python3 scripts/fotos_agenda.py [--prueba] [--desde AAAA-MM-DD] [archivo.md ...]
  --prueba   enseña lo que haría sin descargar ni tocar nada
  --desde    solo actos que terminan en esa fecha o después (por defecto, hoy)
"""
import re
import sys
import urllib.request
from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
AGENDA = ROOT / "content" / "agenda"
IMG = ROOT / "img" / "agenda"
MAX_BYTES = 1_500_000
AGENTE = "Mozilla/5.0 (compatible; GuiaDeArrecife/1.0; +https://guiadearrecife.es/)"

# Medios de comunicación: sus fotos no se usan.
MEDIOS = (
    "lavozdelanzarote.com", "diariodelanzarote.com", "lancelotdigital.com",
    "cronicasdelanzarote.es", "canarias7.es", "laprovincia.es", "eldiario.es",
    "rtvc.es", "lanzaroteinformacion.com", "radiolanzarote.es", "gazettelife.com",
    "revistaalsolajero.com",
)

# Nombre con el que se acredita la foto, según el dominio de la ficha.
CREDITOS = {
    "culturalanzarote.com": "Cultura Lanzarote",
    "cabildodelanzarote.com": "Cabildo de Lanzarote",
    "cactlanzarote.com": "CACT Lanzarote",
    "coolturalanzarote.com": "Cooltura Lanzarote",
    "fiestaslanzarote.com": "Fiestas Lanzarote",
    "arrecife.es": "Ayuntamiento de Arrecife",
    "teguise.es": "Ayuntamiento de Teguise",
    "sanbartolome.es": "Ayuntamiento de San Bartolomé",
    "ayuntamientodetias.es": "Ayuntamiento de Tías",
    "yaiza.es": "Ayuntamiento de Yaiza",
    "tinajo.es": "Ayuntamiento de Tinajo",
    "ayuntamientodeharia.com": "Ayuntamiento de Haría",
    "ecoentradas.com": "Ecoentradas",
    "tomaticket.es": "Tomaticket",
    "ociolanzarote.com": "OcioLanzarote",
    "fihj.es": "Festival Internacional de Humor Jameos",
    "rockthesport.com": "Rockthesport",
    "sportmaniacs.com": "Sportmaniacs",
    "clublasanta.com": "Club La Santa",
}

FIRMAS = {b"\xff\xd8\xff": ".jpg", b"\x89PNG\r\n\x1a\n": ".png"}


def dominio(url):
    d = urlparse(url).hostname or ""
    return d[4:] if d.startswith("www.") else d


def es_de(d, lista):
    return any(d == x or d.endswith("." + x) for x in lista)


def leer(url, limite=None):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(limite + 1 if limite else -1), r.geturl()


def imagen_de_la_ficha(html, base):
    for prop in ("og:image:secure_url", "og:image", "twitter:image", "twitter:image:src"):
        for tag in re.findall(r"<meta\b[^>]*>", html, re.I):
            if re.search(r'(?:property|name)\s*=\s*["\']%s["\']' % re.escape(prop), tag, re.I):
                m = re.search(r'content\s*=\s*["\']([^"\']+)["\']', tag, re.I)
                if m and "logo" not in m.group(1).lower():
                    return urljoin(base, unescape(m.group(1).strip()))
    return None


def extension(datos):
    for firma, ext in FIRMAS.items():
        if datos.startswith(firma):
            return ext
    if datos[:4] == b"RIFF" and datos[8:12] == b"WEBP":
        return ".webp"
    return None


def cabecera(texto):
    m = re.match(r"---\n(.*?)\n---\n", texto, re.S)
    if not m:
        return None, None
    campos = dict(re.findall(r"^(\w+):[ \t]*(.*)$", m.group(1), re.M))
    return campos, m.end(1)


def procesar(md, prueba, desde):
    texto = md.read_text(encoding="utf-8")
    campos, fin = cabecera(texto)
    if campos is None:
        return "sin cabecera"
    if campos.get("imagen"):
        return None
    if (campos.get("fecha_fin") or campos.get("fecha", "")) < desde:
        return None
    m = re.search(r"https?://\S+", campos.get("fuente", ""))
    if not m:
        return "sin URL en fuente"
    url = m.group(0)
    d = dominio(url)
    if es_de(d, MEDIOS):
        return f"la fuente es un medio ({d}): busca la ficha oficial y cambia la fuente"
    try:
        html, base = leer(url)
    except Exception as e:
        return f"no se pudo abrir {url}: {e}"
    img_url = imagen_de_la_ficha(html.decode("utf-8", "replace"), base)
    if not img_url:
        return "la ficha no trae foto (no se pone el campo)"
    if prueba:
        return f"descargaría {img_url}"
    try:
        datos, _ = leer(img_url, MAX_BYTES)
    except Exception as e:
        return f"no se pudo descargar {img_url}: {e}"
    if len(datos) > MAX_BYTES:
        return f"la foto pesa más de 1,5 MB: {img_url}"
    ext = extension(datos)
    if not ext:
        return f"no es una imagen jpg, png ni webp: {img_url}"
    IMG.mkdir(parents=True, exist_ok=True)
    destino = IMG / (md.stem + ext)
    destino.write_bytes(datos)
    credito = next((v for k, v in CREDITOS.items() if es_de(d, [k])), d)
    lineas = f"\nimagen: img/agenda/{destino.name}\ncredito: Foto: {credito}"
    md.write_text(texto[:fin] + lineas + texto[fin:], encoding="utf-8")
    return f"OK {destino.name} ({len(datos) // 1024} KB, {credito})"


def main():
    args = sys.argv[1:]
    prueba = "--prueba" in args
    desde = date.today().isoformat()
    if "--desde" in args:
        desde = args[args.index("--desde") + 1]
        args.remove(desde)
    archivos = [Path(a) for a in args if not a.startswith("--")] or sorted(AGENDA.glob("*.md"))
    hechas = 0
    for md in archivos:
        res = procesar(md, prueba, desde)
        if res:
            print(f"{md.name}: {res}")
            hechas += res.startswith("OK")
    print(f"\n{hechas} fotos añadidas.")


if __name__ == "__main__":
    main()
