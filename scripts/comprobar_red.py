#!/usr/bin/env python3
"""Comprueba si se pueden abrir las fuentes obligatorias de la agenda.

Uso: python3 scripts/comprobar_red.py
Si alguna sale bloqueada en el entorno en la nube, añade ese dominio en
Network access > Allowed domains (lista completa en docs/red.md).
"""
import sys
import urllib.request

FUENTES = [
    "https://fiestaslanzarote.com/",
    "https://culturalanzarote.com/eventos/",
    "https://www.cabildodelanzarote.com/agenda",
    "https://cactlanzarote.com/en/events",
    "https://coolturalanzarote.com/eventos/",
    "https://www.arrecife.es/",
    "https://www.teguise.es/",
    "https://www.sanbartolome.es/",
    "https://www.ayuntamientodetias.es/",
    "https://yaiza.es/",
    "https://www.tinajo.es/",
    "https://www.ayuntamientodeharia.com/",
    "https://turismolanzarote.com/en/events-calendar/",
    "https://ociolanzarote.com/en/events",
    "https://www.tomaticket.es/entradas/lanzarote",
    "https://www.ecoentradas.com/",
]

fallos = 0
for url in FUENTES:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (GuiaDeArrecife)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"OK        {r.status}  {url}")
    except Exception as e:
        fallos += 1
        print(f"BLOQUEADA      {url}  ({e})")
print(f"\n{len(FUENTES) - fallos} de {len(FUENTES)} fuentes accesibles.")
sys.exit(1 if fallos else 0)
