"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Case, CaseStatus } from "@/lib/types";
import { Glass, Badge, Spinner, Empty } from "@/components/ui";
import { SlideTabs } from "@/components/SlideTabs";
import {
  TIER_COLOR,
  STATUS_LABEL,
  caseTitle,
  scoreColor,
  timeAgo,
  violationSummary,
} from "@/lib/format";

const TABS: { key: "all" | CaseStatus; label: string }[] = [
  { key: "all", label: "All" },
  { key: "pending_review", label: "Pending review" },
  { key: "open", label: "Open" },
  { key: "closed", label: "Closed" },
];

export default function CasesPage() {
  const [tab, setTab] = useState<"all" | CaseStatus>("all");
  const [cases, setCases] = useState<Case[] | null>(null);

  useEffect(() => {
    setCases(null);
    const q = tab === "all" ? "" : `?status=${tab}`;
    api<Case[]>(`/cases${q}`).then(setCases).catch(() => setCases([]));
  }, [tab]);

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <SlideTabs tabs={TABS} value={tab} onChange={setTab} className="fade-up" />

      {!cases ? (
        <div className="grid place-items-center py-24 text-muted">
          <Spinner />
        </div>
      ) : cases.length === 0 ? (
        <Glass className="fade-up">
          <Empty title="No cases here" hint="Analyze a ready document from the Documents tab to open a case." />
        </Glass>
      ) : (
        <div className="grid gap-3.5 sm:grid-cols-2">
          {cases.map((c) => (
            <Link key={c.id} href={`/cases/${c.id}`}>
              <Glass hover className="fade-up h-full p-5">
                <div className="flex items-start gap-4">
                  <RiskOrb score={c.risk_score} tier={c.risk_tier} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-semibold">
                      {caseTitle(c)}
                    </div>
                    <div className="mt-1 text-xs text-faint">
                      {violationSummary(c.violation_count)} · Opened {timeAgo(c.created_at)}
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-1.5">
                      <Badge>{STATUS_LABEL[c.status]}</Badge>
                      {c.risk_tier && <Badge color={TIER_COLOR[c.risk_tier]}>{c.risk_tier}</Badge>}
                      {c.regulations_checked.slice(0, 3).map((r) => (
                        <Badge key={r}>{r}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </Glass>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function RiskOrb({ score, tier }: { score: number | null; tier: string | null }) {
  const color = score === null ? "var(--faint)" : scoreColor(score);
  return (
    <div
      className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl font-mono text-lg font-semibold"
      style={{
        color,
        background: `radial-gradient(circle at 50% 30%, color-mix(in srgb, ${color} 28%, transparent), transparent 70%)`,
        border: `1px solid color-mix(in srgb, ${color} 35%, transparent)`,
        boxShadow: `0 0 22px -8px ${color}`,
      }}
      title={tier ?? undefined}
    >
      {score ?? "—"}
    </div>
  );
}
