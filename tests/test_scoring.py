import pytest

from heatadapt.models import InterventionOption, PlanningArea, ScoringWeights
from heatadapt.scoring import rank_interventions


def test_higher_exposure_and_vulnerability_raise_priority() -> None:
    areas = [
        PlanningArea("a", "Area A", 0.9, 0.8, 0.9),
        PlanningArea("b", "Area B", 0.3, 0.4, 0.2),
    ]
    options = [
        InterventionOption("opt-a", "a", "shade", 100, 10, 0.8, 0.8),
        InterventionOption("opt-b", "b", "shade", 100, 10, 0.8, 0.8),
    ]
    result = rank_interventions(areas, options)
    assert result[0].option_id == "opt-a"
    assert result[0].priority_score > result[1].priority_score


def test_lifecycle_cost_includes_maintenance_assumption() -> None:
    area = PlanningArea("a", "Area A", 0.8, 0.8, 0.8)
    option = InterventionOption("opt-a", "a", "trees", 500, 20, 0.7, 0.9)
    result = rank_interventions([area], [option], maintenance_years=4)
    assert result[0].lifecycle_cost == 580


def test_unknown_area_is_rejected() -> None:
    option = InterventionOption("opt-a", "missing", "trees", 500, 20, 0.7, 0.9)
    with pytest.raises(ValueError, match="Unknown planning area"):
        rank_interventions([], [option])


def test_invalid_indicator_is_rejected() -> None:
    with pytest.raises(ValueError, match="heat_exposure"):
        PlanningArea("a", "Area A", 1.2, 0.8, 0.8)


def test_weights_must_have_positive_total() -> None:
    with pytest.raises(ValueError, match="positive"):
        ScoringWeights(0, 0, 0, 0, 0)


def test_results_are_sorted_deterministically() -> None:
    area = PlanningArea("a", "Area A", 0.5, 0.5, 0.5)
    options = [
        InterventionOption("b", "a", "shade", 100, 0, 0.5, 0.5),
        InterventionOption("a", "a", "trees", 100, 0, 0.5, 0.5),
    ]
    result = rank_interventions([area], options)
    assert [item.option_id for item in result] == ["a", "b"]
