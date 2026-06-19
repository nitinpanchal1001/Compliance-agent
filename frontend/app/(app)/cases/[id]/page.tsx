"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { CaseDetail, HumanReview, Violation } from "@/lib/types";
import { useAuth } from "@/lib/auth";
import { Glass, Badge, Button, Spinner, Empty } from "@/components/ui";
import { RiskGauge } from "@/components/RiskGauge";
import { SEVERITY_COLOR, TIER_COLOR, REVIEW_COLOR, STATUS_LABEL, timeAgo } from "@/lib/format";

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { me } = useAuth();
  const canReview = me?.role === "admin" || me?.role === "reviewer";

  const [c, setC] = useState<CaseDetail | null>(null);
  const [reviews, setReviews] = useState<HumanReview[]>([]);
  const [notFound, setNotFound] = useState(false);
  const poll = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async () => {
    try {
      const detail = await api<CaseDetail>(`/cases/${id}`);
      setC(detail);
      api<HumanReview[]>(`/cases/${id}/reviews`).then(setReviews).catch(() => {});
      return detail;
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) setNotFound(true);
      return null;
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // While the case is still being analyzed (status open, no report yet), poll.
  useEffect(() => {
    if (!c) return;
    const analyzing = c.status === "open" && c.report_json === null;
    if (analyzing) {
      poll.current = setTimeout(load, 2500);
      return () => {
        if (poll.current) clearTimeout(poll.current);
      };
    }
  }, [c, load]);

  if (notFound) {
    return <Empty title="Case not found" hint="It may have been deleted or belongs to another workspace." />;
  }
  if (!c) {
    return (
      <div className="grid place-items-center py-32 text-muted">
        <Spinner />
      </div>
    );
  }

  const analyzing = c.status === "open" && c.report_json === null;
  const report = (c.report_json ?? {}) as Record<string, { score?: number } & Record<string, unknown>>;
  const aiScore = (report.risk as { score?: number } | undefined)?.score;
  const reviewedCount = c.violations.filter((v) => v.review_status !== "pending").length;

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <Link href="/cases" className="fade-up inline-flex items-center gap-1 text-sm text-muted hover:text-fg">
        ← All cases
      </Link>

      {/* header */}
      <Glass strong className="fade-up flex flex-col items-center gap-6 p-6 sm:flex-row sm:items-center">
        <RiskGauge score={c.risk_score} tier={c.risk_tier} />
        <div className="flex-1 space-y-3 text-center sm:text-left">
          <div className="flex flex-wrap items-center justify-center gap-2 sm:justify-start">
            <Badge>{STATUS_LABEL[c.status]}</Badge>
            {c.risk_tier && <Badge color={TIER_COLOR[c.risk_tier]}>{c.risk_tier} risk</Badge>}
            {aiScore !== undefined && aiScore !== c.risk_score && (
              <Badge>AI score {aiScore} → adjudicated {c.risk_score}</Badge>
            )}
          </div>
          <div className="text-sm text-muted">
            {c.violation_count} violation{c.violation_count === 1 ? "" : "s"} ·{" "}
            {reviewedCount}/{c.violation_count} reviewed · opened {timeAgo(c.created_at)}
          </div>
          <div className="flex flex-wrap justify-center gap-1.5 sm:justify-start">
            {c.regulations_checked.map((r) => (
              <Badge key={r}>{r}</Badge>
            ))}
          </div>
          {canReview && !analyzing && (
            <div className="pt-1">
              <EscalateButton caseId={c.id} onDone={load} />
            </div>
          )}
        </div>
      </Glass>

      {analyzing && (
        <Glass className="fade-up flex items-center gap-3 p-5 text-sm text-muted">
          <Spinner className="h-5 w-5 text-teal" />
          Agents are analyzing this document — retrieving policies, reasoning over each
          clause, and scoring risk. This updates live.
        </Glass>
      )}

      {/* violations */}
      {!analyzing && c.violations.length === 0 ? (
        <Glass className="fade-up">
          <Empty title="No violations found" hint="This document was analyzed and came back clean." />
        </Glass>
      ) : (
        <div className="space-y-3">
          {c.violations.map((v) => (
            <ViolationCard
              key={v.id}
              v={v}
              caseId={c.id}
              canReview={canReview}
              onUpdated={(detail) => setC(detail)}
            />
          ))}
        </div>
      )}

      {/* audit trail */}
      {reviews.length > 0 && (
        <Glass className="fade-up p-5">
          <h2 className="mb-3 text-sm font-semibold text-muted">Review history</h2>
          <ul className="space-y-2.5">
            {reviews.map((r) => (
              <li key={r.id} className="flex items-start gap-3 text-sm">
                <span
                  className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
                  style={{ background: r.decision === "escalated" ? "var(--high)" : r.decision === "confirmed" ? "var(--crit)" : "var(--low)" }}
                />
                <div>
                  <span className="font-medium capitalize">{r.decision}</span>
                  {r.violation_id ? " · violation" : " · case-level"}
                  <span className="text-faint"> · {timeAgo(r.reviewed_at)}</span>
                  {r.note && <div className="text-muted">“{r.note}”</div>}
                </div>
              </li>
            ))}
          </ul>
        </Glass>
      )}
    </div>
  );
}

