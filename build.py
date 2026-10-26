#!/usr/bin/env python3
"""Generador de Guía de Arrecife (español + inglés).

Lee content/{noticias,dias,agenda,negocios}/*.md y escribe la web en _site/.
El español va en la raíz y el inglés en /en/. Solo usa la biblioteca estándar.

Campos en inglés: titulo_en, entradilla_en (noticias); el texto en inglés va
después de una línea "[en]" en el cuerpo. Agenda: titulo_en, descripcion_en,
precio_en, lugar_en, hora_en. Días: saludo_en, tema_en, nota_en.
Si falta la traducción, se usa el texto en español.

Uso:
  python3 build.py              # web de producción (URLs limpias)
  python3 build.py --preview    # enlaces explícitos a index.html (vista previa)
"""
import hashlib
import html
import json
import math
import random
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from iconos import ICONOS, ICONO_SECCION  # noqa: E402

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
OUT = ROOT / "_site"
SITE_URL = "https://guiadearrecife.es"
SITE_NAME = "Guía de Arrecife"
PREVIEW = "--preview" in sys.argv
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8")) if (ROOT / "config.json").exists() else {}
AUTO = CONFIG.get("modo") == "automatico"
LANGS = ["es", "en"]
LANG = ["es"]

MUNICIPIOS = ["Arrecife", "Haría", "San Bartolomé", "Teguise", "Tías",
              "Tinajo", "Yaiza", "La Graciosa", "Toda la isla"]
ORDEN_SECCIONES = ["Política", "Vivienda", "Empleo", "Economía", "Empresas", "Pymes y normativa",
                   "Ciberseguridad", "Servicios públicos", "Infraestructuras", "Movilidad",
                   "Medio ambiente", "Tiempo", "Cultura", "Deportes", "Redes", "Sucesos"]
COLOR_SECCION = {
    "Política": "#234a74", "Vivienda": "#b4532a", "Empleo": "#6d4a86", "Economía": "#a87d17",
    "Empresas": "#1f6b6b", "Pymes y normativa": "#3e5c3f", "Ciberseguridad": "#1c2533",
    "Servicios públicos": "#1d5c7a", "Infraestructuras": "#474d4a", "Movilidad": "#b85c2a",
    "Sucesos": "#8c2e21", "Redes": "#5b3f8f", "Medio ambiente": "#2f6b3a", "Cultura": "#86385f",
    "Deportes": "#2a6896", "Tiempo": "#2b7a8c",
}
SEC_EN = {"Política": "Politics", "Vivienda": "Housing", "Empleo": "Jobs", "Economía": "Economy",
          "Empresas": "Business", "Pymes y normativa": "SMEs & regulation", "Ciberseguridad": "Cybersecurity",
          "Servicios públicos": "Public services", "Infraestructuras": "Infrastructure",
          "Movilidad": "Getting around", "Medio ambiente": "Environment", "Cultura": "Culture",
          "Deportes": "Sport", "Tiempo": "Weather", "Redes": "Social media", "Sucesos": "Incidents"}
# Grupos del menú: las secciones de cada grupo comparten página ("Todo") y submenú.
GRUPOS = {
    "Sociedad": ["Vivienda", "Empleo", "Servicios públicos", "Sucesos", "Redes"],
    "Economía y empresas": ["Economía", "Empresas", "Pymes y normativa"],
    "Territorio": ["Infraestructuras", "Movilidad", "Medio ambiente", "Tiempo"],
    "Cultura y deporte": ["Cultura", "Deportes"],
}
GRUPO_DE = {s: g for g, hijas in GRUPOS.items() for s in hijas}
COLOR_SECCION.update({"Sociedad": "#b4532a", "Economía y empresas": "#1f6b6b",
                      "Territorio": "#474d4a", "Cultura y deporte": "#86385f"})
SEC_EN.update({"Sociedad": "Society", "Economía y empresas": "Economy & business",
               "Territorio": "Island & environment", "Cultura y deporte": "Culture & sport"})
MUNI_EN = {"Toda la isla": "Island-wide"}
CAT_EN = {"Patrimonio y naturaleza": "Heritage & nature", "Humor": "Comedy", "Danza": "Dance",
          "Charlas": "Talks", "Literatura": "Literature", "Música": "Music", "Teatro": "Theatre",
          "Fiestas": "Fiestas", "Deporte": "Sport", "Mercadillos": "Markets", "Cine": "Film",
          "Familiar": "Family", "Gastronomía": "Food & drink", "Actos": "Events",
          "Exposiciones": "Exhibitions", "Talleres": "Workshops", "Ferias": "Fairs"}
NIVEL_EN = {"Crítico": "Critical", "Alto": "High", "Medio": "Medium", "Bajo": "Low", "informativo": "Info"}

MESES = {"es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                "septiembre", "octubre", "noviembre", "diciembre"],
         "en": ["January", "February", "March", "April", "May", "June", "July", "August",
                "September", "October", "November", "December"]}
