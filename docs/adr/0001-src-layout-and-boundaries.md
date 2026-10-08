# ADR-0001: layout `src` y límites hexagonales

- Estado: aceptada
- Fecha: 2026-07-30

## Contexto

QuantLab necesita crecer durante varios sprints sin que la capa de entrega o una tecnología concreta
absorba lógica de negocio. También debe evitar que tests o scripts importen por accidente el código
desde la raíz del repositorio.

## Decisión

El código instalable vivirá bajo `src/quantlab`, separado en `core`, `domain`, `application`,
`infrastructure`, `interfaces` y `shared`. Se usará un composition root explícito para cablear
adaptadores. `domain` y `application` no importarán desde `infrastructure` ni `interfaces`.

## Consecuencias

- Añadir un proveedor concreto exige implementar un puerto, no modificar el dominio.
- Los tests deben instalar o añadir `src` al path; pytest lo declara explícitamente.
- La raíz conserva carpetas operativas (`config`, `docs`, `docker`, `plugins`, etc.) sin convertirlas
  en paquetes Python.
- Habrá algo más de código de composición, a cambio de dependencias observables y reemplazables.
