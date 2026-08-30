"""Championship Standings Analysis (Wave 1)."""
from typing import Any
import pandas as pd
from f1_platform.analysis.base import BaseAnalysis, register


@register
class ChampionshipStandingsAnalysis(BaseAnalysis):
    slug = "championship_standings"
    title = "Classificação do Campeonato de Pilotos"
    category = "championship"
    reading_guide = "Exibe a pontuação acumulada dos pilotos ao longo da temporada até a etapa selecionada."

    def compute(self) -> dict[str, Any]:
        # 1. Carrega as tabelas do repositório
        df_results = self.repo.results()
        df_sprints = self.repo.sprint_results() if hasattr(self.repo, 'sprint_results') else pd.DataFrame()
        df_races = self.repo.races()
        df_drivers = self.repo.drivers()
        df_constructors = self.repo.constructors()

        if df_results.empty or df_races.empty:
            return {"standings": []}

        # Padroniza nomes das colunas
        df_results.columns = [c.lower() for c in df_results.columns]
        df_races.columns = [c.lower() for c in df_races.columns]

        year_col = "year" if "year" in df_races.columns else "season"

        # 2. Corridas da temporada ordenadas por etapa (round)
        races_season = df_races[df_races[year_col] == self.context.season].sort_values("round").copy()
        if races_season.empty:
            return {"season": self.context.season, "standings": []}

        # 3. FILTRO DA ETAPA: Acumula apenas até a etapa do contexto (ex: Bahrein = Round 1)
        if self.context.event:
            matching_race = races_season[
                races_season["race_id"].astype(str).str.contains(self.context.event, case=False, na=False) |
                races_season["name"].str.lower().str.replace(" ", "_").str.contains(self.context.event.lower(), case=False, na=False)
            ]
            if not matching_race.empty:
                target_round = matching_race.iloc[0]["round"]
                races_season = races_season[races_season["round"] <= target_round]

        valid_race_ids = set(races_season["race_id"])

        # 4. Filtra resultados de corrida até a etapa selecionada
        df_res_filtered = df_results[df_results["race_id"].isin(valid_race_ids)].copy()

        if "position_order" in df_res_filtered.columns:
            df_res_filtered["is_win"] = df_res_filtered["position_order"] == 1
        else:
            df_res_filtered["is_win"] = pd.to_numeric(df_res_filtered["position"], errors="coerce") == 1

        # 5. Consolida pontos e vitórias das corridas principais
        standings_main = (
            df_res_filtered.groupby(["driver_id", "constructor_id"], as_index=False)
            .agg(
                points=("points", "sum"),
                wins=("is_win", "sum")
            )
        )

        # 6. Soma pontos de Corridas Sprint (se houver)
        if not df_sprints.empty:
            df_sprints.columns = [c.lower() for c in df_sprints.columns]
            df_sprints_filtered = df_sprints[df_sprints["race_id"].isin(valid_race_ids)].copy()
            if not df_sprints_filtered.empty:
                sprint_pts = (
                    df_sprints_filtered.groupby("driver_id", as_index=False)
                    .agg(sprint_points=("points", "sum"))
                )
                standings_main = standings_main.merge(sprint_pts, on="driver_id", how="left")
                standings_main["sprint_points"] = standings_main["sprint_points"].fillna(0)
                standings_main["points"] = standings_main["points"] + standings_main["sprint_points"]
                standings_main.drop(columns=["sprint_points"], inplace=True)

        # Ordena o ranking por Pontos e Vitórias
        standings = standings_main.sort_values(by=["points", "wins"], ascending=False).reset_index(drop=True)

        # 7. Adiciona dados dos Pilotos e o NÚMERO DO CARRO na corrida
        if not df_drivers.empty:
            df_drivers.columns = [c.lower() for c in df_drivers.columns]
            if "forename" in df_drivers.columns and "surname" in df_drivers.columns:
                df_drivers["driver_name"] = df_drivers["forename"] + " " + df_drivers["surname"]

            # Pega o número do carro usado na corrida (ex: '1' para o Max)
            latest_numbers = df_res_filtered.sort_values("race_id").groupby("driver_id")["number"].last().reset_index()
            latest_numbers.rename(columns={"number": "car_number"}, inplace=True)

            cols = [c for c in ["driver_id", "driver_name", "code"] if c in df_drivers.columns]
            standings = standings.merge(df_drivers[cols], on="driver_id", how="left")
            standings = standings.merge(latest_numbers, on="driver_id", how="left")

        # 8. Adiciona dados dos Construtores
        if not df_constructors.empty:
            df_constructors.columns = [c.lower() for c in df_constructors.columns]
            if "name" in df_constructors.columns:
                df_constructors.rename(columns={"name": "constructor_name"}, inplace=True)
            cols = [c for c in ["constructor_id", "constructor_name"] if c in df_constructors.columns]
            standings = standings.merge(df_constructors[cols], on="constructor_id", how="left")

        standings["position"] = range(1, len(standings) + 1)

        return {
            "season": self.context.season,
            "event": self.context.event,
            "standings": standings.to_dict(orient="records")
        }