MESES_CORTOS = {"es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
                "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
DIAS = {"es": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
        "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}

UI = {
 "tagline": ("Lo que se cuece en Lanzarote y La Graciosa, contado cada mañana",
             "What's happening in Lanzarote and La Graciosa, every morning"),
 "agenda": ("Agenda", "What's on"), "negocios": ("Negocios de Arrecife", "Arrecife businesses"),
 "buscar": ("Buscar", "Search"), "portada": ("Portada", "Home"), "archivo": ("Archivo", "Archive"),
 "sobre": ("Sobre el portal", "About"), "skip": ("Saltar al contenido", "Skip to content"),
 "secciones": ("Secciones", "Sections"), "menu": ("Menú", "Menu"),
 "la_guia": ("La guía", "The guide"), "municipios": ("Municipios", "Areas"), "idioma": ("Idioma", "Language"), "otro_idioma": ("Read in English", "Leer en español"),
 "footer": ("Resúmenes propios de la actualidad de Lanzarote y La Graciosa, siempre con enlace al medio que dio la noticia. Para leer la información completa, visita la fuente original.",
            "Our own summaries of the news in Lanzarote and La Graciosa, always linking to the outlet that reported it. For the full story, visit the original source (in Spanish)."),
 "footer_ia": ("Los resúmenes y las traducciones se elaboran con ayuda de inteligencia artificial y la redacción los revisa antes de publicarlos.",
               "Summaries and translations are produced with the help of artificial intelligence and checked by our editors before publication."),
 "footer_ia_auto": ("Los resúmenes y las traducciones se elaboran automáticamente con inteligencia artificial a partir de los medios citados.",
                    "Summaries and translations are produced automatically with artificial intelligence from the outlets cited."),
 "nota_ia": ("Resumen elaborado automáticamente con inteligencia artificial.", "Summary produced automatically with artificial intelligence."),
 "hola": ("Buenos días, esto es lo que se cuece hoy en Lanzarote.", "Good morning, here's what's happening in Lanzarote today."),
 "las_hoy": ("Las {n} de hoy", "Today's top {n}"), "mas_hoy": ("Más noticias de hoy", "More news today"),
 "tema": ("El tema del día", "Today's big theme"),
 "ayer_t": ("Por si te lo perdiste", "In case you missed it"),
 "ed_t": ("Ediciones anteriores", "Previous editions"),
 "ed_s": ("Todas las noticias se quedan en el archivo para que puedas consultarlas cuando quieras", "Every story stays in the archive so you can look it up whenever you like"),
 "ed_all": ("Todo el archivo", "Full archive"),
 "dia_prev": ("Día anterior", "Previous day"), "dia_next": ("Día siguiente", "Next day"),
 "ed_dia": ("Edición del {d}", "Edition of {d}"),
 "ayer_s": ("Lo más importante de la edición de {d}", "The top stories from {d}"),
 "emp_t": ("Empresas y pymes", "Business & SMEs"),
 "emp_s": ("Lo que conviene saber si tienes un negocio en la isla", "What you need to know if you run a business on the island"),
 "ver_sec": ("Ver sección", "See section"),
 "red_t": ("Lo que se comenta en redes", "Trending on social media"),
 "red_s": ("Lo que se ha hecho viral en la isla, contado por los medios", "What's gone viral on the island, as reported by the media"),
 "cib_t": ("Ciberseguridad", "Cybersecurity"),
 "cib_s": ("Alertas y parches que afectan a empresas y administraciones de las islas", "Alerts and patches affecting businesses and public bodies in the islands"),
 "cib_all": ("Todas las alertas", "All alerts"), "nivel": ("Nivel {x}", "{x} level"), "que_hacer": ("Qué hacer", "What to do"),
 "ag_s": ("Qué hacer estos días en Arrecife y en toda la isla", "Things to do in Arrecife and around the island"),
 "ag_all": ("Toda la agenda", "Full listings"),
 "cal_add": ("Añadir al calendario", "Add to calendar"), "cal_google": ("Google Calendar", "Google Calendar"), "rango": ("Del {a} al {b}", "{a} – {b}"), "rango_mes": ("Del {a} al {b} de {m}", "{a}–{b} {m}"),
 "biz_k": ("Negocios de Arrecife", "Arrecife businesses"),
 "biz_h": ("Dónde comer, comprar y encontrar un profesional en la capital", "Where to eat, shop and find a professional in the capital"),
 "biz_p": ("Estamos preparando el directorio de comercios, bares, restaurantes y empresas de Arrecife. Aparecer será gratis.",
           "We're putting together a directory of Arrecife's shops, bars, restaurants and businesses. Listing will be free."),
 "biz_btn": ("Quiero aparecer", "Get listed"), "biz_btn2": ("Ver el directorio", "See the directory"),
 "munis_h": ("Noticias de hoy por municipio", "Today's news by area"),
 "noticia_n": ("Noticia {o} de {n}", "Story {o} of {n}"),
 "byline": ("Resumen de Guía de Arrecife", "Summary by Guía de Arrecife"),
 "fuentes": ("Fuentes", "Sources"),
 "fuentes_nota": ("Este texto es un resumen propio. La información completa está en los medios enlazados.",
                  "This is our own summary. The full story is in the linked outlets, which publish in Spanish."),
 "wa": ("Compartir por WhatsApp", "Share on WhatsApp"), "copiar": ("Copiar enlace", "Copy link"),
 "copiado": ("Enlace copiado", "Link copied"), "sigue": ("Sigue leyendo", "Keep reading"),
 "mas_emp": ("Más de empresas y pymes", "More business news"), "mas_cib": ("Más de ciberseguridad", "More cybersecurity"),
 "mas_red": ("Más de lo que se comenta", "More trending stories"),
 "ruta": ("Ruta", "Breadcrumb"),
 "sec_eb": ("Sección", "Section"), "todo": ("Todo", "All"), "muni_eb": ("Municipio", "Area"), "dia_eb": ("Edición del día", "Daily edition"),
 "vacio": ("Todavía no hay noticias aquí.", "No stories here yet."),
 "muni_intro": ("Noticias de {m}.", "News from {m}."),
 "toda_intro": ("Noticias que afectan a toda Lanzarote y La Graciosa.", "News affecting the whole of Lanzarote and La Graciosa."),
 "hemeroteca": ("Hemeroteca", "Back issues"),
 "arch_intro": ("Todas las ediciones diarias, de la más reciente a la más antigua.", "Every daily edition, newest first."),
 "n_noticias": ("{n} noticias", "{n} stories"),
 "bus_h": ("Busca en todas las noticias", "Search all stories"),
 "bus_label": ("Palabras a buscar", "Search terms"),
 "bus_ph": ("Por ejemplo: vivienda, Teguise, guaguas", "For example: housing, Teguise, buses"),
 "bus_1": (" noticia encontrada", " story found"), "bus_n": (" noticias encontradas", " stories found"),
 "bus_last": ("Últimas {n} noticias", "Latest {n} stories"),
 "ag_eb": ("Qué hacer en Lanzarote y La Graciosa", "Things to do in Lanzarote and La Graciosa"),
 "ag_intro": ("Conciertos, charlas, teatro, fiestas, deporte y mercadillos en Arrecife y en toda la isla. Comprueba siempre horarios y entradas en la fuente antes de ir.",
              "Concerts, talks, theatre, fiestas, sport and markets in Arrecife and around the island. Always check times and tickets with the source before you go."),
 "ag_filtro": ("Filtrar por municipio", "Filter by area"), "ag_todas": ("Todos", "All"),
 "ag_vacio": ("No hay actos apuntados para los próximos días. Si organizas algo, escríbenos y lo añadimos.",
              "Nothing listed for the coming days yet. If you're organising something, get in touch and we'll add it."),
 "ag_none": ("No hay actos en este municipio en los próximos días.", "Nothing listed in this area for the coming days."),
 "fuente": ("Fuente", "Source"),
 "dir_eb": ("Directorio", "Directory"),
 "dir_intro": ("De Valterra a La Vega y de Titerroy al Charco de San Ginés: dónde comer, comprar y encontrar un profesional en la capital.",
               "From Valterra to La Vega and from Titerroy to the Charco de San Ginés: where to eat, shop and find a professional in the capital."),
 "dir_empty_h": ("El directorio abre muy pronto", "The directory opens soon"),
 "dir_empty_p": ("Estamos preparando la guía de comercios, bares, restaurantes y empresas de Arrecife, ordenada por barrios y por actividad. Aparecer en ella será gratis.",
                 "We're building a guide to Arrecife's shops, bars, restaurants and businesses, organised by neighbourhood and type. Listing will be free."),
 "dir_cta": ("¿Tienes un negocio en Arrecife? Escríbenos con el nombre, la dirección, un teléfono y una frase sobre lo que haces, y te damos de alta.",
             "Do you run a business in Arrecife? Send us its name, address, a phone number and a line about what you do, and we'll add you."),
 "destacado": ("Destacado", "Featured"),
 "dir_cats": (["Restauración", "Comercio", "Salud y bienestar", "Servicios profesionales", "Tecnología e informática", "Hogar y reformas", "Ocio y cultura", "Motor"],
              ["Restaurants & bars", "Shops", "Health & wellbeing", "Professional services", "Tech & IT", "Home & repairs", "Leisure & culture", "Motoring"]),
 "linea": ("Línea editorial", "Editorial policy"),
 "linea_h": ("Nuestra línea editorial", "Our editorial policy"),
 "linea_intro": ("Qué contamos, cómo lo contamos y desde qué valores.", "What we cover, how we cover it and the values behind it."),
 "sobre_eb": ("Sobre el portal", "About"), "sobre_h": ("Qué es Guía de Arrecife", "What is Guía de Arrecife"),
}
SOBRE = {
 "es": """<p>Guía de Arrecife es un resumen diario de la actualidad de Lanzarote y La Graciosa. Cada mañana revisamos lo que publican los medios digitales de la isla y las notas de prensa del Cabildo y de los siete ayuntamientos, y elegimos las noticias que más importan a quien vive y trabaja aquí: política insular y municipal, vivienda, empleo, servicios públicos, tráfico, turismo, medio ambiente y sucesos relevantes. Además, recogemos lo que interesa a las empresas y pymes, con las novedades de la Cámara de Comercio y de las asociaciones empresariales de la isla, las alertas de ciberseguridad, lo que se comenta en redes y la agenda de actos de toda la isla.</p>
<p>En el bloque de redes solo incluimos temas virales que ya haya contado algún medio. No publicamos rumores ni contenidos que expongan a particulares.</p>
<p>Cada noticia se cuenta con palabras propias, en pocas líneas, y siempre enlaza a los medios que la publicaron. No copiamos textos ni fotografías: las ilustraciones de portada son propias. Si quieres la información completa, el sitio para leerla es la fuente original.</p>
<h2>En dos idiomas</h2><p>Toda la información está en español y en inglés, para que también puedan seguirla los residentes y visitantes que no hablan español.</p>
<h2>Nuestra línea editorial</h2><p>Somos independientes de cualquier partido, pero no neutrales en valores: defendemos los derechos humanos, la paz y a las personas que más lo necesitan. Lo explicamos en nuestra <a href="../linea-editorial/">línea editorial</a>.</p>
<h2>Cómo se elabora</h2>
<p>La selección, la redacción y la traducción de los resúmenes se hacen con ayuda de inteligencia artificial y siguiendo siempre los mismos criterios: nada de contenido patrocinado ni rumores, una sola entrada cuando varios medios cuentan lo mismo, y aviso expreso cuando un dato no está confirmado.</p>
<h2>Correcciones</h2>
<p>Si ves un error en un resumen o eres el medio citado y quieres que cambiemos algo, escríbenos y lo revisaremos lo antes posible.</p>""",
 "en": """<p>Guía de Arrecife is a daily round-up of the news in Lanzarote and La Graciosa. Every morning we go through what the island's online media publish, plus press releases from the Cabildo and the seven town councils, and pick the stories that matter most to people who live and work here: island and local politics, housing, jobs, public services, traffic, tourism, the environment and significant incidents. We also cover what matters to businesses and SMEs, including news from the Chamber of Commerce and the island's business associations, cybersecurity alerts, what's trending on social media, and what's on across the island.</p>
<p>In the social media section we only include viral stories that a news outlet has already reported. We don't publish rumours or content that exposes private individuals.</p>
<p>Each story is told in our own words, in a few lines, and always links to the outlets that published it. We don't copy text or photos: the cover illustrations are our own. For the full story, the place to read it is the original source, which is usually in Spanish.</p>
<h2>In two languages</h2><p>Everything is published in Spanish and English, so residents and visitors who don't speak Spanish can follow island news too.</p>
<h2>Our editorial policy</h2><p>We are independent of any party, but not neutral about values: we stand for human rights, peace and the people who need it most. We explain this in our <a href="../editorial-policy/">editorial policy</a>.</p>
<h2>How it's made</h2>
<p>Stories are selected, written and translated with the help of artificial intelligence, always following the same rules: no sponsored content or rumours, one entry when several outlets report the same thing, and a clear note when a fact hasn't been confirmed.</p>
<h2>Corrections</h2>
<p>If you spot a mistake in a summary, or you're the outlet we cite and want something changed, get in touch and we'll look at it as soon as possible.</p>""",
}
LINEA = {
 "es": """<p>Guía de Arrecife no es neutral en valores, y preferimos decirlo claro. Somos independientes de cualquier partido, empresa o institución, pero tenemos una forma de mirar la actualidad que guía qué noticias elegimos, en qué orden las ponemos y con qué palabras las contamos.</p>
<h2>Nuestros valores</h2>
<ol>
<li><strong>Los derechos humanos, por encima de todo.</strong> La dignidad de cada persona no se negocia, venga de donde venga. Ante cualquier noticia, nos preguntamos a quién afecta y cómo.</li>
<li><strong>La paz frente a la guerra.</strong> No hacemos propaganda bélica ni presentamos la violencia como solución. Cuando hablamos de conflictos, ponemos el foco en las personas que los sufren.</li>
<li><strong>Del lado de quien más lo necesita.</strong> Damos prioridad a lo que afecta a las personas con menos recursos: vivienda, empleo digno, pobreza, dependencia, sanidad y educación públicas, servicios sociales.</li>
<li><strong>Igualdad y diversidad.</strong> Defendemos la igualdad entre mujeres y hombres, los derechos LGTBI y la inclusión de las personas con discapacidad. La violencia machista es violencia machista, no un "suceso familiar".</li>
<li><strong>Las personas migrantes son personas.</strong> Hablamos de personas migrantes, nunca de "ilegales" ni de "avalanchas". Contamos los datos sin alarmismo y recordamos que detrás de cada cifra hay una vida.</li>
<li><strong>Una isla que se cuida.</strong> El territorio, el agua, el paisaje y el legado de César Manrique son patrimonio de todos. Seguimos de cerca cualquier decisión que los afecte.</li>
</ol>
<h2>Cómo trabajamos</h2>
<ul>
<li><strong>Servicio antes que espectáculo.</strong> Cada noticia responde a "¿y a mí qué?": plazos, requisitos, cortes, ayudas, qué hacer.</li>
<li><strong>Arrecife primero, la isla después.</strong> A igual importancia, gana lo que pasa en la capital.</li>
<li><strong>Independientes de partidos.</strong> Contamos lo que proponen y lo que hacen todas las fuerzas políticas, con el mismo rigor, y no pedimos el voto para nadie. Nuestros valores no son de ningún partido.</li>
<li><strong>Para quien tiene un negocio.</strong> Seguimos lo que importa a autónomos y pymes: normativa, ayudas, ciberseguridad y la voz de las asociaciones empresariales. Creemos en una economía que cree empleo digno en la isla.</li>
<li><strong>Sucesos con respeto.</strong> Solo los que afectan a la gente. Sin morbo, sin nombres de víctimas ni de menores y con presunción de inocencia.</li>
<li><strong>Los hechos son sagrados.</strong> Nuestros valores deciden qué contamos y cómo lo enfocamos, nunca cambian los datos. No inventamos, no exageramos y decimos claramente lo que no está confirmado.</li>
<li><strong>Siempre con la fuente.</strong> Cada resumen enlaza al medio que publicó la noticia. Si nos equivocamos, lo corregimos y lo decimos.</li>
</ul>""",
 "en": """<p>Guía de Arrecife is not neutral about values, and we'd rather say so openly. We are independent of any party, company or institution, but we have a way of looking at the news that guides which stories we choose, how we order them and the words we use.</p>
<h2>Our values</h2>
<ol>
<li><strong>Human rights above everything.</strong> Every person's dignity is non-negotiable, wherever they come from. With every story, we ask who it affects and how.</li>
<li><strong>Peace, not war.</strong> We don't spread war propaganda or present violence as a solution. When we cover conflict, we focus on the people who suffer it.</li>
<li><strong>On the side of those who need it most.</strong> We prioritise what affects people with fewer resources: housing, decent jobs, poverty, care for dependent people, public health and education, and social services.</li>
<li><strong>Equality and diversity.</strong> We stand for equality between women and men, LGBTI rights and the inclusion of disabled people. Gender-based violence is gender-based violence, not a "domestic incident".</li>
<li><strong>Migrants are people.</strong> We talk about migrants, never "illegals" or "floods". We report the figures without alarmism and remember that behind every number is a life.</li>
<li><strong>An island worth looking after.</strong> The land, water, landscape and César Manrique's legacy belong to everyone. We closely follow any decision that affects them.</li>
</ol>
<h2>How we work</h2>
<ul>
<li><strong>Service before spectacle.</strong> Every story answers "what does this mean for me?": deadlines, requirements, closures, grants, what to do.</li>
<li><strong>Arrecife first, then the island.</strong> When two stories matter equally, the capital comes first.</li>
<li><strong>Independent of parties.</strong> We report what every political group proposes and does with the same rigour, and we never tell anyone how to vote. Our values don't belong to any party.</li>
<li><strong>For people who run a business.</strong> We follow what matters to the self-employed and SMEs: regulation, grants, cybersecurity and the voice of business associations. We believe in an economy that creates decent jobs on the island.</li>
<li><strong>Incidents with respect.</strong> Only those that affect people. No sensationalism, no names of victims or minors, and the presumption of innocence always applies.</li>
<li><strong>Facts are sacred.</strong> Our values decide what we cover and how we frame it, never the facts themselves. We don't make things up, we don't exaggerate, and we say clearly when something isn't confirmed.</li>
<li><strong>Always with the source.</strong> Every summary links to the outlet that published the story. If we get something wrong, we correct it and say so.</li>
</ul>""",
}
SECCIONES_NAV = []  # entradas del menú: secciones sueltas y grupos
SECCIONES = []      # todas las secciones con noticias (cada una tiene su página)
HOY = [None]


# ---------------------------------------------------------------- idioma
def en():
    return LANG[0] == "en"


def t(key, **kw):
    v = UI[key][1 if en() else 0]
    return v.format(**kw) if kw and isinstance(v, str) else v


def F(obj, key):
    """Campo traducido si existe."""
    if en() and obj.get(key + "_en"):
        return obj[key + "_en"]
    return obj.get(key, "")


def sec_name(s): return SEC_EN.get(s, s) if en() else s
def muni_name(m): return MUNI_EN.get(m, m) if en() else m
def cat_name(c): return CAT_EN.get(c, c) if en() else c
def nivel_name(x): return NIVEL_EN.get(x, x) if en() else x


def fecha_larga(d):
    if en():
        return f"{DIAS['en'][d.weekday()]} {d.day} {MESES['en'][d.month - 1]} {d.year}"
    return f"{DIAS['es'][d.weekday()].capitalize()} {d.day} de {MESES['es'][d.month - 1]} de {d.year}"


def fecha_corta(d):
    return f"{d.day} {MESES['en'][d.month - 1]}" if en() else f"{d.day} de {MESES['es'][d.month - 1]}"


# ---------------------------------------------------------------- utilidades
def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def esc(s):
    return html.escape(str(s), quote=True)


def inline_md(text):
    t_ = esc(text)
    t_ = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t_)
    return re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener" target="_blank">\1</a>', t_)


def parse_file(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.S)
    if not m:
        raise SystemExit(f"Falta la cabecera --- en {path}")
    meta, body, key = {}, m.group(2).strip(), None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        if line.startswith("- ") and key:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(line[2:].strip())
            continue
        k, _, v = line.partition(":")
        key, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1].replace('\\"', '"')
        meta[key] = v if v else []
    return meta, body


