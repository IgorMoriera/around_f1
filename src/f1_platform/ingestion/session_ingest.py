"""Fetch one session from FastF1 and write it in the Parquet Data Lake layout."""
from pathlib import Path
import fastf1
import pandas as pd

CACHE = Path("data/cache")


def ingest_session(spec: dict, out_root: Path) -> list[Path]:
    CACHE.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(CACHE)

    written = []
    part = f"season={spec['season']}/event={spec['event']}/session={spec['session']}"
    session_dir = out_root / "telemetry" / part
    session_dir.mkdir(parents=True, exist_ok=True)

    # 🚨 PROTEÇÃO APRIMORADA: Captura falhas de conexão e Rate Limits logo no carregamento
    try:
        session = fastf1.get_session(spec["season"], spec["round"], spec["session_name"])
        session.load(telemetry=True, laps=True, weather=True)
        laps = session.laps.copy()
    except Exception as e:
        print(f"⚠️ Falha na API da F1 para {spec['event']} - {spec['session']}: {e}")
        return []

    if not laps.empty:
        laps_df = pd.DataFrame({
            "driver": laps["Driver"],
            "team": laps["Team"],
            "lap": laps["LapNumber"].astype("Int32"),
            "lap_time": laps["LapTime"].dt.total_seconds().astype("float32"),
            "sector_1": laps["Sector1Time"].dt.total_seconds().astype("float32"),
            "sector_2": laps["Sector2Time"].dt.total_seconds().astype("float32"),
            "sector_3": laps["Sector3Time"].dt.total_seconds().astype("float32"),
            "compound": laps["Compound"],
            "tyre_life": laps["TyreLife"].astype("Int32"),
            "stint": laps["Stint"].astype("Int32"),
            "position": laps["Position"].astype("Int32"),
            "track_status": laps["TrackStatus"].astype(str),
            "is_personal_best": laps["IsPersonalBest"].fillna(False).astype(bool),
            "is_accurate": laps["IsAccurate"].fillna(False).astype(bool),
            "event_name": spec["event_name"],
        })
        p_laps = session_dir / "laps.parquet"
        laps_df.to_parquet(p_laps, compression="snappy", index=False)
        written.append(p_laps)

    # --- 2. TELEMETRY ---
    frames = []
    for _, lap in laps.iterlaps():
        try:
            tel = lap.get_car_data().add_distance()
            tel["driver"] = lap["Driver"]
            tel["lap"] = lap["LapNumber"]
            frames.append(tel)
        except Exception:
            continue

    if frames:
        tel_df = pd.concat(frames, ignore_index=True)

        numeric_cols = {
            "Speed": "float32", "RPM": "int32", "Throttle": "float32",
            "Brake": "bool", "nGear": "int8", "Distance": "float32",
            "Time": "timedelta64[ns]", "SessionTime": "timedelta64[ns]"
        }
        for col, dtype in numeric_cols.items():
            if col in tel_df.columns:
                tel_df[col] = tel_df[col].astype(dtype)

        tel_df.columns = [c.lower() for c in tel_df.columns]
        p_tel = session_dir / "data.parquet"
        tel_df.to_parquet(p_tel, compression="snappy", index=False)
        written.append(p_tel)

    # --- 3. WEATHER ---
    if session.weather_data is not None and not session.weather_data.empty:
        weather_df = session.weather_data.copy()
        weather_df.columns = [c.lower() for c in weather_df.columns]
        p_weather = session_dir / "weather.parquet"
        weather_df.to_parquet(p_weather, compression="snappy", index=False)
        written.append(p_weather)

    return written
