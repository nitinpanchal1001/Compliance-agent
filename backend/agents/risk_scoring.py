"""Risk scoring agent — turns detected violations into a 0–100 score + tier.

Deterministic and auditable: every point is traceable to a violation's severity,
the model's confidence, and a per-regulation weight. The full breakdown is
returned so a report can show exactly *why* a case scored what it did.

    points(violation) = severity_weight × confidence × regulation_weight
    score             = min(100, round(Σ points))
"""

from dataclasses import dataclass, field

from agents.reasoning import DetectedViolation

# Base points per severity. Tuned so ~2–3 critical findings saturate the scale.
SEVERITY_POINTS: dict[str, float] = {
    "critical": 40.0,
    "high": 25.0,
    "medium": 12.0,
    "low": 5.0,
}

# Per-regulation multiplier; default 1.0. Bump specific regimes here if a tenant
# treats, say, PCI-DSS as higher-stakes than the baseline.
REGULATION_WEIGHTS: dict[str, float] = {}
DEFAULT_REGULATION_WEIGHT = 1.0

# score → tier thresholds (inclusive lower bound).
TIER_THRESHOLDS: list[tuple[int, str]] = [
    (75, "critical"),
    (50, "high"),
    (25, "medium"),
    (0, "low"),
]


@dataclass
class RiskAssessment:
    score: int
    tier: str
    breakdown: dict = field(default_factory=dict)


def _regulation_of(policy_ref: str) -> str:
    """'GDPR Art. 5(1)(e) — ...' → 'GDPR'."""
    return policy_ref.split(" ", 1)[0] if policy_ref else "UNKNOWN"


def _tier_for(score: int) -> str:
    for threshold, tier in TIER_THRESHOLDS:
        if score >= threshold:
            return tier
    return "low"


def assess(violations: list[DetectedViolation]) -> RiskAssessment:
    total = 0.0
    contributions: list[dict] = []
    by_severity: dict[str, int] = {}
    by_regulation: dict[str, int] = {}

    for v in violations:
        base = SEVERITY_POINTS.get(v.severity, SEVERITY_POINTS["medium"])
        regulation = _regulation_of(v.policy_ref)
        reg_weight = REGULATION_WEIGHTS.get(regulation, DEFAULT_REGULATION_WEIGHT)
        points = base * v.confidence * reg_weight
        total += points

        by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
        by_regulation[regulation] = by_regulation.get(regulation, 0) + 1
        contributions.append(
            {
                "policy_ref": v.policy_ref,
                "severity": v.severity,
                "confidence": round(v.confidence, 3),
                "regulation_weight": reg_weight,
                "points": round(points, 2),
            }
        )

    score = min(100, round(total))
    tier = _tier_for(score)

    breakdown = {
        "score": score,
        "tier": tier,
        "raw_points": round(total, 2),
        "violation_count": len(violations),
        "by_severity": by_severity,
        "by_regulation": by_regulation,
        "contributions": contributions,
        "method": (
            "deterministic: Σ(severity_weight × confidence × regulation_weight), "
            "capped at 100"
        ),
    }
    return RiskAssessment(score=score, tier=tier, breakdown=breakdown)
