"""Weekly automated orchestrator for incremental ingestion and HF synchronization."""
import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, login

from f1_platform.ingestion.incremental import pending_sessions
from f1_platform.ingestion.session_ingest import ingest_session
from f1_platform.utils.heartbeat import write_heartbeat

load_dotenv()

# 🚨 Alteração importante: uso do 'or' garante que strings vazias sejam substituídas pelo repositório real
REPO_ID = os.getenv("HF_DATASET_REPO") or "Igor-Moreira/f1-analytics-data"
HF_TOKEN = os.getenv("HF_TOKEN") or ""

# Tratamento seguro da temporada para não quebrar se vier vazio do GitHub
season_env = os.getenv("SEASON")
SEASON = int(season_env) if season_env and season_env.strip() else 2026

DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
OUTPUT_DIR = Path("data/f1-data")

print(f"--- INICIANDO ROTINA SEMANAL ({SEASON}) ---")
print(f"Buscando histórico no repositório: {REPO_ID}")

pending = pending_sessions(SEASON, REPO_ID)
print(f"Sessões pendentes localizadas: {len(pending)}")

ingested = []

if not DRY_RUN and pending:
    if HF_TOKEN:
        login(token=HF_TOKEN)

    for spec in pending:
        print(f"\n-> Ingerindo: {spec['season']} | {spec['event']} | {spec['session']}...")
        written = ingest_session(spec, OUTPUT_DIR)

        if written:
            ingested.append(spec)
            print(f"   Arquivos gerados com sucesso: {len(written)}")
        else:
            print("   ⚠️ Nenhum arquivo gerado. Sessão ignorada.")

    if ingested:
        print("\nSincronizando novos Parquets com o Hugging Face...")
        try:
            api = HfApi()
            api.upload_folder(
                folder_path=str(OUTPUT_DIR),
                repo_id=REPO_ID,
                repo_type="dataset",
            )
            print("🚀 Sincronização concluída!")
        except Exception as e:
            print(f"⚠️ Erro ao fazer upload para o Hugging Face: {e}")

# Grava o Heartbeat garantindo que sempre haverá um commit na semana
write_heartbeat(pending, ingested)
print("✅ Heartbeat gravado em data/state/last_run.json")
