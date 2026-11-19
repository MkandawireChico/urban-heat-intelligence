"""Explainable screening scores; not physical cooling or health-impact estimates."""

from __future__ import annotations

from dataclasses import dataclass

from heatadapt.models import InterventionOption, PlanningArea, ScoringWeights


@dataclass(frozen=True, slots=True)
class RankedOption:
    option_id: str
    area_id: str
    intervention_type: str
    priority_score: float
    evidence_confidence: float
    lifecycle_cost: float
    component_scores: dict[str, float]


def rank_interventions(
    areas: list[PlanningArea],
    options: list[InterventionOption],
    weights: ScoringWeights = ScoringWeights(),
    *,
    maintenance_years: int = 5,
) -> list[RankedOption]:
    """Rank options using declared indicators and a transparent weighted score.

    The score is a screening index, not degrees of cooling, avoided illness, or
    causal impact. Lifecycle cost is undiscounted capital plus stated maintenance.
    """
    if maintenance_years < 0:
        raise ValueError("maintenance_years must not be negative")

    area_by_id = {area.area_id: area for area in areas}
    if len(area_by_id) != len(areas):
        raise ValueError("Planning area IDs must be unique")

    weight_total = sum((weights.heat, weights.population, weights.vulnerability, weights.feasibility, weights.co_benefit))
    ranked: list[RankedOption] = []

    for option in options:
        area = area_by_id.get(option.area_id)
        if area is None:
            raise ValueError(f"Unknown planning area: {option.area_id}")

        components = {
            "heat": area.heat_exposure * option.benefit_potential,
            "population": area.population_exposure * option.benefit_potential,
            "vulnerability": area.social_vulnerability * option.benefit_potential,
            "feasibility": option.feasibility,
            "co_benefit": option.co_benefit,
        }
        score = sum(getattr(weights, key) * value for key, value in components.items()) / weight_total
        ranked.append(
            RankedOption(
                option_id=option.option_id,
                area_id=option.area_id,
                intervention_type=option.intervention_type,
                priority_score=round(score, 6),
                evidence_confidence=area.data_confidence,
                lifecycle_cost=option.capital_cost + maintenance_years * option.annual_maintenance_cost,
                component_scores=components,
            )
        )

    return sorted(ranked, key=lambda item: (-item.priority_score, item.lifecycle_cost, item.option_id))
