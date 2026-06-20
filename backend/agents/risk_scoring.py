"""Risk scoring agent — turns detected violations into a 0–100 score + tier.

Deterministic and auditable. The tier is driven by the *worst credible* violation
severity present; the volume and confidence of findings only position the score
*within* that tier's band (with diminishing returns). This means many low-severity
findings can never, by sheer count, escalate a case into a higher tier — a document
with twenty medium gaps stays "medium", while a single confident critical finding is
"critical". The full breakdown is returned so a report can show exactly why a case
scored what it did.

    tier        = highest severity with a credible (confidence ≥ floor) finding
    score       = band_low + band_width × saturate(weighted evidence)
"""

import math
from dataclasses import dataclass, field

from agents.reasoning import DetectedViolation

# Severity ordering, low → high.
SEVERITY_RANK: dict[str, int] = {"low": 0, "medium": 1, "high": 2, "critical": 3}
_RANK_TO_SEVERITY = {r: s for s, r in SEVERITY_RANK.items()}

# Inclusive score range each tier occupies.
TIER_RANGE: dict[str, tuple[int, int]] = {
    "low": (1, 24),
    "medium": (25, 49),
    "high": (50, 74),
    "critical": (75, 100),
}

# How quickly the score saturates toward the top of its band as evidence
# accumulates. Smaller = saturates faster (a single finding lands higher).
BAND_SCALE: dict[str, float] = {
    "critical": 1.5,
    "high": 2.0,
    "medium": 2.5,
    "low": 3.0,
}

# Ignore findings the model is not reasonably sure about when choosing the tier,
# so a single low-confidence (possibly spurious) finding can't drive the case.
CONFIDENCE_FLOOR = 0.5

# Lower-severity findings still nudge the score up within the chosen band.
SUPPORT_WEIGHT = 0.3

# Per-regulation multiplier; default 1.0. Bump specific regimes here if a tenant
# treats, say, PCI-DSS as higher-stakes than the baseline.
REGULATION_WEIGHTS: dict[str, float] = {}
DEFAULT_REGULATION_WEIGHT = 1.0


@dataclass
class RiskAssessment:
    score: int
    tier: str
    breakdown: dict = field(default_factory=dict)


def _regulation_of(policy_ref: str) -> str:
    """'GDPR Art. 5(1)(e) — ...' → 'GDPR'."""
    return policy_ref.split(" ", 1)[0] if policy_ref else "UNKNOWN"


def assess(violations: list[DetectedViolation]) -> RiskAssessment:
    by_severity: dict[str, int] = {}
    by_regulation: dict[str, int] = {}
    contributions: list[dict] = []

    for v in violations:
        regulation = _regulation_of(v.policy_ref)
        by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
        by_regulation[regulation] = by_regulation.get(regulation, 0) + 1
        contributions.append(
            {
                "policy_ref": v.policy_ref,
                "severity": v.severity,
                "confidence": round(v.confidence, 3),
            }
        )

    if not violations:
        return RiskAssessment(
            score=0,
            tier="low",
            breakdown={
                "score": 0,
                "tier": "low",
                "peak_severity": None,
                "violation_count": 0,
                "by_severity": {},
                "by_regulation": {},
                "contributions": [],
                "method": "tier = worst credible severity; score positioned within band",
            },
        )

    # 1. Pick the tier: the highest severity that has a credible finding. Fall back
    #    to the highest severity present if nothing clears the confidence floor.
    credible = [v for v in violations if v.confidence >= CONFIDENCE_FLOOR]
    pool = credible or violations
    peak_rank = max(SEVERITY_RANK.get(v.severity, 1) for v in pool)
    peak = _RANK_TO_SEVERITY[peak_rank]
    lo, hi = TIER_RANGE[peak]

    # 2. Position within the band from confidence-weighted evidence: full weight for
    #    findings at the peak severity, partial weight for the rest. Regulation
    #    weights scale the evidence. Diminishing returns keep it inside the band.
    evidence = 0.0
    for v in pool:
        reg_weight = REGULATION_WEIGHTS.get(_regulation_of(v.policy_ref), DEFAULT_REGULATION_WEIGHT)
        at_peak = SEVERITY_RANK.get(v.severity, 1) == peak_rank
        weight = 1.0 if at_peak else SUPPORT_WEIGHT
        evidence += v.confidence * reg_weight * weight

    frac = 1.0 - math.exp(-evidence / BAND_SCALE[peak])
    score = round(lo + frac * (hi - lo))
    score = max(lo, min(hi, score))

    breakdown = {
        "score": score,
        "tier": peak,
        "peak_severity": peak,
        "raw_evidence": round(evidence, 3),
        "band": [lo, hi],
        "violation_count": len(violations),
        "by_severity": by_severity,
        "by_regulation": by_regulation,
        "contributions": contributions,
        "method": (
            "tier = worst credible severity (confidence ≥ "
            f"{CONFIDENCE_FLOOR}); score = band_low + band_width × "
            "(1 − e^(−Σ confidence·weight / scale)), so volume positions within "
            "the band but never crosses a tier"
        ),
    }
    return RiskAssessment(score=score, tier=peak, breakdown=breakdown)
