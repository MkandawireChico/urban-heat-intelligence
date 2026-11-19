"""Typed domain models used by the transparent screening engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlanningArea:
    """A planning unit with normalised screening indicators in the range 0..1."""

    area_id: str
    name: str
    heat_exposure: float
    population_exposure: float
    social_vulnerability: float
    data_confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.area_id.strip():
            raise ValueError("area_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        indicator_fields = (
            "heat_exposure",
            "population_exposure",
            "social_vulnerability",
            "data_confidence",
        )
        for field_name in indicator_fields:
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class InterventionOption:
    """A candidate intervention with an assumed, not measured, benefit potential."""

    option_id: str
    area_id: str
    intervention_type: str
    capital_cost: float
    annual_maintenance_cost: float
    benefit_potential: float
    feasibility: float
    co_benefit: float = 0.0

    def __post_init__(self) -> None:
        if not self.option_id.strip() or not self.area_id.strip():
            raise ValueError("option_id and area_id must not be empty")
        if not self.intervention_type.strip():
            raise ValueError("intervention_type must not be empty")
        for field_name in ("capital_cost", "annual_maintenance_cost"):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must not be negative")
        for field_name in ("benefit_potential", "feasibility", "co_benefit"):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class ScoringWeights:
    """Weights for user-configurable screening priorities."""

    heat: float = 0.30
    population: float = 0.20
    vulnerability: float = 0.25
    feasibility: float = 0.15
    co_benefit: float = 0.10

    def __post_init__(self) -> None:
        values = (self.heat, self.population, self.vulnerability, self.feasibility, self.co_benefit)
        if any(value < 0 for value in values):
            raise ValueError("Scoring weights must not be negative")
        if sum(values) <= 0:
            raise ValueError("At least one scoring weight must be positive")
