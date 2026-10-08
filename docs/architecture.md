# Arquitectura — Sprint 1

## Alcance

Este sprint establece infraestructura técnica, no capacidades cuantitativas. No hay modelos,
colectores, almacenamiento de mercado, datasets, estrategias, órdenes, API HTTP ni bases de datos.

## Capas y regla de dependencias

```text
Interfaces (CLI futura / REST futura / Scheduler futuro)
        │ compone dependencias
        ▼
Application (puertos y futuros casos de uso)
        ▼
Domain (eventos y futuros conceptos de negocio)
        ▲
Infrastructure (adaptadores reemplazables)
```

`domain` no importa ningún adaptador. `application` define contratos de salida, como `EventBus`.
`infrastructure` los implementa; hoy proporciona `LocalEventBus` y `PluginLoader`. Las interfaces
son el único lugar autorizado para conocer implementaciones concretas y construir el contenedor.

## Layout

El código Python está bajo `src/quantlab` para evitar importaciones accidentales desde el checkout.
La estructura replica las capas del charter sin convertir las carpetas de raíz en paquetes Python:

| Ubicación | Responsabilidad en Sprint 1 |
| --- | --- |
| `src/quantlab/core` | configuración, logging y contratos técnicos reutilizables |
| `src/quantlab/domain` | evento base, sin dependencias de framework o infraestructura |
| `src/quantlab/application` | puertos; todavía sin casos de uso de negocio |
| `src/quantlab/infrastructure` | adaptadores local-event-bus y filesystem-plugin-loader; contratos de carpetas para cache, database, storage, monitoring y security |
| `src/quantlab/interfaces` | composition root de la CLI técnica; REST y scheduler son marcadores |
| `plugins` | extensión instalada en el proyecto; vacía por diseño |
| `config/environments` | valores no secretos por ambiente |
| `tests` | pruebas unitarias y carpetas separadas para integración, benchmark, performance, regression y stress |

## Composición explícita

`interfaces.cli.composition.bootstrap()` crea `Settings`, configura logging y construye los
adaptadores. Las dependencias se inyectan por constructor. No hay singletons propios, service
locator ni variables globales de aplicación.

## Eventos locales

`LocalEventBus` implementa el puerto `EventBus`. La publicación es secuencial y acepta handlers
síncronos o asíncronos. Si un handler falla, el fallo se registra, se devuelve dentro de
`EventDispatchResult` y los handlers independientes restantes continúan. Esto resulta determinista
para pruebas y permite sustituirlo por un adaptador transaccional o broker sin alterar el dominio.

No ofrece todavía persistencia, reintentos, garantías de entrega, idempotencia distribuida ni
consumidores externos: esas propiedades requerirán una decisión explícita cuando exista un caso de
uso que las necesite.

## Plugins

El cargador busca recursivamente `plugin.yaml`. Cada manifiesto declara identidad, versión, tipo,
descripción, dependencias locales y un entrypoint local. El loader valida el YAML con Pydantic,
evita identificadores duplicados, exige dependencias en formato `type:name`, detecta dependencias
ausentes y ciclos, y devuelve un orden topológico determinista. También impide que el entrypoint
salga del directorio del plugin y compara la metadata del objeto cargado con la del manifiesto.
Ningún plugin de negocio está incluido aún.

## Configuración y observabilidad

Pydantic Settings carga primero `config/environments/<environment>.env`, un `.env` local opcional y
las variables `QUANTLAB_*`; las variables de entorno tienen precedencia. `QUANTLAB_ENVIRONMENT`
selecciona `development`, `testing` o `production` antes del bootstrap.

El logging usa `logging` de la biblioteca estándar: formato de texto para desarrollo y JSON para
producción. Los componentes reciben su `Logger` desde composición para evitar estado de aplicación
oculto.

## Calidad automatizada

Pytest mide cobertura de ramas sobre el paquete instalable y exige un mínimo de 85 %. GitHub Actions
ejecuta Ruff, MyPy y Pytest, conserva `coverage.xml` como artefacto y construye la imagen Docker
después de que los controles Python superen la validación.
