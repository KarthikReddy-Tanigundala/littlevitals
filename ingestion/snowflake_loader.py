"""Reusable helper to load a pandas DataFrame into a Snowflake BRONZE table.

The Snowflake driver is imported lazily inside `get_connection`, so the pure
transformation helpers (`normalize_column`, `prepare_dataframe`) can be unit
tested with no Snowflake installed and no network.
"""

from __future__ import annotations

import logging

import pandas as pd

import config

logger = logging.getLogger(__name__)


def normalize_column(name: object) -> str:
    """Normalise a column name to Snowflake-friendly UPPER_SNAKE_CASE."""
    return (
        str(name).strip().upper()
        .replace(" ", "_").replace("-", "_").replace(".", "_")
    )


def prepare_dataframe(df: pd.DataFrame, table_name: str,
                      source: str | None = None) -> pd.DataFrame:
    """Return a copy with ingestion metadata columns and normalised names.

    Adds `_ingested_at` (UTC) and `_source`, then upper-snake-cases every column.
    The input DataFrame is never mutated.
    """
    out = df.copy()
    out["_ingested_at"] = pd.Timestamp.utcnow()
    out["_source"] = source or table_name
    out.columns = [normalize_column(c) for c in out.columns]
    return out


def get_connection():  # pragma: no cover - requires Snowflake + network
    """Open a Snowflake connection from config (driver imported lazily)."""
    import snowflake.connector

    cfg = config.SNOWFLAKE
    missing = [k for k in ("account", "user", "password") if not cfg.get(k)]
    if missing:
        raise RuntimeError(f"Missing Snowflake credentials: {', '.join(missing)}")
    return snowflake.connector.connect(
        account=cfg["account"], user=cfg["user"], password=cfg["password"],
        warehouse=cfg["warehouse"], database=cfg["database"], role=cfg["role"],
    )


def load_dataframe_to_snowflake(df: pd.DataFrame, table_name: str,
                                schema: str = "BRONZE",
                                if_exists: str = "replace") -> int:  # pragma: no cover
    """Load a DataFrame into `schema.table_name`, returning rows written."""
    prepared = prepare_dataframe(df, table_name)
    from snowflake.connector.pandas_tools import write_pandas

    conn = get_connection()
    try:
        success, _, nrows, _ = write_pandas(
            conn=conn, df=prepared, table_name=table_name.upper(), schema=schema,
            database=config.SNOWFLAKE["database"], auto_create_table=True,
            overwrite=(if_exists == "replace"),
        )
        if not success:
            raise RuntimeError(f"write_pandas failed for {schema}.{table_name}")
        logger.info("Loaded %s rows to %s.%s", nrows, schema, table_name)
        return nrows
    finally:
        conn.close()
