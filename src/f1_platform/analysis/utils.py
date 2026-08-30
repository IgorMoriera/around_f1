"""Shared mathematical and domain utilities for F1 analysis."""

FUEL_EFFECT_S_PER_KG = 0.03
INITIAL_FUEL_KG = {"race": 100.0, "sprint": 30.0}


def fuel_corrected_lap_time(lap_time: float, lap: int, total_laps: int, session: str = "race") -> float:
    """Calcula o tempo de volta corrigido pelo consumo de combustível.
    
    À medida que o combustível é queimado, o carro fica mais leve e ganha ~0.03s por kg.
    """
    initial = INITIAL_FUEL_KG.get(session.lower(), 0.0)
    if total_laps <= 0:
        return lap_time
    remaining_fuel = initial * (1.0 - (lap / total_laps))
    return lap_time - (remaining_fuel * FUEL_EFFECT_S_PER_KG)