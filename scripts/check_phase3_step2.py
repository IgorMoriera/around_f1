"""Script de verificação do Passo 3.2: Ingestão de uma única sessão com FastF1."""
from pathlib import Path
from f1_platform.ingestion.session_ingest import ingest_session

# Utilizamos 'Race' pois tem garantia absoluta de dados completos na API da FIA
mock_spec = {
    "season": 2024,
    "round": 1,
    "event_name": "Bahrain Grand Prix",
    "event": "bahrain_grand_prix",
    "session_name": "Race",
    "session": "race",
}

output_dir = Path("data/f1-data")

print(f"--- TESTANDO INGESTÃO FASTF1 ---")
print(f"Sessão Alvo: {mock_spec['season']} | {mock_spec['event']} | {mock_spec['session']}")

arquivos_gerados = ingest_session(mock_spec, output_dir)

if arquivos_gerados:
    print("\n✅ Ingestão concluída com sucesso!")
    print(f"Arquivos Parquet gravados no Data Lake Local:")
    for path in arquivos_gerados:
        print(f"  - {path}")
else:
    print("\n⚠️ Nenhum arquivo foi gerado. Verifique os logs de erro acima.")
