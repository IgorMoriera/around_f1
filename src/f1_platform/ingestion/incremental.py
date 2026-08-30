"""Work out which sessions exist in the calendar but not yet in our dataset.

State is derived directly from Hugging Face files against FastF1 schedule.
"""
from __future__ import annotations

import os
import re
from typing import Any
import fastf1
import pandas as pd
from huggingface_hub import HfApi

# Margem de segurança de 6h após a sessão para os dados estarem disponíveis no upstream
SETTLE_HOURS = 6

SESSION_MAP = {
    "Practice 1": "fp1",
    "Practice 2": "fp2",
    "Practice 3": "fp3",
    "Qualifying": "qualifying",
    "Race": "race",
    "Sprint": "sprint",
    "Sprint Qualifying": "sprint_qualifying",
    "Sprint Shootout": "sprint_qualifying",
}


def slugify(name: str) -> str:
    """Converte nome de evento/sessão em slug padrão snake_case."""
    s = re.sub(r"[^\w\s-]", "", str(name)).strip().lower()
    return re.sub(r"[\s-]+", "_", s)


def normalise_session(name: str) -> str:
    """Mapeia nomes de sessão do FastF1 para slugs padronizados."""
    return SESSION_MAP.get(name, slugify(name))


def published_sessions(repo_id: str) -> set[tuple[int, str, str]]:
    """Lê do Hugging Face quais sessões (season, event, session) já estão publicadas."""
    api = HfApi()
    token = os.getenv("HF_TOKEN")

    try:
        files = api.list_repo_files(repo_id, repo_type="dataset", token=token)
    except Exception as e:
        print(f"⚠️ Erro ao listar arquivos do repositório {repo_id}: {e}")
        return set()

    found = set()
    for path in files:
        parts = path.split("/")
        # Caminho: telemetry/season=2024/event=bahrain_grand_prix/session=race/data.parquet
        if len(parts) >= 4 and parts[0] == "telemetry":
            try:
                season = int(parts[1].split("=", 1)[1])
                event = parts[2].split("=", 1)[1]
                session = parts[3].split("=", 1)[1]
                found.add((season, event, session))
            except (IndexError, ValueError):
                continue
    return found


def finished_sessions(season: int) -> list[dict[str, Any]]:
    """Busca no calendário oficial do FastF1 todas as sessões já concluídas."""
    schedule = fastf1.get_event_schedule(season, include_testing=False)
    cutoff = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(hours=SETTLE_HOURS)

    out = []
    for _, ev in schedule.iterrows():
        for i in range(1, 6):
            name = ev.get(f"Session{i}")
            date = ev.get(f"Session{i}DateUtc")

            if not name or pd.isna(date) or date > cutoff:
                continue

            out.append({
                "season": season,
                "round": int(ev["RoundNumber"]),
                "event_name": ev["EventName"],
                "event": slugify(ev["EventName"]),
                "session_name": name,
                "session": normalise_session(name),
                "date": date,
            })
    return out


def pending_sessions(season: int, repo_id: str) -> list[dict[str, Any]]:
    """Calcula a diferença: sessões finalizadas na pista menos as já salvas no Hub."""
    have = published_sessions(repo_id)
    all_finished = finished_sessions(season)

    return [
        s for s in all_finished
        if (s["season"], s["event"], s["session"]) not in have
    ]
