"""Parquet based feature store implementation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from quantlab.application.ports.feature import FeatureStore
from quantlab.domain.entities.feature import FeatureSet
from quantlab.domain.value_objects.feature import (
    FeatureFamily,
    FeatureName,
    FeatureSeries,
    FeatureValue,
)
from quantlab.domain.value_objects.market import Interval, Symbol, Timestamp


class ParquetFeatureStore(FeatureStore):
    """Persists and retrieves computed FeatureSets as Apache Parquet files."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def _resolve_path(self, symbol: Symbol, interval: Interval) -> Path:
        normalized_symbol = symbol.name.replace("/", "_").replace("-", "_").lower()
        return self.base_dir / normalized_symbol / interval.name / "features.parquet"

    async def save(self, feature_set: FeatureSet) -> None:
        """Persist a feature set to a partitioned parquet file."""
        if len(feature_set) == 0:
            return

        target_path = self._resolve_path(feature_set.symbol, feature_set.interval)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Collect unique timestamps across all features
        timestamps: set[Timestamp] = set()
        for series in feature_set.features.values():
            for val in series.values:
                timestamps.add(val.timestamp)

        sorted_timestamps = sorted(timestamps, key=lambda t: t.value)

        # Build columnar dictionary
        data: dict[str, list[object]] = {
            "timestamp": [t.value.isoformat() for t in sorted_timestamps],
        }

        # Index each feature series by timestamp
        for name, series in feature_set.features.items():
            ts_to_val = {v.timestamp.value: str(v.value) for v in series.values}
            data[name] = [ts_to_val.get(t.value, "") for t in sorted_timestamps]

        table = pa.Table.from_pydict(data)
        pq.write_table(table, target_path)

    async def load(
        self,
        symbol: Symbol,
        interval: Interval,
        feature_names: Sequence[str] | None = None,
    ) -> FeatureSet | None:
        """Load a persisted feature set from parquet."""
        target_path = self._resolve_path(symbol, interval)
        if not target_path.exists():
            return None

        table = pq.read_table(target_path)
        col_names = table.column_names

        if "timestamp" not in col_names:
            return None

        timestamps = [
            Timestamp(datetime.fromisoformat(str(s)))
            for s in table["timestamp"].to_pylist()
        ]
        features: dict[str, FeatureSeries] = {}

        target_cols = [c for c in col_names if c != "timestamp"]
        if feature_names is not None:
            target_cols = [c for c in target_cols if c in feature_names]

        for col in target_cols:
            raw_vals = table[col].to_pylist()
            f_vals: list[FeatureValue] = []
            for t, v in zip(timestamps, raw_vals, strict=True):
                if v != "":
                    f_vals.append(FeatureValue(timestamp=t, value=Decimal(str(v))))

            family_prefix = col.split(":")[0] if ":" in col else "custom"
            try:
                family = FeatureFamily(family_prefix)
            except ValueError:
                family = FeatureFamily.CUSTOM

            features[col] = FeatureSeries(
                name=FeatureName(col),
                family=family,
                values=tuple(f_vals),
            )

        return FeatureSet(symbol=symbol, interval=interval, features=features)
