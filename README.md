# QUANTLAB AI

Base técnica para una plataforma autónoma de investigación cuantitativa. La versión `0.1.0`
contiene exclusivamente la infraestructura transversal del Sprint 1: configuración, logging,
eventos locales, descubrimiento de plugins, calidad, documentación y automatización.

No contiene colectores, persistencia, PostgreSQL, FastAPI, datasets, modelos de IA, estrategias ni
backtesting. Esas capacidades se incorporarán en sprints posteriores mediante puertos y adaptadores.

## Inicio rápido

Requiere [uv](https://docs.astral.sh/uv/) y Python 3.14.

```powershell
uv sync --all-groups
uv run pre-commit install
uv run pytest
uv run ruff check .
uv run mypy src
```

`pytest` exige una cobertura de ramas mínima del 85 % y genera `coverage.xml` para CI.

El arranque técnico valida la composición de dependencias y escribe un evento de inicio en el log:

```powershell
uv run quantlab
```

## Configuración

El entorno se elige con `QUANTLAB_ENVIRONMENT` (`development`, `testing` o `production`). Los
valores de referencia viven en `config/environments/`; un archivo `.env` local tiene precedencia.
Los ajustes anidados siguen el formato de Pydantic Settings, por ejemplo:

```text
QUANTLAB_LOGGING__LEVEL=DEBUG
QUANTLAB_LOGGING__JSON=true
QUANTLAB_PLUGINS__DIRECTORY=plugins
```

No se deben versionar secretos. La infraestructura recibe `Settings` por inyección desde el
composition root; no mantiene configuración mutable global.

## Contenedor

```powershell
.\scripts\verify-docker.ps1 -Build -Run
```

El compose actual define sólo el proceso técnico de la aplicación y termina tras validarlo. No
inicia una base de datos ni otro servicio de infraestructura externo. Consulta la guía de
[Docker y WSL 2](docs/docker.md) para el diagnóstico paso a paso.

## Documentación

- [Arquitectura](docs/architecture.md)
- [Guía de desarrollo](docs/development.md)
- [Decisiones de arquitectura](docs/adr/)
- [Formato de plugins](docs/plugins.md)

## Estado del proyecto

Sprint 1 — infraestructura: base técnica completada y endurecida. El alcance continúa
deliberadamente limitado para conservar una arquitectura hexagonal y reemplazable antes de añadir
lógica de negocio.
