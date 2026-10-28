# Acceso a la red del entorno en la nube

La tarea diaria necesita abrir las fuentes de la agenda y descargar sus fotos. Si el entorno
tiene la red limitada, estas webs salen bloqueadas y la agenda no se puede actualizar.

## Cómo abrirla
En claude.ai/code, menú del entorno (barra de título de la sesión) → **Edit** → **Network access**:
- O bien elige el nivel de acceso completo (lo más sencillo, porque las fotos pueden estar en
  dominios de terceros, como CDN de imágenes).
- O bien deja el nivel limitado y añade en **Allowed domains** la lista de abajo, manteniendo
  marcada la casilla de gestores de paquetes.

Instrucciones: https://code.claude.com/docs/en/cloud-environments#network-access

Después, comprueba con `python3 scripts/comprobar_red.py`.

## Dominios que usa la agenda
```
fiestaslanzarote.com
culturalanzarote.com
cabildodelanzarote.com
cactlanzarote.com
coolturalanzarote.com
arrecife.es
teguise.es
sanbartolome.es
ayuntamientodetias.es
yaiza.es
tinajo.es
ayuntamientodeharia.com
turismolanzarote.com
ociolanzarote.com
tomaticket.es
ecoentradas.com
fihj.es
rockthesport.com
sportmaniacs.com
clublasanta.com
lavozdelanzarote.com
diariodelanzarote.com
lancelotdigital.com
cronicasdelanzarote.es
canarias7.es
laprovincia.es
eldiario.es
rtvc.es
```
Si un dominio admite subdominios en la lista (p. ej. `*.culturalanzarote.com`), añádelos también:
las webs de WordPress suelen servir las fotos desde el mismo dominio, pero algunas usan `www.` o
un CDN aparte. Si `scripts/fotos_agenda.py` dice "no se pudo descargar" con otro dominio, añade
ese dominio.

## Fotos desde tu ordenador
Si prefieres no abrir la red, puedes poner las fotos desde tu ordenador:
```
git pull
python3 scripts/fotos_agenda.py --prueba   # enseña lo que haría
python3 scripts/fotos_agenda.py            # descarga y añade imagen/credito
python3 scripts/validar.py && python3 build.py
git add content/agenda img/agenda && git commit -m "Agenda: fotos de los actos" && git push
```
