# Research scope and prior-art boundaries

## 1. Problem statement

Urban heat adaptation requires more than identifying hot pixels. Decision-makers must choose among interventions while facing limited budgets, uneven service provision, competing land uses, maintenance constraints, uncertain evidence, and unequal vulnerability.

The initial case study is Blantyre, Malawi. The project will test whether a transparent, spatially explicit decision workflow can help compare feasible adaptation options and show how budget choices distribute potential benefits across neighbourhoods.

## 2. Existing work and what we will not claim

The project begins with a prior-art-aware position.

- WRI's Cool Cities Lab combines urban heat-related indicators with spatial analysis of interventions such as trees, cool roofs, and shade structures.
- WRI's 2026 technical note describes an open, city-agnostic framework for mapping heat-resilient infrastructure scenarios.
- URBADAPT-HEAT describes city-level heat-risk analysis, adaptation pathways, cost-benefit analysis, vulnerability analysis, and budget portfolio optimisation.
- City-HEAT and other research already address multi-objective urban heat adaptation planning.

Therefore, none of the following is a defensible novelty claim by itself: heat mapping, NDVI/LST analysis, tree-planting scenarios, cool-roof scenarios, cost-benefit analysis, or budget optimisation.

## 3. Candidate contribution to investigate

The working research direction is **locally constrained and equity-aware adaptation planning under uncertainty**.

Potential contribution areas:

1. Local feasibility constraints: land availability, ownership or control, water access, maintenance capacity, existing infrastructure, and implementation responsibility.
2. Lifecycle affordability: installation, recurring maintenance, replacement, water, and operational costs, with local cost ranges and transparent provenance.
3. Distributional equity: compare who receives benefits and who bears costs across neighbourhoods and population groups, without hiding trade-offs inside a single opaque score.
4. Robust prioritisation: test whether preferred projects change when costs, feasibility, exposure indicators, and benefit assumptions vary.
5. Decision traceability: every recommendation should show its evidence, assumptions, missing inputs, and reason for ranking.

These are candidate contributions, not established novelty claims. A deeper literature, software, and stakeholder review is required before making a research novelty claim.

## 4. Research questions to test

- How do local implementation and maintenance constraints change the ranking of urban heat adaptation interventions?
- How stable are intervention priorities when key input data and assumptions are uncertain?
- How do alternative budget allocations distribute potential benefits across neighbourhoods with different levels of vulnerability?
- Which local data gaps most affect the reliability of intervention recommendations?

## 5. Initial study boundary

- Geography: Blantyre urban area, with the boundary to be selected and documented.
- Unit of analysis: a spatial planning unit such as neighbourhood, grid cell, or candidate intervention site. The final unit depends on data quality and stakeholder input.
- Initial intervention families: urban trees and shade, cool roofs, and selected public-space cooling measures. Each option must have explicit feasibility and maintenance requirements.
- Initial outputs: screening maps, ranked candidate locations, budget scenarios, equity summaries, uncertainty analysis, and downloadable evidence reports.

## 6. Scientific safeguards

- Land-surface temperature must not be described as air temperature or personal heat exposure.
- Remote-sensing associations must not be presented as causal intervention effects.
- A priority score is a decision aid, not an objective truth.
- Missing data must be flagged, not silently imputed into false precision.
- Costs and feasibility assumptions must be sourced, dated, and editable.
- The platform must distinguish observed data, derived indicators, modelled scenarios, and user-supplied assumptions.
- No health-risk or mortality estimates will be produced without suitable epidemiological evidence and validation.

## 7. Validation plan

1. Data validation: spatial coverage, resolution, dates, coordinate reference systems, missingness, and source licences.
2. Technical validation: reproducible processing, unit tests, spatial sanity checks, and comparison with independent sources where available.
3. Local validation: structured review with planners, environmental practitioners, community representatives, and relevant technical experts.
4. Sensitivity analysis: test how rankings change under plausible ranges for costs, feasibility, weights, and uncertain indicators.
5. Usefulness evaluation: assess whether intended users understand the outputs and whether the tool supports a real planning decision.

## 8. Go/no-go conditions

Do not present the platform as a validated city planning instrument until suitable inputs are identified, local assumptions are reviewed, uncertainty is reported, the workflow is reproducible, and intended users confirm the outputs are useful.

## 9. Prior-art references

- World Resources Institute. (2026). *Mapping scenarios and estimating the potential for heat-resilient infrastructure in cities*. https://www.wri.org/research/mapping-scenarios-and-estimating-potential-heat-resilient-infrastructure-cities
- World Resources Institute. *Cool Cities Lab: Help and methodology*. https://coolcities.wri.org/help
- Aboudrar-Méda, A., & Falchetta, G. (2026). *URBADAPT-HEAT v1.0: A scalable geospatial framework for city-level public-private adaptation infrastructure cost-benefit analysis and its urban heat risk implementation*. https://github.com/URBADAPT/URBADAPT-HEAT
- *City-Heat Equity Adaptation Tool (City-HEAT): Multi-objective optimization of environmental modifications and human heat exposure reductions for urban heat adaptation under uncertainty*. https://doi.org/10.1016/j.scs.2022.104091

This list is a starting point, not an exhaustive systematic review.
