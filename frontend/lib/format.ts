import type { RiskTier, Severity, CaseStatus, DocStatus, ReviewStatus } from "./types";

// Severity / tier → color token (matches CSS vars).
export const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "var(--crit)",
  high: "var(--high)",
  medium: "var(--med)",
  low: "var(--low)",
};

export const TIER_COLOR: Record<RiskTier, string> = SEVERITY_COLOR;

// Risk score (0–100) → a gradient stop color.
export function scoreColor(score: number): string {
  if (score >= 75) return "var(--crit)";
  if (score >= 50) return "var(--high)";
  if (score >= 25) return "var(--med)";
  return "var(--low)";
}

export const STATUS_LABEL: Record<CaseStatus, string> = {
  open: "Open",
  pending_review: "Pending review",
  closed: "Closed",
};

export const DOC_STATUS_COLOR: Record<DocStatus, string> = {
  pending: "var(--faint)",
  processing: "var(--blue)",
  ready: "var(--low)",
  failed: "var(--crit)",
};

export const REVIEW_COLOR: Record<ReviewStatus, string> = {
  pending: "var(--muted)",
  confirmed: "var(--crit)",
  dismissed: "var(--low)",
};

export function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  const s = Math.max(1, Math.floor((Date.now() - then) / 1000));
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

export function bytes(n: number | null): string {
  if (!n) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export function initials(name: string | null, email: string): string {
  if (name) {
    const parts = name.trim().split(/\s+/);
    return (parts[0][0] + (parts[1]?.[0] ?? "")).toUpperCase();
  }
  return email.slice(0, 2).toUpperCase();
}
