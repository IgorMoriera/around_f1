"""Single point of access to the Parquet Data Lake on Hugging Face or local disk."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class DataRepository:
    """Reads Hive-partitioned Parquet files using DuckDB."""

    def __init__(self, base_path: str | None = None, use_remote: bool = False):
        self.use_remote = use_remote
        self.con = duckdb.connect()

        if self.use_remote:
            repo = os.getenv("HF_DATASET_REPO") or "Igor-Moreira/f1-analytics-data"
            token = os.getenv("HF_TOKEN") or ""

            self.base = f"hf://datasets/{repo}"

            self.con.execute("INSTALL httpfs; LOAD httpfs;")
            if token:
                self.con.execute(f"""
                    CREATE SECRET IF NOT EXISTS hf_auth (
                        TYPE HUGGINGFACE,
                        TOKEN '{token}'
                    );
                """)
        else:
            self.base = str(Path(base_path or "data/f1-data").resolve())

    def _read_table(self, table_name: str) -> pd.DataFrame:
        """Lê tabelas dimensionais da raiz do Data Lake."""
        try:
            path = f"{self.base}/{table_name}/*.parquet"
            return self.con.execute(f"SELECT * FROM read_parquet('{path}')").df()
        except Exception:
            try:
                path = f"{self.base}/{table_name}/**/*.parquet"
                return self.con.execute(f"SELECT * FROM read_parquet('{path}', hive_partitioning=1)").df()
            except Exception:
                return pd.DataFrame()

    def read_session_file(self, season: int, event: str, session: str, table_name: str) -> pd.DataFrame:
        """Lê um arquivo específico de uma sessão diretamente pelo caminho exato."""
        file_path = f"{self.base}/telemetry/season={season}/event={event}/session={session}/{table_name}.parquet"
        try:
            return self.con.execute(f"SELECT * FROM read_parquet('{file_path}')").df()
        except Exception:
            return pd.DataFrame()

    @lru_cache(maxsize=16)
    def telemetry(self, season: int, event: str, session: str) -> pd.DataFrame:
        return self.read_session_file(season, event, session, "data")

    @lru_cache(maxsize=32)
    def laps(self, season: int, event: str, session: str) -> pd.DataFrame:
        return self.read_session_file(season, event, session, "laps")

    @lru_cache(maxsize=16)
    def weather(self, season: int, event: str, session: str) -> pd.DataFrame:
        return self.read_session_file(season, event, session, "weather")

    @lru_cache(maxsize=16)
    def corners(self, season: int, event: str, session: str) -> pd.DataFrame:
        return self.read_session_file(season, event, session, "corners")

    @lru_cache(maxsize=1)
    def results(self) -> pd.DataFrame:
        return self._read_table("results")

    @lru_cache(maxsize=1)
    def races(self) -> pd.DataFrame:
        return self._read_table("races")

    @lru_cache(maxsize=1)
    def drivers(self) -> pd.DataFrame:
        return self._read_table("drivers")

    @lru_cache(maxsize=1)
    def constructors(self) -> pd.DataFrame:
        return self._read_table("constructors")
