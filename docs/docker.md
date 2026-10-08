# Docker en Windows con WSL 2

## Qué contiene el Sprint 1

La imagen ejecuta exclusivamente el bootstrap técnico de QuantLab y finaliza con código `0`. No
publica puertos y no levanta PostgreSQL, Redis, FastAPI, colectores ni mensajería externa.

La imagen está fijada a Python 3.14 y uv 0.12.0. Instala dependencias desde `uv.lock`, se ejecuta
con un usuario no privilegiado (`quantlab`) y Docker Compose activa filesystem de sólo lectura,
`no-new-privileges` y un `/tmp` temporal.

## Diagnóstico paso a paso

Abre Docker Desktop y espera al estado **Engine running**. Después, desde PowerShell en la raíz del
repositorio, ejecuta:

```powershell
.\scripts\verify-docker.ps1
```

El script comprueba, en este orden:

1. Que WSL está disponible y su estado es correcto.
2. Que el cliente Docker puede comunicarse con el motor.
3. Que Docker Compose V2 está disponible.
4. Que `docker-compose.yml` es válido.

Para además reconstruir la imagen y ejecutar el smoke test:

```powershell
.\scripts\verify-docker.ps1 -Build -Run
```

También se pueden ejecutar las comprobaciones de forma individual:

```powershell
wsl --status
wsl --list --verbose
docker version
docker compose version
docker compose config --quiet
docker compose build --no-cache
docker compose run --rm quantlab
```

## Fallos frecuentes

### `docker version` no muestra la sección Server

Docker Desktop no está iniciado o su motor aún está arrancando. Ábrelo, espera a **Engine running**
y repite `docker version`. Si sigue fallando, en Docker Desktop comprueba que está seleccionado el
backend **Use the WSL 2 based engine** y reinicia Docker Desktop.

### WSL no usa versión 2

Ejecuta `wsl --list --verbose`. Para una distribución existente que figure como versión 1, ejecuta
`wsl --set-version <NombreDeDistribución> 2` en una terminal de administrador. En Docker Desktop,
activa la integración WSL para esa distribución en **Settings > Resources > WSL Integration**.

### `docker compose` no existe

Actualiza o reinstala Docker Desktop; Compose V2 viene integrado y se invoca como `docker compose`,
no como el binario heredado `docker-compose`.

### La construcción falla al descargar imágenes o paquetes

Verifica conectividad, proxy corporativo y que Docker Desktop tenga acceso a Internet. Después
reintenta `docker compose build --no-cache`. No elimines imágenes, volúmenes o datos de Docker como
primer paso de diagnóstico.

### Error de permisos o filesystem de sólo lectura al arrancar

La aplicación no necesita escritura en la imagen. Si una futura funcionalidad necesita artefactos o
datos, deberá declarar un volumen o adaptador de almacenamiento específico; no se desactivará la
protección globalmente.

## CI

GitHub Actions valida el fichero Compose, construye la imagen y arranca el bootstrap técnico con el
perfil `production`. Esto impide que un cambio de dependencias o de la imagen rompa la entrega sin
ser detectado.