function ViolationCard({
  v,
  caseId,
  canReview,
  onUpdated,
}: {
  v: Violation;
  caseId: string;
  canReview: boolean;
  onUpdated: (d: CaseDetail) => void;
}) {
  const [busy, setBusy] = useState<"confirmed" | "dismissed" | null>(null);
  const color = SEVERITY_COLOR[v.severity];

  async function review(decision: "confirmed" | "dismissed") {
    setBusy(decision);
    try {
      const detail = await api<CaseDetail>(`/cases/${caseId}/violations/${v.id}/review`, {
        method: "POST",
        body: { decision },
      });
      onUpdated(detail);
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "Review failed");
    } finally {
      setBusy(null);
    }
  }

  const dimmed = v.review_status === "dismissed";

  return (
    <Glass className={`fade-up overflow-hidden transition ${dimmed ? "opacity-60" : ""}`}>
      <div className="h-1 w-full" style={{ background: `linear-gradient(90deg, ${color}, transparent)` }} />
      <div className="p-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: color, boxShadow: `0 0 10px ${color}` }} />
          <span className="font-semibold">{v.violation_type}</span>
          <Badge color={color}>{v.severity}</Badge>
          <Badge color={REVIEW_COLOR[v.review_status]}>{v.review_status}</Badge>
          <span className="ml-auto font-mono text-xs text-faint">
            {(v.confidence * 100).toFixed(0)}% confidence
          </span>
        </div>

        <div className="mt-2 font-mono text-xs text-teal">{v.policy_ref}</div>

        <blockquote
          className="mt-3 rounded-lg border-l-2 px-3 py-2 text-sm text-fg/90"
          style={{ borderColor: color, background: "var(--fill-1)" }}
        >
          “{v.doc_excerpt}”
        </blockquote>

        <p className="mt-3 text-sm text-muted">{v.reasoning}</p>

        <details className="mt-2 text-sm">
          <summary className="cursor-pointer text-xs text-faint hover:text-muted">Policy clause</summary>
          <p className="mt-2 text-muted">{v.clause_text}</p>
        </details>

        {/* confidence bar */}
        <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-[var(--line)]">
          <div className="h-full rounded-full" style={{ width: `${v.confidence * 100}%`, background: color }} />
        </div>

        {canReview && v.review_status === "pending" && (
          <div className="mt-4 flex gap-2">
            <Button variant="danger" loading={busy === "confirmed"} onClick={() => review("confirmed")} className="!py-1.5 text-xs">
              Confirm violation
            </Button>
            <Button variant="soft" loading={busy === "dismissed"} onClick={() => review("dismissed")} className="!py-1.5 text-xs">
              Dismiss (false positive)
            </Button>
          </div>
        )}
      </div>
    </Glass>
  );
}

function EscalateButton({ caseId, onDone }: { caseId: string; onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  async function escalate() {
    const note = prompt("Add a note for the escalation (optional):") ?? undefined;
    setBusy(true);
    try {
      await api(`/cases/${caseId}/escalate`, { method: "POST", body: { note } });
      onDone();
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "Escalation failed");
    } finally {
      setBusy(false);
    }
  }
  return (
    <Button variant="soft" loading={busy} onClick={escalate} className="!py-1.5 text-xs">
      Escalate for senior review
    </Button>
  );
}
