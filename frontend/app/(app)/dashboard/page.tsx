"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Case, Document, Severity } from "@/lib/types";
import { Glass, Badge, Spinner, Empty } from "@/components/ui";
import { RiskGauge } from "@/components/RiskGauge";
import { SeveritySpectrum } from "@/components/SeveritySpectrum";
import { TIER_COLOR, STATUS_LABEL, timeAgo, scoreColor } from "@/lib/format";

export default function DashboardPage() {
  const [cases, setCases] = useState<Case[] | null>(null);
  const [docs, setDocs] = useState<Document[] | null>(null);

  useEffect(() => {
    api<Case[]>("/cases").then(setCases).catch(() => setCases([]));
    api<Document[]>("/documents").then(setDocs).catch(() => setDocs([]));
  }, []);

  if (!cases || !docs) {
    return (
      <div className="grid place-items-center py-32 text-muted">
        <Spinner />
      </div>
    );
  }

  const scored = cases.filter((c) => c.risk_score !== null);
  const avgRisk = scored.length
    ? Math.round(scored.reduce((s, c) => s + (c.risk_score ?? 0), 0) / scored.length)
    : 0;
  const peakRisk = scored.reduce((m, c) => Math.max(m, c.risk_score ?? 0), 0);

  const severityCounts: Partial<Record<Severity, number>> = {};
  for (const c of cases) {
    if (c.risk_tier) severityCounts[c.risk_tier] = (severityCounts[c.risk_tier] ?? 0) + 1;
  }

  const pending = cases.filter((c) => c.status === "pending_review").length;
  const critical = cases.filter((c) => c.risk_tier === "critical").length;
  const recent = [...cases].slice(0, 6);

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      {/* hero stats */}
      <div className="grid gap-5 lg:grid-cols-3">
        <Glass strong className="fade-up flex items-center justify-center p-6 lg:row-span-1">
          <RiskGauge score={scored.length ? avgRisk : null} tier={null} label="AVG RISK" />
        </Glass>

        <div className="grid grid-cols-2 gap-5 lg:col-span-2">
          <Stat label="Documents" value={docs.length} sub={`${docs.filter((d) => d.status === "ready").length} ready`} accent="var(--blue)" />
          <Stat label="Cases" value={cases.length} sub={`${pending} pending review`} accent="var(--violet)" />
          <Stat label="Critical" value={critical} sub="high-risk cases" accent="var(--crit)" />
          <Stat label="Peak risk" value={peakRisk} sub="highest scored" accent={scoreColor(peakRisk)} mono />
        </div>
      </div>

      {/* severity + recent */}
      <div className="grid gap-5 lg:grid-cols-5">
        <Glass className="fade-up p-6 lg:col-span-2">
          <SectionTitle>Risk distribution</SectionTitle>
          {cases.length ? (
            <div className="mt-5">
              <SeveritySpectrum counts={severityCounts} />
            </div>
          ) : (
            <Empty title="No cases yet" hint="Run an analysis to populate risk data." />
          )}
        </Glass>

        <Glass className="fade-up p-6 lg:col-span-3">
          <div className="flex items-center justify-between">
            <SectionTitle>Recent cases</SectionTitle>
            <Link href="/cases" className="text-xs text-teal hover:underline">
              View all →
            </Link>
          </div>
          {recent.length ? (
            <ul className="mt-3 divide-y divide-[var(--line)]">
              {recent.map((c) => (
                <li key={c.id}>
                  <Link
                    href={`/cases/${c.id}`}
                    className="flex items-center gap-3 rounded-lg px-2 py-3 transition hover:bg-[var(--fill-1)]"
                  >
                    <RiskChip score={c.risk_score} />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">
                        Case · {c.violation_count} violation{c.violation_count === 1 ? "" : "s"}
                      </div>
                      <div className="text-xs text-faint">{timeAgo(c.created_at)}</div>
                    </div>
                    {c.risk_tier && <Badge color={TIER_COLOR[c.risk_tier]}>{c.risk_tier}</Badge>}
                    <Badge>{STATUS_LABEL[c.status]}</Badge>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <Empty title="No cases yet" hint="Upload a document and run analysis to create your first case." />
          )}
        </Glass>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  sub,
  accent,
  mono,
}: {
  label: string;
  value: number;
  sub: string;
  accent: string;
  mono?: boolean;
}) {
  return (
    <Glass hover className="fade-up relative overflow-hidden p-5">
      <div
        className="absolute -right-6 -top-6 h-20 w-20 rounded-full opacity-30 blur-2xl"
        style={{ background: accent }}
      />
      <div className="text-xs uppercase tracking-wider text-faint">{label}</div>
      <div className={`mt-2 text-4xl font-semibold ${mono ? "font-mono tabular-nums" : ""}`} style={{ color: accent }}>
        {value}
      </div>
      <div className="mt-1 text-xs text-muted">{sub}</div>
    </Glass>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="text-sm font-semibold tracking-tight text-muted">{children}</h2>;
}

function RiskChip({ score }: { score: number | null }) {
  const color = score === null ? "var(--faint)" : scoreColor(score);
  return (
    <span
      className="grid h-10 w-10 shrink-0 place-items-center rounded-xl font-mono text-sm font-semibold"
      style={{ color, background: `color-mix(in srgb, ${color} 14%, transparent)`, border: `1px solid color-mix(in srgb, ${color} 30%, transparent)` }}
    >
      {score ?? "—"}
    </span>
  );
}
