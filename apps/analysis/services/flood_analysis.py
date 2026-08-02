"""
Rule-based flood risk engine.

Methodology (documented for README/portfolio honesty — this is NOT a trained
ML model, it's a transparent weighted scoring system using three factors):

1. Elevation: lower elevation relative to the region baseline -> higher risk.
   Brahmaputra floodplain in this region sits roughly 45-60m; below ~50m is
   flagged as elevated risk.
2. Water coverage: higher % of the analyzed polygon covered by water bodies
   -> higher risk (more low-lying, water-adjacent land).
3. Water body intersection count: more distinct water bodies touching the
   polygon -> higher risk (more exposure edges).

Each factor contributes a 0-100 score; the final score is a weighted average.
This is intentionally simple and swappable — the architecture allows this
function to be replaced by an ML model later without touching callers.
"""

ELEVATION_LOW_THRESHOLD_M = 50.0
ELEVATION_HIGH_THRESHOLD_M = 70.0

WEIGHTS = {
    "elevation": 0.5,
    "water_coverage": 0.35,
    "water_bodies_count": 0.15,
}


def _elevation_score(mean_elevation_m: float | None) -> float:
    if mean_elevation_m is None:
        return 50.0  # unknown -> neutral/moderate contribution
    if mean_elevation_m <= ELEVATION_LOW_THRESHOLD_M:
        return 100.0
    if mean_elevation_m >= ELEVATION_HIGH_THRESHOLD_M:
        return 0.0
    # linear interpolation between thresholds
    span = ELEVATION_HIGH_THRESHOLD_M - ELEVATION_LOW_THRESHOLD_M
    return 100.0 * (ELEVATION_HIGH_THRESHOLD_M - mean_elevation_m) / span


def _water_coverage_score(water_coverage_percent: float) -> float:
    return min(water_coverage_percent * 2, 100.0)  # 50% coverage already maxes out


def _water_bodies_count_score(count: int) -> float:
    return min(count * 25, 100.0)  # 4+ intersecting water bodies maxes out


def compute_flood_risk(
    mean_elevation_m: float | None,
    water_coverage_percent: float,
    water_bodies_intersecting: int,
    has_water_data_coverage: bool = True,
) -> tuple[str, dict]:
    """
    Returns:
        (risk_level, breakdown_dict) — breakdown_dict is stored in
        Analysis.result_metadata for auditability.

    IMPORTANT: if elevation is unavailable (polygon outside the loaded DEM
    tile) AND no water body data coverage exists for this region, the system
    does NOT guess a risk level. Silently defaulting to a neutral/low score
    would present "we don't know" as "it's safe", which is a dangerous
    failure mode for a disaster-risk tool. In that case we return
    "INSUFFICIENT_DATA" instead.
    """
    if mean_elevation_m is None and not has_water_data_coverage:
        breakdown = {
            "methodology": "rule_based_weighted_v1",
            "reason": (
                "No elevation data (outside loaded DEM tile) and no water "
                "body reference data available for this region. Risk cannot "
                "be responsibly estimated."
            ),
        }
        return "INSUFFICIENT_DATA", breakdown

    elevation_score = _elevation_score(mean_elevation_m)
    water_coverage_score = _water_coverage_score(water_coverage_percent)
    water_bodies_score = _water_bodies_count_score(water_bodies_intersecting)

    final_score = (
        elevation_score * WEIGHTS["elevation"]
        + water_coverage_score * WEIGHTS["water_coverage"]
        + water_bodies_score * WEIGHTS["water_bodies_count"]
    )

    if final_score >= 66:
        risk_level = "HIGH"
    elif final_score >= 33:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    breakdown = {
        "methodology": "rule_based_weighted_v1",
        "final_score": round(final_score, 2),
        "factors": {
            "elevation_score": round(elevation_score, 2),
            "water_coverage_score": round(water_coverage_score, 2),
            "water_bodies_score": round(water_bodies_score, 2),
        },
        "weights": WEIGHTS,
    }

    return risk_level, breakdown