def pct(s):
    return "".join(c if re.match(r"[A-Za-z0-9\-_.~]", c) else "".join("%%%02X" % b for b in c.encode()) for c in s)


def paras(text):
    return [x.strip() for x in re.split(r"\n\s*\n", text) if x.strip()]


# ---------------------------------------------------------------- portadas generadas
def cover_svg(seed_text, color, icono):
    """Portada propia: color de la sección, curvas de nivel suaves y un pictograma del tema."""
    rnd = random.Random(int(hashlib.md5(seed_text.encode()).hexdigest(), 16))
    W, H = 1200, 675
    cx, cy = 600, 300
    p = [rnd.uniform(0, 6.28) for _ in range(3)]
    a = [rnd.uniform(0.05, 0.12), rnd.uniform(0.03, 0.08), rnd.uniform(0.02, 0.05)]
    rings = []
    for k in range(4, 17):
        r0 = 38 * k
        pts = []
        for i in range(72):
            th = i / 72 * math.tau
            r = r0 * (1 + a[0] * math.sin(2 * th + p[0] + k * .05) + a[1] * math.sin(3 * th + p[1])
                      + a[2] * math.sin(5 * th + p[2] - k * .08))
            pts.append(f"{cx + r * math.cos(th) * 1.4:.0f},{cy + r * math.sin(th):.0f}")
        rings.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="#fff" stroke-opacity="{0.05 + 0.07 * (1 - k / 17):.2f}" stroke-width="1.4"/>')
    glyph = ICONOS.get(icono) or ICONOS["edificio"]
    s = 5.4  # 64 * 5.4 = 345 px
    icon = (f'<circle cx="{cx}" cy="{cy}" r="225" fill="#fff" fill-opacity=".09"/>'
            f'<circle cx="{cx}" cy="{cy}" r="225" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="2"/>'
            f'<g transform="translate({cx - 32 * s:.1f} {cy - 32 * s:.1f}) scale({s})" fill="none" stroke="#fff" '
            f'stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">{glyph}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{color}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity=".8"/></linearGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="#111"/><rect width="{W}" height="{H}" fill="url(#g)"/>'
            f'{"".join(rings)}{icon}</svg>')


# ---------------------------------------------------------------- contenido
def load():
    noticias = []
    for p in sorted((CONTENT / "noticias").glob("*.md")):
        meta, body = parse_file(p)
        try:
            f = date.fromisoformat(meta["fecha"])
        except (KeyError, ValueError):
            raise SystemExit(f"Fecha no válida en {p.name}")
        fuentes = []
        for line in meta.get("fuentes", []):
            nombre, _, url = line.partition("|")
            fuentes.append({"nombre": nombre.strip(), "url": url.strip()})
        es_body, _, en_body = body.partition("\n[en]\n")
        munis = [x.strip() for x in str(meta.get("municipios", "Toda la isla")).split(",") if x.strip()]
        noticias.append({
            "slug": p.stem, "titulo": meta["titulo"], "titulo_en": meta.get("titulo_en", ""), "fecha": f,
            "orden": int(meta.get("orden", 99)), "bloque": meta.get("bloque", "diez"),
            "seccion": meta.get("seccion", "Actualidad"), "municipios": munis,
            "entradilla": meta.get("entradilla", ""), "entradilla_en": meta.get("entradilla_en", ""),
            "nivel": meta.get("nivel", ""), "icono": meta.get("icono", ""), "imagen": meta.get("imagen", ""), "credito": meta.get("credito", ""),
            "actualizado": meta.get("actualizado", ""),
            "fuentes": fuentes, "parrafos": paras(es_body), "parrafos_en": paras(en_body),
        })
    noticias.sort(key=lambda n: (-n["fecha"].toordinal(), n["orden"]))

    dias = {}
    for p in sorted((CONTENT / "dias").glob("*.md")):
        meta, _ = parse_file(p)
        dias[date.fromisoformat(meta["fecha"])] = meta

    agenda = []
    for p in sorted((CONTENT / "agenda").glob("*.md")):
        meta, _ = parse_file(p)
        ini = date.fromisoformat(meta["fecha"])
        fin = date.fromisoformat(meta["fecha_fin"]) if meta.get("fecha_fin") else ini
        nombre, _, url = str(meta.get("fuente", "")).partition("|")
        agenda.append({**meta, "slug": p.stem, "ini": ini, "fin": fin,
                       "fuente_nombre": nombre.strip(), "fuente_url": url.strip()})
    agenda.sort(key=lambda e: (e["ini"], e.get("hora", "")))

    negocios = []
    for p in sorted((CONTENT / "negocios").glob("*.md")):
        meta, body = parse_file(p)
        negocios.append({**meta, "slug": p.stem, "texto": body})
    negocios.sort(key=lambda b: b.get("nombre", "").lower())
    return noticias, dias, agenda, negocios


# ---------------------------------------------------------------- rutas
ROUTES = {
    "es": {"home": "", "noticia": "noticias/{}/", "seccion": "seccion/{}/", "municipio": "municipio/{}/",
           "dia": "archivo/{}/", "archivo": "archivo/", "agenda": "agenda/", "negocios": "negocios/",
           "buscar": "buscar/", "sobre": "sobre/", "linea": "linea-editorial/"},
    "en": {"home": "en/", "noticia": "en/news/{}/", "seccion": "en/section/{}/", "municipio": "en/area/{}/",
           "dia": "en/archive/{}/", "archivo": "en/archive/", "agenda": "en/whats-on/", "negocios": "en/businesses/",
           "buscar": "en/search/", "sobre": "en/about/", "linea": "en/editorial-policy/"},
}


def R(kind, arg=None, lang=None):
    lang = lang or LANG[0]
    if kind == "seccion" and lang == "en":
        arg = slugify(SEC_EN.get(arg, arg))
    elif kind == "seccion":
        arg = slugify(arg)
    elif kind == "municipio":
        arg = slugify(MUNI_EN.get(arg, arg) if lang == "en" else arg)
    elif kind == "dia":
        arg = arg.isoformat()
    elif kind == "noticia":
        arg = arg["slug"]
    return ROUTES[lang][kind].format(arg) if arg is not None else ROUTES[lang][kind]


def depth_of(path):
    return path.count("/")


class Linker:
    def __init__(self, path):
        self.prefix = "../" * depth_of(path)

    def __call__(self, d=""):
        if PREVIEW:
            return self.prefix + d + "index.html"
        return (self.prefix + d) or "./"

    def file(self, f):
        return self.prefix + f


def cover_src(n, L):
    return L.file(n["imagen"]) if n["imagen"] else L.file(f"img/portadas/{n['slug']}.svg")


# ---------------------------------------------------------------- plantilla
CSS = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
# Fuentes alojadas en la propia web (assets/fonts): más rápido y sin pedir nada a Google.
FONTS_CSS = (ROOT / "assets" / "fonts" / "fonts.css").read_text(encoding="utf-8")
FONTS_PRELOAD = ["archivo-normal-400-900-latin.woff2", "source-serif-4-normal-400-700-latin.woff2"]


# ---------------------------------------------------------------- SEO: imágenes, logo y datos estructurados
PNG = set()          # portadas que tienen versión PNG (slug)
LOGO_PNG = [False]   # True si se ha podido generar img/logo-512.png
SITEMAP = []         # (path, alt, lastmod) de cada página publicada


