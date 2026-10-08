# ADR-0002: dependencias locales explícitas para plugins

- Estado: aceptada
- Fecha: 2026-10-07

## Contexto

La plataforma es plugin-first, pero un plugin puede requerir que una extensión técnica se inicialice
antes. Cargar archivos según el orden del filesystem vuelve esa relación implícita, no determinista
y difícil de diagnosticar.

## Decisión

Cada `plugin.yaml` declara sus dependencias con identificadores completos `tipo:nombre`. El loader
valida el manifiesto antes de ejecutar cualquier entrypoint y resuelve un orden topológico estable.
Falla de forma explícita ante dependencias ausentes, duplicadas o cíclicas.

Esta decisión se limita al registro de plugins del proyecto. No se instalan paquetes, no se accede a
red y no se resuelven rangos de versión dentro del loader.

## Consecuencias

- El orden de inicialización deja de depender de rutas del sistema operativo.
- Un error de composición se observa antes de ejecutar código dinámico de un plugin.
- La versión sigue siendo metadata para el registro; el versionado semántico entre plugins podrá
  añadirse posteriormente mediante una nueva decisión, sin mezclarla con discovery.
