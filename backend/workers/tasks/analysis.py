"""Case analysis task: run the reasoning agent over a document and persist results.

Case.status lifecycle here:
    open → pending_review   (violations found)
         → closed           (clean)
On failure the error is recorded in report_json and the task retries.
"""

import structlog

from agents import reasoning
from db.models.case import Case, CaseStatus
from db.models.violation import Violation, ViolationSeverity
from workers.celery_app import celery_app
from workers.db import get_sync_db

log = structlog.get_logger()


@celery_app.task(
    bind=True,
    name="workers.tasks.analysis.analyze_case",
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def analyze_case(self, case_id: str, regulations: list[str] | None = None) -> dict:
    # 1. Load case context.
    with get_sync_db() as db:
        case = db.get(Case, case_id)
        if case is None:
            log.warning("analysis.case_missing", case_id=case_id)
            return {"status": "missing", "case_id": case_id}
        tenant_id = case.tenant_id
        document_id = case.document_id
        case.status = CaseStatus.open

    try:
        # 2. Run the reasoning agent (retrieve → LLM → structured violations).
        result = reasoning.analyze_document(
            tenant_id=tenant_id,
            document_id=document_id,
            regulations=regulations,
        )

        # 3. Persist violations + report.
        with get_sync_db() as db:
            case = db.get(Case, case_id)

            # Clear any prior violations so re-running a case is idempotent.
            for old in list(case.violations):
                db.delete(old)
            db.flush()

            for v in result.violations:
                db.add(
                    Violation(
                        case_id=case_id,
                        violation_type=v.violation_type,
                        severity=ViolationSeverity(v.severity),
                        policy_ref=v.policy_ref,
                        doc_excerpt=v.doc_excerpt,
                        clause_text=v.clause_text,
                        reasoning=v.reasoning,
                        confidence=v.confidence,
                    )
                )

            case.regulations_checked = result.regulations_checked
            case.report_json = result.report
            case.status = (
                CaseStatus.pending_review if result.violations else CaseStatus.closed
            )

        log.info(
            "analysis.success",
            case_id=case_id,
            violations=len(result.violations),
        )
        return {
            "status": "analyzed",
            "case_id": case_id,
            "violations": len(result.violations),
        }

    except Exception as exc:
        log.error("analysis.failed", case_id=case_id, error=str(exc))
        with get_sync_db() as db:
            case = db.get(Case, case_id)
            if case is not None:
                case.report_json = {"error": str(exc)[:1000]}
                case.status = CaseStatus.open
        raise self.retry(exc=exc)