def rasterize(svg_path, png_path, w, h):
    """Convierte un SVG en PNG con rsvg-convert (o ImageMagick). Devuelve False si no hay herramienta."""
    cmds = (["rsvg-convert", "-w", str(w), "-h", str(h), "-o", str(png_path), str(svg_path)],
            ["convert", "-background", "none", "-density", "192", str(svg_path), "-resize", f"{w}x{h}!", str(png_path)])
    for cmd in cmds:
        if shutil.which(cmd[0]):
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode == 0 and png_path.exists() and png_path.stat().st_size:
                return True
    return False


def logo_svg():
    """Logo cuadrado: verde de carpintería, aro claro y el velero de los pictogramas."""
    s = 5.4
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
            '<rect width="512" height="512" rx="96" fill="#17633f"/>'
            '<circle cx="256" cy="256" r="196" fill="#fff" fill-opacity=".1" stroke="#fff" stroke-opacity=".35" stroke-width="6"/>'
            f'<g transform="translate({256 - 32 * s:.1f} {256 - 32 * s:.1f}) scale({s})" fill="none" stroke="#fff" '
            f'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{ICONOS["velero"]}</g></svg>')


def abs_url(rel):
    return f"{SITE_URL}/{rel}"


def news_image(n):
    """URL absoluta de la imagen de una noticia para Google y redes, y su tamaño si se conoce."""
    if n["imagen"]:
        return abs_url(n["imagen"]), None
    if n["slug"] in PNG:
        return abs_url(f"img/portadas/{n['slug']}.png"), (1200, 675)
    return None, None


def pub_dt(d):
    """Hora de publicación de la edición (7:00 en Canarias, que en invierno es UTC)."""
    return datetime(d.year, d.month, d.day, 7, 0, tzinfo=timezone.utc)


def mod_date(n):
    return n["actualizado"] or pub_dt(n["fecha"]).isoformat()


def org_ld():
    org = {"@type": "NewsMediaOrganization", "@id": f"{SITE_URL}/#org", "name": SITE_NAME, "url": f"{SITE_URL}/",
           "publishingPrinciples": abs_url(R("linea", lang="es")), "areaServed": "Lanzarote y La Graciosa"}
    if LOGO_PNG[0]:
        org["logo"] = {"@type": "ImageObject", "url": abs_url("img/logo-512.png"), "width": 512, "height": 512}
    return org


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": name, "item": abs_url(path)}
        for i, (name, path) in enumerate(items)]}


def ld_tag(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def sec_crumbs(s):
    """Portada › Grupo › Sección (el grupo solo si la sección pertenece a uno)."""
    out = [(t("portada"), R("home"))]
    if GRUPO_DE.get(s):
        out.append((sec_name(GRUPO_DE[s]), R("seccion", GRUPO_DE[s])))
    out.append((sec_name(s), R("seccion", s)))
    return out


def page(*, title, path, alt, body, description="", og_type="website", extra_head="", fragment=False,
         image=None, image_size=None, crumbs=None, lastmod=None):
    """path: ruta de esta página; alt: ruta equivalente en el otro idioma.
    image: URL absoluta de la imagen para Google y redes; crumbs: [(nombre, ruta)] para la ruta de navegación."""
    L = Linker(path)
    lang = LANG[0]
    other = "es" if en() else "en"
    full_title = f"{title} · {SITE_NAME}" if title != SITE_NAME else SITE_NAME
    canonical = SITE_URL + "/" + path
    nav = "".join(f'<a href="{L(R("seccion", s))}">{esc(sec_name(s))}</a>' for s in SECCIONES_NAV)
    fecha_top = esc(fecha_larga(HOY[0])) if HOY[0] else ""
    es_path, en_path = (alt, path) if en() else (path, alt)
    if path != "404.html" and not PREVIEW:
        SITEMAP.append((path, alt, lastmod))
    if not image and LOGO_PNG[0]:
        image, image_size = abs_url("img/logo-512.png"), (512, 512)
    grande = image and image_size != (512, 512)
    og_img = ""
    if image:
        og_img = f'<meta property="og:image" content="{esc(image)}"><meta name="twitter:image" content="{esc(image)}">'
        if image_size:
            og_img += f'<meta property="og:image:width" content="{image_size[0]}"><meta property="og:image:height" content="{image_size[1]}">'
    if crumbs is None:
        crumbs = [] if path in (R("home"), "404.html") else [(t("portada"), R("home")), (title, path)]
    crumbs_tag = ld_tag(crumbs_ld(crumbs)) if len(crumbs) > 1 else ""
    font_dir = L.file("assets/fonts/")
    fonts = "".join(f'<link rel="preload" href="{font_dir}{f}" as="font" type="font/woff2" crossorigin>' for f in FONTS_PRELOAD)
    head = (
        f"<title>{esc(full_title)}</title>"
        '<meta name="claude:viewport-fit-sides" content="cover">'
        f'<meta name="description" content="{esc(description or t("tagline"))}">'
        f'<link rel="canonical" href="{esc(canonical)}">'
        f'<link rel="alternate" hreflang="es" href="{SITE_URL}/{es_path}">'
        f'<link rel="alternate" hreflang="en" href="{SITE_URL}/{en_path}">'
        f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/{es_path}">'
        f'<meta property="og:site_name" content="{SITE_NAME}">'
        f'<meta property="og:title" content="{esc(title)}">'
        f'<meta property="og:description" content="{esc(description or t("tagline"))}">'
        f'<meta property="og:type" content="{og_type}"><meta property="og:url" content="{esc(canonical)}">'
        f'<meta property="og:locale" content="{"en_GB" if en() else "es_ES"}">'
        f'<meta name="twitter:card" content="{"summary_large_image" if grande else "summary"}">{og_img}'
        '<meta name="robots" content="max-image-preview:large">'
        f'<link rel="icon" href="{L.file("img/logo.svg")}" type="image/svg+xml">'
        + (f'<link rel="apple-touch-icon" href="{L.file("img/apple-touch-icon.png")}">' if LOGO_PNG[0] else "") +
        f'<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{SITE_URL}/{"en/" if en() else ""}feed.xml">'
        f"{fonts}<style>{FONTS_CSS.replace('{FONTS}', font_dir)}{CSS}</style>{crumbs_tag}{extra_head}"
    )
    munis_nav = "".join(f'<a href="{L(R("municipio", m))}">{esc(muni_name(m))}</a>' for m in MUNICIPIOS)
    lang_switch = (f'<span class="lang" role="group" aria-label="Idioma / Language">'
                   f'<a href="{L(es_path)}" lang="es" hreflang="es"{" aria-current=true" if not en() else ""}>ES</a>'
                   f'<a href="{L(en_path)}" lang="en" hreflang="en"{" aria-current=true" if en() else ""}>EN</a></span>')
    shell = f"""
<a class="skip" href="#contenido">{t('skip')}</a>
<header class="masthead">
  <div class="topbar"><div class="wrap topbar-inner">
    <span class="topbar-date">{fecha_top}</span>
    <span class="topbar-links"><a href="{L(R('agenda'))}">{t('agenda')}</a><a class="hide-sm" href="{L(R('negocios'))}">{t('negocios')}</a><a href="{L(R('buscar'))}">{t('buscar')}</a>{lang_switch}</span>
  </div></div>
  <div class="wrap brandrow">
    <a class="brand" href="{L(R('home'))}"><span class="brand-name">Guía de <em>Arrecife</em></span></a>
    <p class="brand-tag">{esc(t('tagline'))}</p>
    <div class="m-tools">
      <a class="m-search" href="{L(R('buscar'))}" aria-label="{t('buscar')}"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg></a>
      <details class="mnav">
        <summary aria-label="{t('menu')}"><span class="burger" aria-hidden="true"><i></i><i></i><i></i></span><span class="m-label">{t('menu')}</span></summary>
        <div class="mnav-panel">
          <div class="mnav-group mnav-guide">
            <p class="mnav-title">{t('la_guia')}</p>
            <a href="{L(R('home'))}">{t('portada')}</a>
            <a href="{L(R('agenda'))}">{t('agenda')}</a>
            <a href="{L(R('negocios'))}">{t('negocios')}</a>
            <a href="{L(R('archivo'))}">{t('archivo')}</a>
            <a href="{L(R('buscar'))}">{t('buscar')}</a>
          </div>
          <div class="mnav-group">
            <p class="mnav-title">{t('secciones')}</p>
            <div class="mnav-grid">{nav}</div>
          </div>
          <div class="mnav-group">
            <p class="mnav-title">{t('municipios')}</p>
            <div class="mnav-chips">{munis_nav}</div>
          </div>
          <div class="mnav-group mnav-lang">
            <p class="mnav-title">{t('idioma')}</p>
            <a href="{L(es_path)}" lang="es" hreflang="es"{" aria-current=true" if not en() else ""}>Español</a>
            <a href="{L(en_path)}" lang="en" hreflang="en"{" aria-current=true" if en() else ""}>English</a>
          </div>
        </div>
      </details>
    </div>
  </div>
  <nav class="navband" aria-label="{t('secciones')}"><div class="wrap navband-inner">
    <a class="nav-home" href="{L(R('home'))}">{t('portada')}</a>
    <a class="nav-key" href="{L(R('agenda'))}">{t('agenda')}</a>
    {nav}
    <a href="{L(R('archivo'))}">{t('archivo')}</a>
  </div></nav>
</header>
<main id="contenido">{body}</main>
<script>
(function(){{var d=document.querySelector('.mnav');if(!d)return;
d.addEventListener('toggle',function(){{var h=document.querySelector('.masthead');if(h)document.documentElement.style.setProperty('--mh',h.getBoundingClientRect().bottom+'px');document.documentElement.classList.toggle('menu-open',d.open);}});
document.addEventListener('keydown',function(e){{if(e.key==='Escape'&&d.open){{d.open=false;}}}});
d.querySelectorAll('.mnav-panel a').forEach(function(a){{a.addEventListener('click',function(){{d.open=false;}});}});}})();
</script>
<footer class="footer">
  <div class="wrap footer-inner">
    <div>
      <p class="footer-brand">Guía de <em>Arrecife</em></p>
      <p>{t('footer')}</p>
      <p class="footer-ia">{t('footer_ia_auto') if AUTO else t('footer_ia')} <a href="{L(R('sobre'))}">{t('sobre')}</a></p>
      <p><a href="{L(alt)}" hreflang="{other}">{t('otro_idioma')}</a></p>
    </div>
    <ul class="footer-links">
      <li><a href="{L(R('agenda'))}">{t('agenda')}</a></li>
      <li><a href="{L(R('negocios'))}">{t('negocios')}</a></li>
      <li><a href="{L(R('archivo'))}">{t('archivo')}</a></li>
      <li><a href="{L(R('sobre'))}">{t('sobre')}</a></li>
      <li><a href="{L(R('linea'))}">{t('linea')}</a></li>
      <li><a href="{SITE_URL}/{'en/' if en() else ''}feed.xml">RSS</a></li>
    </ul>
  </div>
</footer>"""
    if fragment:
        return head + shell
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f"{head}</head><body>{shell}</body></html>")


