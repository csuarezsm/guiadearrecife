---
titulo: Si tu empresa tiene un Fortinet, toca actualizar ya
icono: escudo
fecha: 2026-10-24
bloque: ciber
nivel: Crítico
seccion: Ciberseguridad
municipios: Toda la isla
entradilla: INCIBE-CERT da la máxima gravedad a un paquete de parches de Fortinet para FortiOS, FortiManager, FortiAnalyzer, FortiMail y FortiAuthenticator.
fuentes:
- Moncloa.com (aviso INCIBE-CERT) | https://www.moncloa.com/2026/10/24/incibe-cert-fortinet-actualizaciones-seguridad-3454396
- INCIBE-CERT, avisos de alerta temprana | https://www.incibe.es/incibe-cert/alerta-temprana/avisos
titulo_en: If your business uses Fortinet, update now
entradilla_en: INCIBE-CERT has given its highest severity rating to a batch of Fortinet patches for FortiOS, FortiManager, FortiAnalyzer, FortiMail and FortiAuthenticator.
---
El aviso, publicado el viernes, tiene la puntuación más alta de INCIBE-CERT (crítica). Fortinet ha corregido varios fallos críticos y altos en FortiOS (ramas 7.2 a 8.0), FortiManager, FortiAnalyzer, FortiMail y FortiAuthenticator. Los detalles técnicos y los identificadores CVE no saldrán hasta el 10 de noviembre, así que de momento no se sabe exactamente qué permiten hacer.

Las versiones corregidas son, entre otras, FortiOS 8.0.2, 7.6.8, 7.4.13 y 7.2.14. Ojo con FortiMail 7.2: no tiene parche y hay que migrar a una rama soportada.

Qué hacer: haz copia de la configuración antes de actualizar, empieza por los equipos que dan directamente a internet, limita el acceso de administración a IP de confianza con doble factor y no dejes FortiManager expuesto. Muchos cortafuegos de pymes canarias son de esta marca, así que merece la pena revisarlo el lunes a primera hora.

[en]
The advisory, published on Friday, carries INCIBE-CERT's top (critical) rating. Fortinet has fixed several critical and high-severity flaws in FortiOS (branches 7.2 to 8.0), FortiManager, FortiAnalyzer, FortiMail and FortiAuthenticator. Technical details and CVE identifiers won't be released until 10 November, so for now it isn't known exactly what they allow an attacker to do.

Fixed versions include FortiOS 8.0.2, 7.6.8, 7.4.13 and 7.2.14. Watch out for FortiMail 7.2: there is no patch and you need to move to a supported branch.

What to do: back up your configuration before updating, start with internet-facing devices, restrict admin access to trusted IPs with two-factor authentication, and don't leave FortiManager exposed. Many small businesses in the Canaries use this brand of firewall, so it's worth checking first thing on Monday.
