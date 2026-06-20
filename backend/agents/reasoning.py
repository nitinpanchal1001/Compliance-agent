"""Reasoning agent — detects compliance violations in a document.

For each document chunk it retrieves the most relevant policy clauses (Phase 3
RAG), then asks the LLM whether the text violates any of them, returning
structured, citation-backed violations. Results are aggregated into a report.
"""

from dataclasses import dataclass, field

import structlog

from agents.policy_rag import PolicyMatch, retrieve_policies
from core import llm, vectorstore
from core.config import get_settings

settings = get_settings()
log = structlog.get_logger()

_VALID_SEVERITIES = {"critical", "high", "medium", "low"}

SYSTEM_PROMPT = (
    "You are a meticulous compliance analyst for regulated industries. "
    "You are given an excerpt from a company document and a set of candidate "
    "regulatory policy clauses. Identify ONLY genuine violations where the "
    "excerpt clearly conflicts with a specific provided clause. Be conservative: "
    "if the excerpt does not clearly violate a clause, do not report it. Never "
    "invent clauses — cite only from the provided clauses.\n\n"
    "Grade severity proportionally and reserve the top levels for genuine harm. "
    "Do NOT default to 'high' or 'critical'; most real-world gaps are 'medium' "
    "or 'low'. Use this rubric:\n"
    "- critical: direct, active exposure or unlawful handling of sensitive data "
    "with serious, likely harm — e.g. storing plaintext card numbers WITH CVV, "
    "fully unencrypted protected health information that anyone can read, "
    "transmitting sensitive data in cleartext over the public internet, or "
    "unlawful processing/transfer with no safeguards at all.\n"
    "- high: a significant control failure that materially raises risk but is "
    "not in itself live exposure of sensitive data — e.g. no access controls or "
    "MFA on a sensitive system, audit logging disabled, no breach-notification "
    "process, a missing required agreement (DPA/BAA), or weak key management.\n"
    "- medium: a partial or weakened control, or a gap where compensating "
    "controls exist — e.g. log retention shorter than required, slow handling of "
    "data-subject requests, incomplete records, lapsed key rotation, bundled "
    "consent, or an overdue review.\n"
    "- low: a minor or administrative/documentation shortfall with little direct "
    "risk — e.g. an outdated privacy notice, training cadence gaps, or a policy "
    "past its review date.\n\n"
    "Respond with a JSON object of the form:\n"
    '{"violations": [{'
    '"violation_type": "<short label>", '
    '"severity": "critical|high|medium|low", '
    '"policy_ref": "<exact citation from a provided clause>", '
    '"doc_excerpt": "<the offending sentence(s) quoted from the excerpt>", '
    '"clause_text": "<the clause text that is violated>", '
    '"reasoning": "<why this is a violation>", '
    '"confidence": <number between 0 and 1>'
    "}]}\n"
    'If there are no violations, return {"violations": []}.'
)


@dataclass
class DetectedViolation:
    violation_type: str
    severity: str
    policy_ref: str
    doc_excerpt: str
    clause_text: str
    reasoning: str
    confidence: float


@dataclass
class AnalysisResult:
    violations: list[DetectedViolation] = field(default_factory=list)
    regulations_checked: list[str] = field(default_factory=list)
    chunks_analyzed: int = 0
    report: dict = field(default_factory=dict)


def _build_user_prompt(chunk_text: str, policies: list[PolicyMatch]) -> str:
    clauses = "\n\n".join(
        f"[{i + 1}] Citation: {p.citation}\nClause: {p.text}"
        for i, p in enumerate(policies)
    )
    return (
        f"DOCUMENT EXCERPT:\n{chunk_text}\n\n"
        f"CANDIDATE POLICY CLAUSES:\n{clauses}\n\n"
        "Identify any violations of the clauses above in the excerpt."
    )


def _parse_violations(raw: dict) -> list[DetectedViolation]:
    out: list[DetectedViolation] = []
    for v in raw.get("violations", []) or []:
        if not isinstance(v, dict):
            continue
        severity = str(v.get("severity", "")).lower().strip()
        if severity not in _VALID_SEVERITIES:
            severity = "medium"
        try:
            confidence = float(v.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        policy_ref = str(v.get("policy_ref", "")).strip()
        doc_excerpt = str(v.get("doc_excerpt", "")).strip()
        if not policy_ref or not doc_excerpt:
            continue  # a violation must be grounded in a clause and an excerpt

        out.append(
            DetectedViolation(
                violation_type=str(v.get("violation_type", "Unspecified")).strip(),
                severity=severity,
                policy_ref=policy_ref,
                doc_excerpt=doc_excerpt,
                clause_text=str(v.get("clause_text", "")).strip(),
                reasoning=str(v.get("reasoning", "")).strip(),
                confidence=confidence,
            )
        )
    return out


def analyze_chunk(
    tenant_id: str,
    chunk_text: str,
    regulations: list[str] | None,
) -> tuple[list[DetectedViolation], list[str]]:
    """Analyze one chunk. Returns (violations, regulations_considered)."""
    policies = retrieve_policies(
        tenant_id=tenant_id,
        query=chunk_text,
        top_k=settings.reasoning_top_k,
        regulations=regulations,
    )
    if not policies:
        return [], []

    regs_considered = sorted({p.regulation for p in policies})
    raw = llm.chat_json(SYSTEM_PROMPT, _build_user_prompt(chunk_text, policies))
    return _parse_violations(raw), regs_considered


def analyze_document(
    tenant_id: str,
    document_id: str,
    regulations: list[str] | None = None,
) -> AnalysisResult:
    chunks = vectorstore.get_document_chunks(tenant_id, document_id)
    if not chunks:
        return AnalysisResult(report={"note": "no chunks found for document"})

    chunks = chunks[: settings.max_chunks_per_analysis]
    all_violations: list[DetectedViolation] = []
    regs_seen: set[str] = set()

    for chunk in chunks:
        violations, regs = analyze_chunk(tenant_id, chunk["text"], regulations)
        all_violations.extend(violations)
        regs_seen.update(regs)

    by_severity: dict[str, int] = {}
    for v in all_violations:
        by_severity[v.severity] = by_severity.get(v.severity, 0) + 1

    regulations_checked = sorted(regs_seen)
    report = {
        "summary": {
            "total_violations": len(all_violations),
            "by_severity": by_severity,
            "chunks_analyzed": len(chunks),
        },
        "regulations_checked": regulations_checked,
        "model": settings.litellm_reasoning_model,
    }

    log.info(
        "reasoning.complete",
        document_id=document_id,
        violations=len(all_violations),
        chunks=len(chunks),
    )
    return AnalysisResult(
        violations=all_violations,
        regulations_checked=regulations_checked,
        chunks_analyzed=len(chunks),
        report=report,
    )
