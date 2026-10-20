# ADR-0004: persistencia de datos de mercado en TimescaleDB y exportación a Parquet

- Estado: aceptada
- Fecha: 2026-10-19

## Contexto

QuantLab requiere procesar series de datos de mercado con dos perfiles de acceso claramente diferenciados:
1. Ingesta continua, validación, deduplicación y consultas por rangos temporales específicos de instrumentos financieros.
2. Procesamiento analítico masivo, ingeniería de variables (features) y entrenamiento de modelos de Machine Learning y Deep Learning sobre millones de registros históricos.

El uso de una base de datos puramente relacional o de archivos planos aislados no satisface ambos perfiles con el rendimiento, consistencia y reproducibilidad exigidos por el Project Charter.

## Decisión

Se adopta una estrategia de almacenamiento dual desacoplada mediante Arquitectura Hexagonal:

1. **Almacenamiento transaccional de series temporales (TimescaleDB):**
   - El puerto `MarketDataStorage` abstrae la persistencia y consulta de velas (`Candle`).
   - El adaptador `PostgresMarketDataStorage` implementa este puerto utilizando PostgreSQL con la extensión TimescaleDB, transformando automáticamente la tabla `market_data` en una *hypertable* particionada por tiempo.
   - La comunicación se realiza mediante `asyncpg` asíncrono y sentencias SQL directas con columnas `NUMERIC`, mapeando directamente instancias `Decimal` de Python para garantizar precisión matemática absoluta sin conversión a punto flotante binario (`float`).

2. **Data Lake analítico de alto rendimiento (Apache Parquet):**
   - El puerto `MarketDataExporter` abstrae la exportación y serialización de series temporales.
   - El adaptador `ParquetMarketDataExporter` implementa este puerto mediante `pyarrow`, permitiendo generar archivos Parquet comprimidos, particionados y optimizados para lectura columnar vectorizada por librerías como Polars y PyTorch.

3. **Caché en memoria volátil:**
   - El puerto `MarketDataCache` y su adaptador `InMemoryMarketDataCache` proporcionan acceso inmediato de baja latencia con tiempo de vida (TTL) para evitar consultas redundantes a la base de datos durante pipelines de ejecución rápida.

## Consecuencias

- `domain` y `application` permanecen 100% agnósticos a TimescaleDB, PostgreSQL, asyncpg y PyArrow.
- La frontera hexagonal (`test_import_boundaries.py`) bloquea la importación de `asyncpg`, `pyarrow` y `httpx` fuera de la capa de infraestructura.
- Los modelos de IA y el Feature Engine pueden consumir datasets masivos directamente desde Parquet sin sobrecargar la base de datos transaccional.
- Se mantiene el soporte para sustituir o extender estos adaptadores en el futuro (ej. almacenamiento en S3, Redis, ClickHouse) sin alterar la lógica de negocio.