# ---------------------------------------------------------------- piezas
def sec_chip(n, L):
    return f'<a class="kicker" href="{L(R("seccion", n["seccion"]))}">{esc(sec_name(n["seccion"]))}</a>'


def muni_text(n):
    return " · ".join(muni_name(m) for m in n["municipios"])


def figure(n, L, cls=""):
    label = esc(muni_name(n["municipios"][0])) if n["municipios"] else ""
    return (f'<a class="fig {cls}" href="{L(R("noticia", n))}" tabindex="-1" aria-hidden="true">'
            f'<img src="{cover_src(n, L)}" alt="" loading="lazy"><span class="fig-place">{label}</span></a>')


def story_card(n, L, variant="card", lede=True):
    rank = f'<span class="num">{n["orden"]:02d}</span>' if n["bloque"] == "diez" else ""
    lede_html = f'<p class="lede">{esc(F(n, "entradilla"))}</p>' if lede else ""
    return (f'<article class="{variant}">{figure(n, L)}<div class="txt">'
            f'<div class="meta-row">{rank}{sec_chip(n, L)}</div>'
            f'<h3><a href="{L(R("noticia", n))}">{esc(F(n, "titulo"))}</a></h3>{lede_html}</div></article>')


def date_block(d, fin=None):
    lg = "en" if en() else "es"
    hasta = (f'<span class="dblock-fin">→ {fin.day} {MESES_CORTOS[lg][fin.month - 1]}</span>' if fin and fin != d else "")
    return (f'<span class="dblock"><span class="dblock-wd">{DIAS[lg][d.weekday()][:3]}</span>'
            f'<span class="dblock-d">{d.day}</span><span class="dblock-m">{MESES_CORTOS[lg][d.month - 1]}</span>{hasta}</span>')


def ev_rango(e):
    a, b = e["ini"], e["fin"]
    if a.month == b.month and a.year == b.year:
        return t("rango_mes", a=a.day, b=b.day, m=MESES["en" if en() else "es"][a.month - 1])
    return t("rango", a=fecha_corta(a), b=fecha_corta(b))


def ev_when(e):
    return ev_rango(e) if e["fin"] != e["ini"] else F(e, "hora")


def ev_card(e, hoy):
    return (f'<article class="evcard">{date_block(e["ini"], e["fin"])}<div class="evcard-txt">'
            f'<p class="evcard-cat">{esc(cat_name(e.get("categoria", "Actos")))} · {esc(ev_when(e))}</p>'
            f'<h3>{esc(F(e, "titulo"))}</h3><p class="evcard-place">{esc(F(e, "lugar"))}, {esc(muni_name(e.get("municipio", "")))}</p>'
            f'</div></article>')


def ev_horario(e):
    """(inicio, fin) en UTC si la hora es concreta (dos horas por defecto); None si es de día completo."""
    m = re.match(r"\s*(\d{1,2})[:.](\d{2})", str(e.get("hora", "")))
    if not m or e["fin"] != e["ini"]:
        return None
    ini = datetime(e["ini"].year, e["ini"].month, e["ini"].day, int(m[1]), int(m[2]), tzinfo=ZoneInfo("Atlantic/Canary"))
    return ini.astimezone(timezone.utc), (ini + timedelta(hours=2)).astimezone(timezone.utc)


def ev_detalles(e):
    partes = [F(e, "descripcion"), F(e, "hora") if not ev_horario(e) else "", F(e, "precio"), e.get("fuente_url", "")]
    return "\n\n".join(x for x in partes if x)


def ev_lugar(e):
    return f'{F(e, "lugar")}, {muni_name(e.get("municipio", ""))}, Lanzarote'


def ev_ics(e):
    def txt(v):
        return str(v).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

    def fold(line):
        out, b = [], line.encode("utf-8")
        while len(b) > 75:
            cut = 75 if not out else 74
            while (b[cut] & 0xC0) == 0x80:
                cut -= 1
            out.append(b[:cut].decode("utf-8"))
            b = b[cut:]
        out.append(b.decode("utf-8"))
        return "\r\n ".join(out)

    h = ev_horario(e)
    if h:
        cuando = [f"DTSTART:{h[0]:%Y%m%dT%H%M%SZ}", f"DTEND:{h[1]:%Y%m%dT%H%M%SZ}"]
    else:
        cuando = [f"DTSTART;VALUE=DATE:{e['ini']:%Y%m%d}", f"DTEND;VALUE=DATE:{e['fin'] + timedelta(days=1):%Y%m%d}"]
    lineas = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{SITE_NAME}//Agenda//{LANG[0].upper()}", "CALSCALE:GREGORIAN",
              "METHOD:PUBLISH", "BEGIN:VEVENT", f"UID:{e['slug']}@guiadearrecife.es",
              f"DTSTAMP:{HOY[0]:%Y%m%d}T070000Z", *cuando, f"SUMMARY:{txt(F(e, 'titulo'))}",
              f"LOCATION:{txt(ev_lugar(e))}", f"DESCRIPTION:{txt(ev_detalles(e))}"]
    if e.get("fuente_url"):
        lineas.append(f"URL:{e['fuente_url']}")
    lineas += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(fold(x) for x in lineas) + "\r\n"


def ev_google(e):
    h = ev_horario(e)
    fechas = (f"{h[0]:%Y%m%dT%H%M%SZ}/{h[1]:%Y%m%dT%H%M%SZ}" if h
              else f"{e['ini']:%Y%m%d}/{e['fin'] + timedelta(days=1):%Y%m%d}")
    return "https://calendar.google.com/calendar/render?" + urlencode(
        {"action": "TEMPLATE", "text": F(e, "titulo"), "dates": fechas, "details": ev_detalles(e), "location": ev_lugar(e)})


def ev_ics_path(e):
    return R("agenda") + f"ics/{e['slug']}.ics"


def evento_html(e, L):
    fuente = (f'<a href="{esc(e["fuente_url"])}" rel="noopener" target="_blank">{esc(e["fuente_nombre"])}</a>'
              if e.get("fuente_url") else "")
    return (f'<article class="ev" data-muni="{esc(slugify(e.get("municipio", "")))}" data-fin="{e["fin"].isoformat()}">'
            f'{date_block(e["ini"], e["fin"])}'
            f'<div class="ev-body"><p class="evcard-cat">{esc(cat_name(e.get("categoria", "Actos")))} · {esc(ev_when(e))}</p>'
            f'<h3>{esc(F(e, "titulo"))}</h3><p class="ev-place">{esc(F(e, "lugar"))} · '
            f'<a href="{L(R("municipio", e.get("municipio", "Toda la isla")))}">{esc(muni_name(e.get("municipio", "")))}</a></p>'
            f'<p class="ev-desc">{esc(F(e, "descripcion"))}</p>'
            f'<p class="ev-meta">{esc(F(e, "precio"))}{" · " + t("fuente") + ": " + fuente if fuente else ""}</p>'
            f'<p class="ev-cal"><a class="btn btn-ghost btn-sm" href="{L.file(ev_ics_path(e))}" download="{esc(e["slug"])}.ics">'
            f'<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15" rx="2" fill="none" stroke="currentColor" stroke-width="2"/>'
            f'<path d="M3.5 10h17M8 3v4M16 3v4M12 13v5M9.5 15.5h5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>{t("cal_add")}</a>'
            f'<a class="ev-gcal" href="{esc(ev_google(e))}" rel="noopener" target="_blank">{t("cal_google")}</a></p></div>'
            f'{ev_foto(e, L)}</article>')


def ev_foto(e, L):
    if not e.get("imagen"):
        return ""
    credito = f'<figcaption>{esc(e["credito"])}</figcaption>' if e.get("credito") else ""
    return (f'<figure class="ev-img"><img src="{L.file(e["imagen"])}" alt="{esc(F(e, "titulo"))}" loading="lazy">'
            f'{credito}</figure>')


def band(title, sub, inner, cls="", more=""):
    return (f'<section class="band {cls}"><div class="wrap">'
            f'<header class="band-head"><h2>{title}</h2>{f"<p>{sub}</p>" if sub else ""}{more}</header>'
            f'{inner}</div></section>')


