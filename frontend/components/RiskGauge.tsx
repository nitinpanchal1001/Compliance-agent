"use client";

import { useEffect, useId, useState } from "react";
import { scoreColor } from "@/lib/format";

// Animated radial gauge. A 270° arc that sweeps to the score on mount, with a
// glowing stroke whose color reflects the risk band.
export function RiskGauge({
  score,
  size = 180,
  label = "RISK SCORE",
  tier,
}: {
  score: number | null;
  size?: number;
  label?: string;
  tier?: string | null;
}) {
  const [shown, setShown] = useState(0);
  const gradientId = `gauge-grad-${useId().replaceAll(":", "")}`;
  const target = score ?? 0;

  useEffect(() => {
    const t = setTimeout(() => setShown(target), 80);
    return () => clearTimeout(t);
  }, [target]);

  const stroke = 12;
  const glowPadding = 18;
  const canvasSize = size + glowPadding * 2;
  const r = (size - stroke) / 2 - 6;
  const cx = size / 2;
  const cy = size / 2;
  const sweep = 270; // degrees
  const start = 135; // start angle (bottom-left)
  const circ = 2 * Math.PI * r;
  const arcLen = (sweep / 360) * circ;
  const offset = arcLen * (1 - shown / 100);
  const color = scoreColor(target);

  return (
    <div
      className="relative grid place-items-center"
      style={{ width: size, height: size }}
    >
      <svg
        width={canvasSize}
        height={canvasSize}
        viewBox={`${-glowPadding} ${-glowPadding} ${canvasSize} ${canvasSize}`}
        className="absolute overflow-visible"
        style={{ inset: -glowPadding }}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.5" />
            <stop offset="100%" stopColor={color} />
          </linearGradient>
        </defs>
        {/* track */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="var(--fill-2)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${arcLen} ${circ}`}
          transform={`rotate(${start} ${cx} ${cy})`}
        />
        {/* value */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${arcLen} ${circ}`}
          strokeDashoffset={offset}
          transform={`rotate(${start} ${cx} ${cy})`}
          style={{
            transition: "stroke-dashoffset 1.1s cubic-bezier(0.22,1,0.36,1)",
            filter: `drop-shadow(0 0 8px ${color})`,
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span
          className="font-mono text-4xl font-semibold tabular-nums"
          style={{ color }}
        >
          {score === null ? "—" : Math.round(shown)}
        </span>
        <span className="mt-1 text-[10px] font-medium tracking-[0.2em] text-faint">
          {label}
        </span>
        {tier && (
          <span
            className="mt-1.5 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
            style={{
              color,
              background: `color-mix(in srgb, ${color} 16%, transparent)`,
            }}
          >
            {tier}
          </span>
        )}
      </div>
    </div>
  );
}
