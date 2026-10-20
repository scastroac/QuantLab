# Arquitectura — Sprints 1 y 2

## Alcance

QuantLab implementa una plataforma autónoma de investigación cuantitativa basada en Inteligencia Artificial y gobernada por Arquitectura Hexagonal (puertos y adaptadores), arquitectura dirigida por eventos (Event-Driven) y extensibilidad de plugins (Plugin-First).

- **Sprint 1 (Infraestructura Transversal):** Configuración por perfiles, logging estructurado (JSON/texto), bus de eventos desacoplado (`LocalEventBus`), cargador determinista de plugins (`PluginLoader`), empaquetado Docker y CI/CD con controles de calidad automatizados.
- **Sprint 2 (Plataforma de Datos de Mercado):** Ingesta multicanal (CSV, Binance REST), validación de invariantes financieras, deduplicación y detección de huecos temporales (`MarketDataCleaner`), almacenamiento relacional de series temporales en TimescaleDB, caché volátil en memoria y exportación analítica a Apache Parquet.

## Capas y regla de dependencias

```text
Interfaces (CLI / REST / Scheduler)
        │ compone dependencias
        ▼
Application (puertos, casos de uso y pipelines)
        ▼
Domain (entidades, value objects, eventos y servicios de dominio)
        ▲
Infrastructure (adaptadores reemplazables: DB, cache, collectors, storage)
```

`domain` nunca importa ningún adaptador tecnológico ni frameworks externos. `application` define contratos abstractos de entrada y salida (puertos). `infrastructure` implementa dichos puertos mediante tecnologías concretas. Las interfaces construyen el composition root y coordinan el ciclo de vida de la aplicación.

## Layout

El código fuente Python reside bajo `src/quantlab` para evitar importaciones accidentales desde el checkout:

| Ubicación | Responsabilidad |
| --- | --- |
| `src/quantlab/core` | Configuración (`Settings`), logging y contratos base de plugins (`PluginMetadata`, `Plugin`). |
| `src/quantlab/domain` | Modelos ontológicos puros: Value Objects (`Symbol`, `Interval`, `Timestamp`, `OHLCV`), Entidad `Candle`, Eventos (`DataCollected`, `DataValidated`, `DataStored`, `GapDetected`, `DataCleaned`) y Servicios de Dominio (`MarketDataCleaner`). |
| `src/quantlab/application` | Puertos de mercado (`MarketDataCollector`, `MarketDataValidator`, `MarketDataStorage`), puerto de caché (`MarketDataCache`), puerto de exportación (`MarketDataExporter`) y orquestadores (`MarketDataPipeline`). |
| `src/quantlab/infrastructure` | Adaptadores concretos: `PostgresMarketDataStorage` (TimescaleDB), `InMemoryMarketDataCache`, `ParquetMarketDataExporter`, `CsvMarketDataCollector`, `BinanceMarketDataCollector`, `LocalEventBus` y `PluginLoader`. |
| `src/quantlab/interfaces` | Puntos de entrada y composition root (`interfaces.cli.composition`). |
| `plugins` | Extensiones modulares de colectores, features, modelos, estrategias y reportes. |
| `config/environments` | Archivos de entorno desacoplados sin secretos versionados. |
| `tests` | Batería de pruebas unitarias, de integración y de límites arquitectónicos. |

## Modelo de Datos de Mercado

1. **Invariantes Financieras Universales:**
   El Value Object `OHLCV` asegura matemáticamente que los precios sean estrictamente positivos, volumen $\ge 0$, y se cumpla:
   $$\text{low} \le \min(\text{open}, \text{close}) \le \max(\text{open}, \text{close}) \le \text{high}$$
2. **Preservación de Precisión Numérica:**
   Todos los cálculos y la persistencia en base de datos utilizan `decimal.Decimal` mapeado a columnas `NUMERIC` de PostgreSQL, evitando la pérdida de precisión de punto flotante binario (`float`).
3. **Limpieza y Detección de Anomalías:**
   `MarketDataCleaner` garantiza el orden cronológico estricto, resuelve duplicados y calcula los intervalos temporales perdidos emitiendo eventos de dominio `GapDetected`.

## Persistencia y Data Lake

- **TimescaleDB:** La tabla `market_data` se particiona automáticamente como una *hypertable* indexada por tiempo y símbolo, permitiendo consultas de series temporales de alta velocidad mediante `get_candles()`.
- **Apache Parquet:** `ParquetMarketDataExporter` genera archivos columnares comprimidos de alto rendimiento para el entrenamiento vectorizado de modelos de machine learning.
- **Caché:** `InMemoryMarketDataCache` provee almacenamiento temporal en memoria con TTL para optimizar pipelines de ejecución continua.

## Calidad Automatizada

Pytest mide cobertura de ramas exigiendo un mínimo del 85 % (alcanzando actualmente más del 94 %). GitHub Actions ejecuta Ruff, MyPy estricto, Pytest, genera `coverage.xml` y verifica el contenedor Docker en cada commit o pull request.
