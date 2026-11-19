"""One query function for the app and the advisory: DuckDB on local Parquet or Athena, chosen by $SOURCE."""
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv(".env")


@lru_cache(maxsize=1)
def _duckdb():
    from tools.query_local import connect
    return connect()


def query(sql, params=()):
    """Run SQL with `?` placeholders and return a DataFrame."""
    if os.environ.get("SOURCE", "local") == "athena":
        from tools.run_athena import run
        df, _ = run(sql, list(params))
        return df.apply(lambda col: _to_number(col))
    return _duckdb().execute(sql, list(params)).df()


def _to_number(col):
    """Athena returns every value as text; turn numeric columns back into numbers."""
    import pandas as pd
    converted = pd.to_numeric(col, errors="coerce")
    return converted if converted.notna().sum() == col.notna().sum() else col
