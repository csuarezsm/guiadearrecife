"""Pictogramas propios (rejilla de 64x64, solo trazo) para las portadas de las noticias.

Para elegir uno en una noticia, añade en su cabecera:  icono: velero
Si no se indica, se usa el de su sección (ver ICONO_SECCION).
"""
ICONOS = {
    "velero": '<path d="M32 8V46"/><path d="M33 10L50 42H33Z"/><path d="M30 16L14 42H30"/><path d="M10 46H54L48 54H16Z"/><path d="M4 60q5-4 10 0t10 0t10 0t10 0t10 0t10 0"/>',
    "casa": '<path d="M8 30L32 10L56 30"/><path d="M16 26V54H48V26"/><path d="M28 54V40H36V54"/><path d="M20 32H26V38H20Z"/><path d="M38 32H44V38H38Z"/>',
    "llave": '<circle cx="20" cy="32" r="11"/><circle cx="20" cy="32" r="3.5"/><path d="M31 32H58"/><path d="M50 32V41"/><path d="M57 32V39"/>',
    "basura": '<path d="M12 18H52"/><path d="M26 18V11H38V18"/><path d="M17 18L21 56H43L47 18"/><path d="M27 26V48"/><path d="M32 26V48"/><path d="M37 26V48"/>',
    "torre": '<path d="M32 6L19 58"/><path d="M32 6L45 58"/><path d="M12 18H52"/><path d="M16 30H48"/><path d="M25 19L40 30"/><path d="M39 19L24 30"/><path d="M21 44H43"/><path d="M21 44L45 58"/><path d="M43 44L19 58"/><path d="M12 18V23"/><path d="M52 18V23"/><path d="M16 30V35"/><path d="M48 30V35"/>',
    "agua": '<path d="M32 8C32 8 15 29 15 40a17 17 0 0 0 34 0C49 29 32 8 32 8Z"/><path d="M23 41a9 9 0 0 0 7 8"/>',
    "avion": '<path d="M6 42L52 18a4 4 0 0 1 5 5L14 48Z"/><path d="M30 31L22 13H28L42 25"/><path d="M33 38L40 54H34L26 42"/><path d="M12 43L7 34H11L17 40"/><path d="M4 60H60"/>',
    "sol": '<circle cx="32" cy="26" r="10"/><path d="M32 6V11M32 41V46M12 26H17M47 26H52M18 12L21.5 15.5M42.5 36.5L46 40M18 40L21.5 36.5M42.5 15.5L46 12"/><path d="M6 54q6.5-5 13 0t13 0t13 0t13 0"/>',
    "nube": '<path d="M18 38a10 10 0 0 1 1-20a14 14 0 0 1 27 3a8.5 8.5 0 0 1 0 17Z"/><path d="M22 45L18 55"/><path d="M32 45L28 55"/><path d="M42 45L38 55"/>',
    "coche": '<path d="M8 42V33L16 22H44L54 33V42Z"/><path d="M19 30L23 26H40L45 30Z"/><circle cx="19" cy="44" r="5"/><circle cx="45" cy="44" r="5"/><path d="M4 54H60"/>',
    "cono": '<path d="M27 10H37L48 50H16Z"/><path d="M22 27H42"/><path d="M19 38H45"/><path d="M10 50H54V56H10Z"/>',
    "urna": '<path d="M12 30H52V54H12Z"/><path d="M24 30H40"/><path d="M26 30V10H38V30"/><path d="M29 20L32 23L36 17"/>',
    "balanza": '<path d="M32 10V54"/><path d="M20 54H44"/><path d="M12 18H52"/><path d="M12 18L6 34H18Z"/><path d="M52 18L46 34H58Z"/><circle cx="32" cy="10" r="2.5"/>',
    "grafica": '<path d="M10 8V54H58"/><path d="M17 40H24V54H17Z"/><path d="M29 32H36V54H29Z"/><path d="M41 24H48V54H41Z"/><path d="M15 30L27 20L38 24L53 10"/><path d="M45 10H53V18"/>',
    "escudo": '<path d="M32 6L52 14V30C52 44 42 52 32 58C22 52 12 44 12 30V14Z"/><path d="M24 30H40V42H24Z"/><path d="M27 30V25a5 5 0 0 1 10 0V30"/>',
    "factura": '<path d="M16 6H40L50 16V58H16Z"/><path d="M40 6V16H50"/><path d="M22 26H44"/><path d="M22 34H44"/><path d="M22 42H36"/><path d="M38 52H44"/>',
    "tienda": '<path d="M8 22L14 10H50L56 22Z"/><path d="M8 22q4 6 8 0q4 6 8 0q4 6 8 0q4 6 8 0q4 6 8 0q4 6 8 0"/><path d="M12 27V54H52V27"/><path d="M24 54V38H34V54"/><path d="M39 36H47V44H39Z"/>',
    "personas": '<circle cx="18" cy="24" r="6"/><circle cx="46" cy="24" r="6"/><circle cx="32" cy="18" r="7"/><path d="M6 50a12 12 0 0 1 22 0"/><path d="M36 50a12 12 0 0 1 22 0"/><path d="M18 54a14 14 0 0 1 28 0"/>',
    "crono": '<circle cx="32" cy="36" r="18"/><path d="M27 10H37"/><path d="M32 10V18"/><path d="M32 36L40 28"/><path d="M47 19L51 15"/>',
    "vasija": '<path d="M24 10H40"/><path d="M26 10C26 18 14 22 14 36C14 48 22 56 32 56C42 56 50 48 50 36C50 22 38 18 38 10"/><path d="M17 32H47"/><path d="M15 42H49"/><path d="M19 37l4-3l4 3l4-3l4 3l4-3l4 3l4-3"/>',
    "emergencia": '<circle cx="32" cy="32" r="22"/><path d="M32 20V44"/><path d="M20 32H44"/>',
    "ue": '<circle cx="32" cy="14" r="2.2"/><circle cx="41" cy="16.4" r="2.2"/><circle cx="47.6" cy="23" r="2.2"/><circle cx="50" cy="32" r="2.2"/><circle cx="47.6" cy="41" r="2.2"/><circle cx="41" cy="47.6" r="2.2"/><circle cx="32" cy="50" r="2.2"/><circle cx="23" cy="47.6" r="2.2"/><circle cx="16.4" cy="41" r="2.2"/><circle cx="14" cy="32" r="2.2"/><circle cx="16.4" cy="23" r="2.2"/><circle cx="23" cy="16.4" r="2.2"/>',
    "calendario": '<path d="M10 14H54V54H10Z"/><path d="M10 24H54"/><path d="M22 8V18"/><path d="M42 8V18"/><path d="M18 32H22M30 32H34M42 32H46M18 42H22M30 42H34"/>',
    "megafono": '<path d="M10 28V38H18L40 49V17L18 28Z"/><path d="M18 38L22 50H28L25 39"/><path d="M47 25q6 8 0 16"/><path d="M52 20q10 13 0 26"/>',
    "hoja": '<path d="M12 52C12 26 32 12 54 10C52 34 38 52 12 52Z"/><path d="M12 52L38 26"/>',
    "edificio": '<path d="M8 22L32 10L56 22Z"/><path d="M12 26V50M22 26V50M32 26V50M42 26V50M52 26V50"/><path d="M8 54H56"/>',
}
ICONO_SECCION = {
    "Política": "urna", "Vivienda": "casa", "Empleo": "personas", "Economía": "grafica",
    "Empresas": "tienda", "Pymes y normativa": "factura", "Ciberseguridad": "escudo",
    "Servicios públicos": "edificio", "Infraestructuras": "torre", "Movilidad": "cono",
    "Medio ambiente": "hoja", "Tiempo": "sol", "Cultura": "vasija", "Deportes": "crono",
    "Redes": "megafono", "Sucesos": "emergencia",
}
