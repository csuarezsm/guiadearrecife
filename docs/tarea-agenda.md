# Tarea diaria de la agenda (automática, GitHub Actions)

Trabaja solo en la agenda: no toques `content/noticias`, `content/dias` ni `config.json`.
Escribe en español. Las reglas del portal están en `docs/tarea-diaria.md` (pasos 2, 3 y 4,
parte de Agenda) y `docs/linea-editorial.md`: léelas antes de empezar.

HOY = `TZ=Atlantic/Canary date +%F`.

1. **Fiestas.** Revisa la web completa https://fiestaslanzarote.com/ y añade en `content/agenda/`
   todas las fiestas patronales y populares, romerías, verbenas y sus actos principales de HOY
   en adelante que aún no estén, con `fecha` de inicio y `fecha_fin` reales.
2. **Resto de fuentes.** Repasa https://culturalanzarote.com/ (eventos y todas sus categorías),
   https://coolturalanzarote.com/ (eventos y artículos), https://cactlanzarote.com/en/events y
   las agendas de los siete ayuntamientos, por si falta algún acto del próximo mes o posterior.
   No dupliques actos que ya estén (mismo acto y fecha aunque el título cambie un poco). Si uno
   ha cambiado de fecha, hora o lugar, corrige su archivo.
3. **Fotos.** Para cada acto sin `imagen:`, busca la foto o cartel en su ficha oficial
   (organizador, Cultura Lanzarote, CACT, ayuntamiento, Cooltura, Fiestas Lanzarote o web de
   entradas; nunca de medios de comunicación). Primero ejecuta `python3 scripts/fotos_agenda.py`,
   que lo hace solo cuando la `fuente` es la ficha oficial. Para los que queden sin foto,
   descárgala a mano con `curl -sSL -o img/agenda/<nombre del .md sin .md>.<jpg|png|webp> "<url>"`,
   comprueba con `file` que es una imagen y con `stat` que pesa menos de 1,5 MB, y añade
   `imagen: img/agenda/...` y `credito: Foto: <fuente>`. Si no hay foto, no pongas el campo.
4. **Fechas.** Todo acto de varios días debe tener `fecha` = primer día y `fecha_fin` = último
   día. Corrige los que no.
5. **Comprobar.** `python3 scripts/validar.py` (0 errores) y `python3 build.py` (OK).
6. No hagas commit ni push. Al terminar, escribe un resumen: actos nuevos, fotos añadidas,
   fechas corregidas y fuentes que no se pudieron leer.
