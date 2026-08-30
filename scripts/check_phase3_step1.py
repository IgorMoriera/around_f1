"""Script de verificação do Passo 3.1: Detecção de sessões pendentes."""

import os
from dotenv import load_dotenv
from f1_platform.ingestion.incremental import published_sessions, finished_sessions, pending_sessions

load_dotenv()
repo_id = os.getenv("HF_DATASET_REPO", "Igor-Moreira/f1-analytics-data")

print(f"1. Buscando sessões existentes no repositório: {repo_id}")
published = published_sessions(repo_id)
print(f"   -> Total de sessões encontradas no Hub: {len(published)}")

print("\n2. Buscando histórico de 2026 no calendário oficial FastF1...")
finished_2026 = finished_sessions(2026)
print(f"   -> Total de sessões concluídas em 2026: {len(finished_2026)}")

print("\n3. Calculando pendências de 2026 (deve ser 0 se o dataset estiver completo)...")
pending_2026 = pending_sessions(2026, repo_id)
print(f"   -> Sessões pendentes: {len(pending_2026)}")

if not pending_2026:
    print("\n✅ Passo 3.1 validado com sucesso! Slugs e detecção perfeitamente alinhados.")
else:
    print(f"\n⚠️ Foram encontradas {len(pending_2026)} divergências de slug:")
    for p in pending_2026[:15]:
        print(f"   - {p['season']} | {p['event']} | {p['session']}")
