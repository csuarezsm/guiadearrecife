# Guía de Arrecife

Portal de noticias de Lanzarote y La Graciosa (guiadearrecife.es), en español e inglés.

## Cómo funciona
1. Cada mañana la tarea programada "Edición diaria" (texto en `docs/tarea-diaria.md`) busca las noticias, escribe los archivos en `content/` y los sube a este repositorio.
2. GitHub Actions (`.github/workflows/publicar.yml`) valida el contenido (`scripts/validar.py`), genera la web (`build.py`) y la publica en GitHub Pages con el dominio guiadearrecife.es.
3. Si la validación falla, la web no cambia: sigue publicada la versión anterior.

## Modo de publicación (`config.json`)
- `revision`: la tarea abre una propuesta de cambios; se publica cuando Carlos la aprueba.
- `automatico`: la tarea publica directamente. Cada noticia muestra un aviso breve de IA.

## Contenido
- `content/noticias/AAAA-MM-DD-titulo.md` — una noticia (español arriba, inglés después de `[en]`).
- `content/dias/AAAA-MM-DD.md` — saludo y tema del día.
- `content/agenda/AAAA-MM-DD-titulo.md` — un acto de la agenda.
- `content/negocios/*.md` — fichas del directorio de Arrecife.
- `docs/linea-editorial.md` — la línea editorial que aplica la tarea.

## Probar en local
```
python3 scripts/validar.py && python3 build.py && python3 -m http.server -d _site
```
