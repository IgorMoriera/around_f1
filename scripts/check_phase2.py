"""Script para testar a execução da primeira análise da Fase 2."""

import json
from f1_platform.analysis.base import REGISTRY, SessionContext
from f1_platform.storage.repository import DataRepository
import f1_platform.analysis.championship.standings

print("1. Inicializando Repositório de Dados (Uso Remoto via HF)...")
repo = DataRepository(use_remote=True)

# Define o contexto da busca: Bahrain 2024 - Race
context = SessionContext(season=2024, event="bahrain_grand_prix", session="race")

print("\n2. Classes registradas na plataforma:")
for slug in REGISTRY:
    print(f"  - {slug}")

# Instancia a classe de análise
analysis_cls = REGISTRY.get("championship_standings")
if analysis_cls:
    analysis = analysis_cls(context, repo)
    result_json = analysis.to_json()
    
    print("\n3. Resultado da Análise (JSON gerado com sucesso):")
    print(json.dumps(result_json, indent=2))
    