# ---------------------------------------------------------------- portada
def build_home(noticias, dias, agenda, negocios):
    path, alt = R("home"), R("home", lang="es" if en() else "en")
    L = Linker(path)
    hoy = noticias[0]["fecha"]
    todas = [n for n in noticias if n["fecha"] == hoy]
    diez = [n for n in todas if n["bloque"] == "diez"] or todas
    recientes = [n for n in noticias if (hoy - n["fecha"]).days <= 7]
    empresas = [n for n in recientes if n["bloque"] == "empresas"][:6]
    ciber = [n for n in recientes if n["bloque"] == "ciber"][:3]
    redes = [n for n in noticias if n["bloque"] == "redes" and (hoy - n["fecha"]).days <= 1][:3]
    previas = sorted({n["fecha"] for n in noticias if n["fecha"] < hoy}, reverse=True)
    ayer = []
    if len(diez) < 10 and previas:
        ayer = [n for n in noticias if n["fecha"] == previas[0] and n["bloque"] == "diez"][:6]
    meta = dias.get(hoy, {})
    lead, seg, resto = diez[0], diez[1:3], diez[3:]
    grid4, compact = resto[:4], resto[4:]

    indice = "".join(f'<li><span class="num">{n["orden"]:02d}</span><a href="{L(R("noticia", n))}">{esc(F(n, "titulo"))}</a></li>'
                     for n in diez)
    saludo = esc(F(meta, "saludo") or t("hola"))
    nota = f'<span class="hello-note">{esc(F(meta, "nota"))}</span>' if F(meta, "nota") else ""

    hero = f"""
<section class="hello"><div class="wrap"><p><strong>{saludo}</strong> {nota}</p></div></section>
<section class="hero"><div class="wrap hero-grid">
  <article class="lead">
    {figure(lead, L, "fig-lead")}
    <div class="meta-row"><span class="num">01</span>{sec_chip(lead, L)}<span class="where">{esc(muni_text(lead))}</span></div>
    <h2><a href="{L(R('noticia', lead))}">{esc(F(lead, 'titulo'))}</a></h2>
    <p class="lede">{esc(F(lead, 'entradilla'))}</p>
  </article>
  <div class="hero-second">{''.join(story_card(n, L, 'card card-second') for n in seg)}</div>
  <aside class="hero-index"><h2 class="mini-head">{t('las_hoy', n=len(diez))}</h2><ol class="index-list">{indice}</ol></aside>
</div></section>"""

    mas = ""
    if grid4:
        mas = (f'<section class="more-news"><div class="wrap"><h2 class="rule-head">{t("mas_hoy")}</h2>'
               f'<div class="{ {1: "grid2", 2: "grid2", 3: "grid3"}.get(len(grid4), "grid4") }">{"".join(story_card(n, L) for n in grid4)}</div>'
               f'<div class="grid3 grid-compact">{"".join(story_card(n, L, "card card-row", lede=False) for n in compact)}</div></div></section>')
    ay = ""
    if ayer:
        ay = (f'<section class="more-news more-yesterday"><div class="wrap"><h2 class="rule-head">{t("ayer_t")}</h2>'
              f'<p class="rule-sub">{t("ayer_s", d=fecha_larga(previas[0]))}</p>'
              f'<div class="grid3">{"".join(story_card(n, L, "card card-row", lede=False) for n in ayer)}</div>'
              f'<a class="band-more" href="{L(R("dia", previas[0]))}">{fecha_larga(previas[0])} →</a></div></section>')
    tema = (f'<section class="quote"><div class="wrap"><p class="quote-label">{t("tema")}</p>'
            f'<blockquote>{esc(F(meta, "tema"))}</blockquote></div></section>') if F(meta, "tema") else ""
    emp = ""
    if empresas:
        if len(empresas) >= 4:
            empresas = empresas[:4]
        cls = {1: "grid2", 2: "grid2", 3: "grid3"}.get(len(empresas), "grid4")
        emp = band(t("emp_t"), t("emp_s"),
                   f'<div class="{cls}">{"".join(story_card(n, L, "card card-biz") for n in empresas)}</div>',
                   "band-biz", f'<a class="band-more" href="{L(R("seccion", "Empresas"))}">{t("ver_sec")}</a>')
    red = ""
    if redes:
        red = band(t("red_t"), t("red_s"), f'<div class="grid3">{"".join(story_card(n, L) for n in redes)}</div>', "band-redes")
    cib = ""
    if ciber:
        items = "".join(
            f'<article class="alert"><p class="alert-level"><span class="dot"></span>{t("nivel", x=nivel_name(n["nivel"] or "informativo"))}</p>'
            f'<h3><a href="{L(R("noticia", n))}">{esc(F(n, "titulo"))}</a></h3><p>{esc(F(n, "entradilla"))}</p>'
            f'<a class="alert-cta" href="{L(R("noticia", n))}">{t("que_hacer")}</a></article>' for n in ciber)
        cib = band(t("cib_t"), t("cib_s"), f'<div class="alerts">{items}</div>', "band-cyber",
                   f'<a class="band-more" href="{L(R("seccion", "Ciberseguridad"))}">{t("cib_all")}</a>')
    proximos = [e for e in agenda if e["fin"] >= hoy][:6]
    ag = ""
    if proximos:
        ag = band(t("agenda"), t("ag_s"), f'<div class="evgrid">{"".join(ev_card(e, hoy) for e in proximos)}</div>',
                  "band-agenda", f'<a class="band-more" href="{L(R("agenda"))}">{t("ag_all")}</a>')
    cuenta = {}
    for n in todas:
        for m in n["municipios"]:
            cuenta[m] = cuenta.get(m, 0) + 1
    munis = "".join(f'<a href="{L(R("municipio", m))}">{esc(muni_name(m))}<span>{cuenta.get(m, 0)}</span></a>' for m in MUNICIPIOS)
    biz = f"""
<section class="band band-local"><div class="wrap local-grid">
  <div class="biz-promo">
    <p class="biz-promo-kicker">{t('biz_k')}</p>
    <h2>{t('biz_h')}</h2>
    <p>{t('biz_p')}</p>
    <a class="btn" href="{L(R('negocios'))}">{t('biz_btn2') if negocios else t('biz_btn')}</a>
  </div>
  <div class="munis-box"><h2 class="mini-head">{t('munis_h')}</h2><div class="muni-chips">{munis}</div></div>
</div></section>"""
    eds = ""
    if previas:
        filas = ""
        for d in previas[:7]:
            del_dia = [n for n in noticias if n["fecha"] == d]
            top = next((n for n in del_dia if n["bloque"] == "diez"), del_dia[0])
            filas += (f'<a class="edcard" href="{L(R("dia", d))}">{date_block(d)}<span class="edcard-txt">'
                      f'<span class="edcard-date">{esc(fecha_larga(d))}</span><span class="edcard-top">{esc(F(top, "titulo"))}</span>'
                      f'<span class="count">{t("n_noticias", n=len(del_dia))}</span></span></a>')
        eds = band(t("ed_t"), t("ed_s"), f'<div class="edgrid">{filas}</div>', "band-eds",
                   f'<a class="band-more" href="{L(R("archivo"))}">{t("ed_all")}</a>')
    body = hero + mas + ay + tema + emp + red + cib + ag + eds + biz
    img, size = news_image(lead)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "@id": f"{SITE_URL}/#website", "url": abs_url(R("home")), "name": SITE_NAME,
         "description": t("tagline"), "inLanguage": LANG[0], "publisher": {"@id": f"{SITE_URL}/#org"}},
        org_ld()]}
    return page(title=SITE_NAME, path=path, alt=alt, body=body,
                description=f"{fecha_corta(hoy)}: {F(lead, 'titulo')}", fragment=PREVIEW and not en(),
                image=img, image_size=size, extra_head=ld_tag(ld), lastmod=pub_dt(hoy).isoformat())


# ---------------------------------------------------------------- noticia
def build_noticia(n, noticias, agenda):
    path = R("noticia", n)
    alt = R("noticia", n, lang="es" if en() else "en")
    L = Linker(path)
    body_paras = n["parrafos_en"] if en() and n["parrafos_en"] else n["parrafos"]
    parrafos = "".join(f"<p>{inline_md(p)}</p>" for p in body_paras)
    fuentes = "".join(f'<li><a href="{esc(f["url"])}" rel="noopener" target="_blank">{esc(f["nombre"])}</a></li>'
                      for f in n["fuentes"])
    dia = [x for x in noticias if x["fecha"] == n["fecha"]]
    diez = [x for x in dia if x["bloque"] == "diez"]
    mismo = [x for x in dia if x["bloque"] == n["bloque"] and x["slug"] != n["slug"]]
    if n["bloque"] == "diez":
        ruta = t("noticia_n", o=n["orden"], n=len(diez))
        sigue = [x for x in diez if x["orden"] > n["orden"]][:3] or [x for x in diez if x["slug"] != n["slug"]][:3]
    else:
        ruta = esc(sec_name(n["seccion"]))
        sigue = mismo[:3] or diez[:3]
    share_url = f"{SITE_URL}/{path}"
    wa = "https://wa.me/?text=" + pct(f"{F(n, 'titulo')} {share_url}")
    indice = "".join(
        f'<li{" class=is-here" if x["slug"] == n["slug"] else ""}><span class="num">{x["orden"]:02d}</span>'
        f'<a href="{L(R("noticia", x))}">{esc(F(x, "titulo"))}</a></li>' for x in diez)
    hoy = HOY[0] or n["fecha"]
    prox = "".join(ev_card(e, hoy) for e in [e for e in agenda if e["fin"] >= hoy][:3])
    alerta = (f'<p class="alert-level alert-inline"><span class="dot"></span>{t("nivel", x=nivel_name(n["nivel"]))}</p>'
              if n["nivel"] else "")
    credito = f'<figcaption>{esc(n["credito"])}</figcaption>' if n["credito"] else ""
    img, size = news_image(n)
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": F(n, "titulo"),
          "description": F(n, "entradilla"), "datePublished": pub_dt(n["fecha"]).isoformat(),
          "dateModified": mod_date(n), "inLanguage": LANG[0], "articleSection": sec_name(n["seccion"]),
          "contentLocation": [{"@type": "Place", "name": f"{m}, Lanzarote"} for m in n["municipios"]],
          "author": {"@type": "Organization", "name": SITE_NAME, "url": abs_url(R("sobre"))},
          "publisher": org_ld(), "mainEntityOfPage": share_url, "isBasedOn": [f["url"] for f in n["fuentes"]]}
    if img:
        ld["image"] = [img]
    body = f"""
<div class="wrap">
  <nav class="crumbs" aria-label="{t('ruta')}"><a href="{L(R('home'))}">{t('portada')}</a> / <a href="{L(R('seccion', n['seccion']))}">{esc(sec_name(n['seccion']))}</a> / <span>{ruta}</span></nav>
  <header class="story-head">
    <div class="meta-row">{sec_chip(n, L)}<span class="where">{esc(muni_text(n))}</span></div>
    {alerta}
    <h1>{esc(F(n, 'titulo'))}</h1>
    <p class="story-lede">{esc(F(n, 'entradilla'))}</p>
    <p class="byline"><a href="{L(R('dia', n['fecha']))}"><time datetime="{n['fecha'].isoformat()}">{esc(fecha_larga(n['fecha']))}</time></a> · {t('byline')}</p>
  </header>
  <figure class="story-fig"><img src="{cover_src(n, L)}" alt="">{credito}</figure>
  <div class="story-grid">
    <article class="story-body">
      {parrafos}
      <section class="sources"><h2>{t('fuentes')}</h2><ul>{fuentes}</ul>
        <p class="sources-note">{t('fuentes_nota')}{(" " + t('nota_ia')) if AUTO else ""}</p></section>
      <div class="share">
        <a class="btn" href="{wa}" rel="noopener" target="_blank">{t('wa')}</a>
        <button class="btn btn-ghost" type="button" id="copiar" data-url="{esc(share_url)}" data-ok="{t('copiado')}">{t('copiar')}</button>
        <span class="copied" id="copiado" role="status"></span>
      </div>
    </article>
    <aside class="story-side">
      <section><h2 class="mini-head">{t('las_hoy', n=len(diez))}</h2><ol class="index-list">{indice}</ol></section>
      {f'<section><h2 class="mini-head">{t("agenda")}</h2><div class="side-evs">{prox}</div><a class="more" href="{L(R("agenda"))}">{t("ag_all")}</a></section>' if prox else ''}
    </aside>
  </div>
</div>
<section class="more-news more-after"><div class="wrap"><h2 class="rule-head">{t('sigue')}</h2>
<div class="grid3">{''.join(story_card(x, L) for x in sigue)}</div></div></section>
<script>
(function(){{var b=document.getElementById('copiar'),s=document.getElementById('copiado');if(!b)return;
b.addEventListener('click',function(){{var u=b.getAttribute('data-url');
function ok(){{s.textContent=b.getAttribute('data-ok');}}function no(){{s.textContent=u;}}
try{{navigator.clipboard.writeText(u).then(ok,no);}}catch(e){{no();}}}});}})();
</script>"""
    extra = (ld_tag(ld) + f'<meta property="article:published_time" content="{pub_dt(n["fecha"]).isoformat()}">'
             f'<meta property="article:modified_time" content="{esc(mod_date(n))}">'
             f'<meta property="article:section" content="{esc(sec_name(n["seccion"]))}">')
    return page(title=F(n, "titulo"), path=path, alt=alt, body=body,
                description=F(n, "entradilla"), og_type="article", extra_head=extra,
                image=img, image_size=size, crumbs=sec_crumbs(n["seccion"]) + [(F(n, "titulo"), path)],
                lastmod=mod_date(n))


