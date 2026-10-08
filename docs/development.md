# Guía de desarrollo

## Requisitos

- Python 3.14, gestionado por uv
- uv instalado y disponible en `PATH`
- Docker Desktop sólo para construir o ejecutar el contenedor local

## Entorno local

```powershell
uv python install 3.14
uv sync --all-groups
uv run pre-commit install
```

Ejecuta los controles antes de entregar un cambio:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

Las pruebas generan `coverage.xml` y fallan si la cobertura de ramas baja de 85 %. El reporte se
publica como artefacto de GitHub Actions.

Para aplicar automáticamente los arreglos seguros de estilo:

```powershell
uv run ruff check . --fix
uv run ruff format .
```

## Ambientes

```powershell
$env:QUANTLAB_ENVIRONMENT = "development"
uv run quantlab
```

Los archivos dentro de `config/environments/` no contienen secretos. Para credenciales futuras se
usarán variables del entorno o un gestor de secretos; nunca deben añadirse a un manifiesto, imagen,
registro de logs o repositorio.

## Convenciones

- Python 3.14 y tipado estricto en todo código nuevo.
- Docstrings estilo Google para APIs públicas.
- Ruff aplica formato, imports y reglas de calidad.
- Todo cambio de comportamiento necesita pruebas proporcionales.
- La lógica de negocio no pertenece a FastAPI, al filesystem, a Docker ni a los adaptadores.
- Los cambios se describen con Conventional Commits cuando se creen commits.

## Contenedor

```powershell
.\scripts\verify-docker.ps1 -Build -Run
```

La imagen ejecuta el binario instalado de `quantlab` como usuario no privilegiado. No publica puertos
ni crea servicios de datos porque Sprint 1 no incluye FastAPI, PostgreSQL, Redis ni mensajería
externa. Consulta [Docker y WSL 2](docker.md) para la secuencia de diagnóstico.

GitHub Actions también valida la especificación de Compose y construye la imagen. Docker Desktop
no es un requisito para ejecutar las comprobaciones Python locales.
