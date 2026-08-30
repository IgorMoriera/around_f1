"""Common interface for every analysis class and the exporter registry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

REGISTRY: dict[str, type["BaseAnalysis"]] = {}


def register(cls: type["BaseAnalysis"]) -> type["BaseAnalysis"]:
    """Class decorator that registers analysis classes automatically."""
    if not cls.slug:
        raise ValueError(f"{cls.__name__} must define a 'slug'")
    if cls.slug in REGISTRY:
        raise ValueError(f"Duplicate slug registered: {cls.slug}")
    REGISTRY[cls.slug] = cls
    return cls


@dataclass(frozen=True)
class SessionContext:
    """Filter context for an analysis execution."""
    season: int
    event: str
    session: str
    drivers: tuple[str, ...] = field(default_factory=tuple)
    expert_mode: bool = False


class BaseAnalysis(ABC):
    slug: str = ""
    title: str = ""
    category: str = ""
    reading_guide: str = ""

    def __init__(self, context: SessionContext, repo):
        self.context = context
        self.repo = repo

    @classmethod
    def applies_to(cls, context: SessionContext) -> bool:
        """Define se a análise se aplica à sessão atual (ex: estratégia de pneus só para corrida)."""
        return True

    @abstractmethod
    def compute(self) -> dict[str, Any]:
        """Calcula os dados da análise e retorna um dicionário JSON-serializável."""

    def to_json(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "category": self.category,
            "context": self.context.__dict__,
            "reading_guide": self.reading_guide,
            "data": self.compute(),
        }