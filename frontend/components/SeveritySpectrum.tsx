"use client";

import { useEffect, useState } from "react";
import { SEVERITY_COLOR } from "@/lib/format";
import type { Severity } from "@/lib/types";

const ORDER: Severity[] = ["critical", "high", "medium", "low"];

// Horizontal stacked spectrum + per-band counts. Bars grow on mount.
export function SeveritySpectrum({ counts }: { counts: Partial<Record<Severity, number>> }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(t);
  }, []);

  const total = ORDER.reduce((s, k) => s + (counts[k] ?? 0), 0);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-[var(--line)]">
        {ORDER.map((sev) => {
          const n = counts[sev] ?? 0;
          const pct = total ? (n / total) * 100 : 0;
          return (
            <div
              key={sev}
              style={{
                width: mounted ? `${pct}%` : "0%",
                background: SEVERITY_COLOR[sev],
                transition: "width 0.9s cubic-bezier(0.22,1,0.36,1)",
                boxShadow: pct ? `0 0 12px -2px ${SEVERITY_COLOR[sev]}` : "none",
              }}
            />
          );
        })}
      </div>
      <div className="grid grid-cols-4 gap-2">
        {ORDER.map((sev) => (
          <div key={sev} className="flex flex-col gap-1">
            <span
              className="font-mono text-xl font-semibold tabular-nums"
              style={{ color: SEVERITY_COLOR[sev] }}
            >
              {counts[sev] ?? 0}
            </span>
            <span className="text-[10px] uppercase tracking-wider text-faint">{sev}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
