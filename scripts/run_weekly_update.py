"""Weekly automated orchestrator for incremental ingestion and HF synchronization."""
import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, login

from f1_platform.ingestion.incremental import pending_sessions
from f1_platform.ingestion.session_ingest import ingest_session
from f1_platform.utils.heartbeat import write_heartbeat

load_dotenv()

REPO_ID = os.getenv("HF_DATASET_REPO", "Igor-Moreira/f1-analytics-data")
HF_TOKEN = os.getenv("HF_TOKEN")
SEASON = int(os.getenv("SEASON", "2026"))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
OUTPUT_DIR = Path("data/f1-data")

print(f"--- INICIANDO ROTINA SEMANAL ({SEASON}) ---")
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
        api = HfApi()
        api.upload_folder(
            folder_path=str(OUTPUT_DIR),
            repo_id=REPO_ID,
            repo_type="dataset",
        )
        print("Sincronização concluída!")

# Grava o Heartbeat garantindo que sempre haverá um commit na semana
write_heartbeat(pending, ingested)
print("✅ Heartbeat gravado em data/state/last_run.json")
