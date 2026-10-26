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

## SEO
- Cada portada se publica en SVG y en PNG de 1200×675 (Google Discover, WhatsApp y Facebook no usan SVG). El PNG lo genera `build.py` con `rsvg-convert` (paquete `librsvg2-bin`, lo instala el workflow).
- Datos estructurados: `NewsArticle` (con imagen, fechas y logo del medio), `WebSite` y `NewsMediaOrganization` en la portada y `BreadcrumbList` en todas las páginas.
- `sitemap.xml` con fecha de actualización e idiomas, y `news-sitemap.xml` con las noticias de las últimas 48 horas para Google News.
- Si una noticia se corrige después de publicarla, añade `actualizado: AAAA-MM-DDTHH:MM:SS+00:00` en su cabecera.
- Las fuentes de letra están en `assets/fonts/` (no se cargan desde Google).

## Probar en local
```
python3 scripts/validar.py && python3 build.py && python3 -m http.server -d _site
```