# ---------------------------------------------------------------- listados
def page_head(eyebrow, titulo, intro="", color=""):
    style = f' style="--sec:{color}"' if color else ""
    intro_html = f'<p class="page-intro">{intro}</p>' if intro else ""
    return (f'<header class="page-head"{style}><div class="wrap"><p class="eyebrow">{esc(eyebrow)}</p>'
            f'<h1>{esc(titulo)}</h1>{intro_html}</div></header>')


def subnav(grupo, actual, L):
    hijas = [s for s in SECCIONES if GRUPO_DE.get(s) == grupo]
    enlaces = [(grupo, t("todo"))] + [(s, sec_name(s)) for s in hijas]
    return ('<div class="wrap"><nav class="subnav" aria-label="' + t("secciones") + '">'
            + "".join(f'<a href="{L(R("seccion", s))}"{" aria-current=page" if s == actual else ""}>{esc(nombre)}</a>'
                      for s, nombre in enlaces)
            + '</nav></div>')


def build_lista(titulo, eyebrow, items, path, alt, intro="", color="", prev_d=None, next_d=None, layout="grid",
                grupo=None, actual=None, crumbs=None):
    L = Linker(path)
    img, size = news_image(items[0]) if items else (None, None)
    seo = dict(image=img, image_size=size, crumbs=crumbs,
               lastmod=max(mod_date(n) for n in items) if items else None)
    nav = ""
    if prev_d or next_d:
        nav = ('<nav class="daynav">'
               + (f'<a class="daynav-prev" href="{L(R("dia", prev_d))}">← {t("dia_prev")}<span>{esc(fecha_corta(prev_d))}</span></a>' if prev_d else '<span></span>')
               + f'<a class="daynav-all" href="{L(R("archivo"))}">{t("ed_all")}</a>'
               + (f'<a class="daynav-next" href="{L(R("dia", next_d))}">{t("dia_next")} →<span>{esc(fecha_corta(next_d))}</span></a>' if next_d else '<span></span>')
               + '</nav>')
    if layout == "feed":
        filas = ""
        for i, n in enumerate(items):
            cls = "row-item row-lead" if i == 0 else "row-item"
            filas += (f'<article class="{cls}">{figure(n, L)}<div class="txt">'
                      f'<div class="meta-row">{sec_chip(n, L)}<a class="where" href="{L(R("dia", n["fecha"]))}">{esc(fecha_larga(n["fecha"]))}</a></div>'
                      f'<h3><a href="{L(R("noticia", n))}">{esc(F(n, "titulo"))}</a></h3>'
                      f'<p class="lede">{esc(F(n, "entradilla"))}</p>'
                      f'<p class="row-where">{esc(muni_text(n))}</p></div></article>')
        secs = "".join(f'<li><a href="{L(R("seccion", s_))}">{esc(sec_name(s_))}</a></li>' for s_ in SECCIONES_NAV)
        munis = "".join(f'<a href="{L(R("municipio", m))}">{esc(muni_name(m))}</a>' for m in MUNICIPIOS)
        aside = (f'<aside class="feed-side"><section><h2 class="mini-head">{t("secciones")}</h2><ul class="side-list">{secs}</ul></section>'
                 f'<section><h2 class="mini-head">{t("municipios")}</h2><div class="muni-chips">{munis}</div></section>'
                 f'<a class="more" href="{L(R("archivo"))}">{t("ed_all")}</a></aside>')
        vacio = f'<p class="empty">{t("vacio")}</p>' if not items else ""
        body = (page_head(eyebrow, titulo, esc(intro), color)
                + (subnav(grupo, actual, L) if grupo else "")
                + f'<div class="wrap list-wrap feed-grid"><div class="feed">{filas}{vacio}</div>{aside}</div>')
        return page(title=titulo, path=path, alt=alt, body=body, description=f"{titulo} · {SITE_NAME}", **seo)
    grupos = {}
    for n in items:
        grupos.setdefault(n["fecha"], []).append(n)
    bloques = "".join(
        f'<section class="day-group"><h2 class="rule-head"><a href="{L(R("dia", d))}">{esc(fecha_larga(d))}</a></h2>'
        f'<div class="grid3">{"".join(story_card(n, L) for n in grupos[d])}</div></section>'
        for d in sorted(grupos, reverse=True))
    vacio = f'<p class="empty">{t("vacio")}</p>' if not items else ""
    body = page_head(eyebrow, titulo, esc(intro), color) + f'<div class="wrap list-wrap">{nav}{bloques}{vacio}{nav}</div>'
    return page(title=titulo, path=path, alt=alt, body=body, description=f"{titulo} · {SITE_NAME}", **seo)


def build_archivo(noticias):
    path, alt = R("archivo"), R("archivo", lang="es" if en() else "en")
    L = Linker(path)
    filas = []
    for d in sorted({n["fecha"] for n in noticias}, reverse=True):
        del_dia = [n for n in noticias if n["fecha"] == d]
        filas.append(f'<li><a href="{L(R("dia", d))}">{date_block(d)}<span class="arch-txt"><span class="arch-date">{esc(fecha_larga(d))}</span>'
                     f'<span class="arch-top">{esc(F(del_dia[0], "titulo"))}</span></span><span class="count">{t("n_noticias", n=len(del_dia))}</span></a></li>')
    body = page_head(t("hemeroteca"), t("archivo"), t("arch_intro")) + \
        f'<div class="wrap list-wrap"><ul class="archive">{"".join(filas)}</ul></div>'
    return page(title=t("archivo"), path=path, alt=alt, body=body)


def build_buscar(noticias):
    path, alt = R("buscar"), R("buscar", lang="es" if en() else "en")
    L = Linker(path)
    idx = [{"t": F(n, "titulo"), "e": F(n, "entradilla"), "s": sec_name(n["seccion"]), "m": muni_text(n),
            "f": fecha_larga(n["fecha"]), "u": L(R("noticia", n)), "i": cover_src(n, L)} for n in noticias]
    data = json.dumps(idx, ensure_ascii=False).replace("</", "<\\/")
    strs = json.dumps({"one": t("bus_1"), "many": t("bus_n"), "last": t("bus_last", n="{n}")}, ensure_ascii=False)
    body = page_head(t("buscar"), t("bus_h")) + f"""
<div class="wrap list-wrap">
<form class="search" id="f" role="search"><label for="q" class="sr">{t('bus_label')}</label>
<input id="q" type="search" placeholder="{t('bus_ph')}" autocomplete="off"></form>
<p class="search-count" id="n" role="status"></p>
<div class="grid3" id="r"></div></div>
<script>
(function(){{var D={data},S={strs};
function norm(s){{return s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');}}
function e(s){{return s.replace(/[&<>"]/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];}});}}
var q=document.getElementById('q'),r=document.getElementById('r'),n=document.getElementById('n');
function run(){{var tx=norm(q.value.trim());var w=tx?tx.split(/\\s+/):[];
var res=D.filter(function(x){{var h=norm(x.t+' '+x.e+' '+x.s+' '+x.m);return w.every(function(k){{return h.indexOf(k)>-1;}});}});
n.textContent=w.length?(res.length+(res.length===1?S.one:S.many)):S.last.replace('{{n}}',Math.min(res.length,12));
r.innerHTML=res.slice(0,w.length?60:12).map(function(x){{return '<article class="card"><a class="fig" href="'+x.u+'" tabindex="-1" aria-hidden="true"><img src="'+x.i+'" alt="" loading="lazy"><span class="fig-place">'+e(x.m.split(' · ')[0])+'</span></a><div class="txt"><div class="meta-row"><span class="kicker">'+e(x.s)+'</span><span class="where">'+e(x.f)+'</span></div><h3><a href="'+x.u+'">'+e(x.t)+'</a></h3><p class="lede">'+e(x.e)+'</p></div></article>';}}).join('');}}
document.getElementById('f').addEventListener('submit',function(ev){{ev.preventDefault();run();}});
q.addEventListener('input',run);try{{var p=new URLSearchParams(location.search).get('q');if(p)q.value=p;}}catch(e){{}}run();}})();
</script>"""
    return page(title=t("buscar"), path=path, alt=alt, body=body)


def build_agenda(agenda, hoy):
    path, alt = R("agenda"), R("agenda", lang="es" if en() else "en")
    L = Linker(path)
    por_dia = {}
    for e in [e for e in agenda if e["fin"] >= hoy]:
        clave = max(e["ini"], hoy) if e["fin"] != e["ini"] else e["ini"]
        por_dia.setdefault(clave, []).append(e)
    bloques = "".join(
        f'<section class="ev-day"><h2 class="rule-head">{esc(fecha_larga(d))}</h2>'
        f'{"".join(evento_html(e, L) for e in por_dia[d])}</section>' for d in sorted(por_dia))
    filtros = f'<button type="button" class="filter is-on" data-f="" aria-pressed="true">{t("ag_todas")}</button>' + "".join(
        f'<button type="button" class="filter" data-f="{slugify(m)}" aria-pressed="false">{esc(m)}</button>'
        for m in MUNICIPIOS if m != "Toda la isla")
    body = page_head(t("ag_eb"), t("agenda"), t("ag_intro")) + f"""
<div class="wrap list-wrap">
<div class="filters" role="group" aria-label="{t('ag_filtro')}">{filtros}</div>
<div id="ev-list">{bloques or f'<p class="empty">{t("ag_vacio")}</p>'}</div>
<p class="empty" id="ev-none" hidden>{t('ag_none')}</p></div>
<script>
(function(){{var bs=document.querySelectorAll('.filter'),evs=document.querySelectorAll('.ev'),days=document.querySelectorAll('.ev-day'),none=document.getElementById('ev-none');
var d=new Date(),today=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
function apply(f){{var shown=0;evs.forEach(function(e){{var ok=(!f||e.dataset.muni===f||e.dataset.muni==='toda-la-isla')&&e.dataset.fin>=today;e.hidden=!ok;if(ok)shown++;}});
days.forEach(function(x){{x.hidden=!x.querySelector('.ev:not([hidden])');}});none.hidden=shown>0||!evs.length;}}
function pick(f){{var b=null;bs.forEach(function(x){{var on=x.dataset.f===f;x.classList.toggle('is-on',on);x.setAttribute('aria-pressed',on?'true':'false');if(on)b=x;}});if(!b){{f='';bs[0].classList.add('is-on');bs[0].setAttribute('aria-pressed','true');}}apply(f);}}
bs.forEach(function(b){{b.addEventListener('click',function(){{pick(b.dataset.f);try{{history.replaceState(null,'',b.dataset.f?'#'+b.dataset.f:location.pathname+location.search);}}catch(e){{}}}});}});
pick(decodeURIComponent(location.hash.slice(1)));}})();
</script>"""
    return page(title=t("agenda"), path=path, alt=alt, body=body, description=t("ag_intro"))


