# ADR-0003: modelo de confianza de plugins

- Estado: aceptada
- Fecha: 2026-10-07

## Contexto

El Plugin Loader importa y ejecuta archivos Python dentro del proceso de la aplicación. Las
validaciones existentes (manifiesto, dependencias, contención de rutas, comparación de metadata)
detectan errores de composición; no aíslan código malicioso.

## Decisión

Un plugin es código de confianza del proyecto, con los mismos permisos que la aplicación:
filesystem, red y variables de entorno. Sólo se cargan plugins revisados y versionados en el
repositorio. No se cargan plugins desde cargas de usuarios, descargas, directorios temporales ni
rutas controladas por terceros.

`discover()` sólo lee y valida manifiestos; no ejecuta código de plugins. `load_all()` es el único
punto que ejecuta entrypoints.

El directorio de plugins es una decisión de despliegue: en producción forma parte de la imagen
inmutable. Quien pueda modificar `QUANTLAB_PLUGINS__DIRECTORY`, un `.env` local o el contenido de
ese directorio puede ejecutar código en el proceso, por lo que esos puntos se protegen como
cualquier otro control de ejecución.

## Consecuencias

- Los plugins pasan por revisión de código como cualquier otro módulo del proyecto.
- Los secretos futuros quedan al alcance de todo plugin cargado; no se inyectan en procesos que
  carguen plugins no aprobados.
- Si algún día se admiten plugins de terceros, será necesaria una decisión nueva (proceso aislado
  o sandbox); este loader no es un límite de seguridad.