def build_negocios(negocios):
    path, alt = R("negocios"), R("negocios", lang="es" if en() else "en")
    if negocios:
        cats = sorted({b.get("categoria", "Otros") for b in negocios})
        inner = "".join(
            f'<section class="biz-group"><h2 class="rule-head">{esc(c)}</h2><div class="biz-grid">'
            + "".join(
                f'<article class="biz{" biz-dest" if b.get("destacado") == "si" else ""}">'
                f'{"<p class=biz-flag>" + t("destacado") + "</p>" if b.get("destacado") == "si" else ""}'
                f'<h3>{esc(b.get("nombre", ""))}</h3><p class="biz-zone">{esc(b.get("barrio", ""))}</p>'
                f'<p>{esc(F(b, "descripcion"))}</p><p class="biz-contact">{esc(b.get("direccion", ""))}'
                f'{"<br>" + esc(b["telefono"]) if b.get("telefono") else ""}'
                f'{"<br><a href=" + chr(34) + esc(b["web"]) + chr(34) + " rel=noopener target=_blank>Web</a>" if b.get("web") else ""}</p></article>'
                for b in negocios if b.get("categoria", "Otros") == c) + "</div></section>" for c in cats)
    else:
        inner = (f'<section class="biz-empty"><h2>{t("dir_empty_h")}</h2><p>{t("dir_empty_p")}</p>'
                 '<ul class="biz-cats">' + "".join(f"<li>{esc(c)}</li>" for c in t("dir_cats")) + '</ul>'
                 f'<p class="biz-cta">{t("dir_cta")}</p></section>')
    body = page_head(t("dir_eb"), t("negocios"), t("dir_intro")) + f'<div class="wrap list-wrap">{inner}</div>'
    return page(title=t("negocios"), path=path, alt=alt, body=body, description=t("dir_intro"))


def build_sobre():
    path, alt = R("sobre"), R("sobre", lang="es" if en() else "en")
    L = Linker(path)
    txt = SOBRE[LANG[0]].replace('href="../linea-editorial/"', f'href="{L(R("linea"))}"').replace('href="../editorial-policy/"', f'href="{L(R("linea"))}"')
    body = page_head(t("sobre_eb"), t("sobre_h")) + f'<div class="wrap list-wrap"><div class="prose">{txt}</div></div>'
    return page(title=t("sobre"), path=path, alt=alt, body=body)


def build_linea():
    path, alt = R("linea"), R("linea", lang="es" if en() else "en")
    body = page_head(t("sobre_eb"), t("linea_h"), t("linea_intro")) + f'<div class="wrap list-wrap"><div class="prose">{LINEA[LANG[0]]}</div></div>'
    return page(title=t("linea"), path=path, alt=alt, body=body, description=t("linea_intro"))


def build_404():
    body = page_head("Error 404", "Esta página no existe · Page not found",
                     'Puede que el enlace esté mal escrito o que la noticia se haya movido. <a href="/">Vuelve a la portada</a>. '
                     '· The link may be wrong or the story may have moved. <a href="/en/">Go to the English home page</a>.')
    return page(title="404", path="404.html", alt="404.html", body=body,
                extra_head='<base href="/"><meta name="robots" content="noindex">')


def build_feed(noticias):
    items = []
    for n in noticias[:50]:
        link = f"{SITE_URL}/{R('noticia', n)}"
        pub = pub_dt(n["fecha"])
        items.append(f"<item><title>{esc(F(n, 'titulo'))}</title><link>{link}</link><guid>{link}</guid>"
                     f"<pubDate>{pub.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>"
                     f"<category>{esc(sec_name(n['seccion']))}</category><description>{esc(F(n, 'entradilla'))}</description></item>")
    return ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
            f"<title>{SITE_NAME}</title><link>{SITE_URL}/{R('home')}</link><description>{esc(t('tagline'))}</description>"
            f"<language>{LANG[0]}</language>{''.join(items)}</channel></rss>")


def build_sitemap():
    """Todas las páginas, con fecha de actualización y su equivalente en el otro idioma."""
    urls = []
    for path, alt, lastmod in SITEMAP:
        es_p, en_p = (alt, path) if path.startswith("en/") else (path, alt)
        mod = f"<lastmod>{esc(lastmod)}</lastmod>" if lastmod else ""
        urls.append(f"<url><loc>{abs_url(path)}</loc>{mod}"
                    f'<xhtml:link rel="alternate" hreflang="es" href="{abs_url(es_p)}"/>'
                    f'<xhtml:link rel="alternate" hreflang="en" href="{abs_url(en_p)}"/>'
                    f'<xhtml:link rel="alternate" hreflang="x-default" href="{abs_url(es_p)}"/></url>')
    return ('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            f'xmlns:xhtml="http://www.w3.org/1999/xhtml">{"".join(urls)}</urlset>')


def build_news_sitemap(noticias):
    """Mapa de Google News: solo las noticias de las últimas 48 horas, en los dos idiomas."""
    limite = datetime.now(timezone.utc) - timedelta(hours=48)
    urls = []
    for n in noticias:
        if pub_dt(n["fecha"]) < limite:
            continue
        for lang in LANGS:
            LANG[0] = lang
            urls.append(f"<url><loc>{abs_url(R('noticia', n))}</loc><news:news><news:publication>"
                        f"<news:name>{SITE_NAME}</news:name><news:language>{lang}</news:language></news:publication>"
                        f"<news:publication_date>{pub_dt(n['fecha']).isoformat()}</news:publication_date>"
                        f"<news:title>{esc(F(n, 'titulo'))}</news:title></news:news></url>")
    LANG[0] = "es"
    return ('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            f'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">{"".join(urls)}</urlset>')


# ---------------------------------------------------------------- principal
def write(rel, text):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def build_lang(noticias, dias, agenda, negocios, hoy):
    paths = []
    other = "es" if en() else "en"

    def put(path, html_):
        write(path + "index.html", html_)
        paths.append(path)

    put(R("home"), build_home(noticias, dias, agenda, negocios))
    put(R("agenda"), build_agenda(agenda, hoy))
    for e in agenda:
        if e["fin"] >= hoy:
            write(ev_ics_path(e), ev_ics(e))
    put(R("negocios"), build_negocios(negocios))
    for n in noticias:
        put(R("noticia", n), build_noticia(n, noticias, agenda))
    for s in SECCIONES:
        items = [n for n in noticias if n["seccion"] == s]
        grupo = GRUPO_DE.get(s)
        put(R("seccion", s), build_lista(sec_name(s), sec_name(grupo) if grupo else t("sec_eb"), items,
                                         R("seccion", s), R("seccion", s, lang=other),
                                         color=COLOR_SECCION.get(s, ""), layout="feed", grupo=grupo, actual=s,
                                         crumbs=sec_crumbs(s)))
    for g in SECCIONES_NAV:
        if g not in GRUPOS:
            continue
        items = [n for n in noticias if GRUPO_DE.get(n["seccion"]) == g]
        put(R("seccion", g), build_lista(sec_name(g), t("sec_eb"), items, R("seccion", g), R("seccion", g, lang=other),
                                         color=COLOR_SECCION.get(g, ""), layout="feed", grupo=g, actual=g,
                                         crumbs=sec_crumbs(g)))
    for m in MUNICIPIOS:
        items = [n for n in noticias if m in n["municipios"]]
        intro = t("toda_intro") if m == "Toda la isla" else t("muni_intro", m=m)
        put(R("municipio", m), build_lista(muni_name(m), t("muni_eb"), items, R("municipio", m), R("municipio", m, lang=other), intro, layout="feed"))
    fechas = sorted({n["fecha"] for n in noticias})
    for i, d in enumerate(fechas):
        items = [n for n in noticias if n["fecha"] == d]
        put(R("dia", d), build_lista(fecha_larga(d), t("dia_eb"), items, R("dia", d), R("dia", d, lang=other),
                                     F(dias.get(d, {}), "tema"),
                                     prev_d=fechas[i - 1] if i > 0 else None,
                                     next_d=fechas[i + 1] if i + 1 < len(fechas) else None,
                                     crumbs=[(t("portada"), R("home")), (t("archivo"), R("archivo")),
                                             (fecha_larga(d), R("dia", d))]))
    put(R("archivo"), build_archivo(noticias))
    put(R("buscar"), build_buscar(noticias))
    put(R("sobre"), build_sobre())
    put(R("linea"), build_linea())
    if not PREVIEW:
        write(R("home") + "feed.xml", build_feed(noticias))
    return paths


def main():
    noticias, dias, agenda, negocios = load()
    if not noticias:
        raise SystemExit("No hay noticias en content/noticias")
    presentes = {n["seccion"] for n in noticias}
    SECCIONES[:] = [s for s in ORDEN_SECCIONES if s in presentes] + sorted(presentes - set(ORDEN_SECCIONES))
    SECCIONES_NAV[:] = []
    for s in SECCIONES:
        entrada = GRUPO_DE.get(s, s)
        if entrada not in SECCIONES_NAV:
            SECCIONES_NAV.append(entrada)
    hoy = noticias[0]["fecha"]
    HOY[0] = hoy

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for n in noticias:
        if not n["imagen"]:
            write(f"img/portadas/{n['slug']}.svg", cover_svg(n["slug"], COLOR_SECCION.get(n["seccion"], "#17633f"),
                                                                n["icono"] or ICONO_SECCION.get(n["seccion"], "edificio")))
    if (ROOT / "img").exists():
        shutil.copytree(ROOT / "img", OUT / "img", dirs_exist_ok=True)
    shutil.copytree(ROOT / "assets" / "fonts", OUT / "assets" / "fonts", ignore=shutil.ignore_patterns("*.css"))
    write("img/logo.svg", logo_svg())
    if not PREVIEW:
        # PNG de 1200 px para Google Discover, WhatsApp y Facebook, que no usan SVG
        PNG.update(n["slug"] for n in noticias if not n["imagen"] and rasterize(
            OUT / f"img/portadas/{n['slug']}.svg", OUT / f"img/portadas/{n['slug']}.png", 1200, 675))
        LOGO_PNG[0] = (rasterize(OUT / "img/logo.svg", OUT / "img/logo-512.png", 512, 512)
                       and rasterize(OUT / "img/logo.svg", OUT / "img/apple-touch-icon.png", 180, 180))
        sin_png = sum(1 for n in noticias if not n["imagen"]) - len(PNG)
        if sin_png:
            print(f"AVISO: {sin_png} portadas sin PNG (instala rsvg-convert: apt-get install librsvg2-bin)")

    paths = []
    for lang in LANGS:
        LANG[0] = lang
        paths += build_lang(noticias, dias, agenda, negocios, hoy)
    LANG[0] = "es"
    if not PREVIEW:
        write("404.html", build_404())
        write("sitemap.xml", build_sitemap())
        write("news-sitemap.xml", build_news_sitemap(noticias))
        write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\nSitemap: {SITE_URL}/news-sitemap.xml\n")
        write("CNAME", "guiadearrecife.es\n")
        write(".nojekyll", "")
    print(f"OK: {len(noticias)} noticias, {len(paths)} páginas ({', '.join(LANGS)}) en {OUT}")


if __name__ == "__main__":
    main()
