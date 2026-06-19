"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AuditEntry } from "@/lib/types";
import { Glass, Badge, Button, Spinner, Empty } from "@/components/ui";
import { timeAgo } from "@/lib/format";

const PAGE = 50;

// action prefix → accent color
function actionColor(action: string): string {
  if (action.startsWith("auth")) return "var(--blue)";
  if (action.includes("delete")) return "var(--crit)";
  if (action.includes("create") || action.includes("upload")) return "var(--low)";
  if (action.includes("review") || action.includes("escalate")) return "var(--high)";
  return "var(--violet)";
}

export default function AuditPage() {
  const { me, loading } = useAuth();
  const router = useRouter();
  const [entries, setEntries] = useState<AuditEntry[] | null>(null);
  const [offset, setOffset] = useState(0);
  const [filter, setFilter] = useState("");
  const [fetching, setFetching] = useState(false);

  const load = useCallback(
    async (off: number, action: string) => {
      setFetching(true);
      try {
        const qs = new URLSearchParams({ limit: String(PAGE), offset: String(off) });
        if (action) qs.set("action", action);
        setEntries(await api<AuditEntry[]>(`/audit?${qs.toString()}`));
      } catch {
        setEntries([]);
      } finally {
        setFetching(false);
      }
    },
    []
  );

  useEffect(() => {
    if (!loading && me && me.role !== "admin") router.replace("/dashboard");
  }, [me, loading, router]);

  useEffect(() => {
    if (me?.role === "admin") load(offset, filter);
  }, [me, offset, filter, load]);

  if (loading || me?.role !== "admin") {
    return (
      <div className="grid place-items-center py-32 text-muted">
        <Spinner />
      </div>
    );
  }

  const page = Math.floor(offset / PAGE) + 1;
  const hasNext = (entries?.length ?? 0) === PAGE;

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <Glass strong className="fade-up flex flex-wrap items-center justify-between gap-3 p-6">
        <div>
          <h2 className="font-display text-xl">Audit trail</h2>
          <p className="mt-1 text-sm text-muted">
            An immutable, append-only record of every action taken in this workspace.
          </p>
        </div>
        <select
          value={filter}
          onChange={(e) => {
            setOffset(0);
            setFilter(e.target.value);
          }}
          className="rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] px-3 py-2 text-sm text-fg outline-none focus:border-[rgba(45,212,191,0.6)]"
        >
          <option value="">All actions</option>
          {ACTIONS.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
      </Glass>

      <Glass className="fade-up overflow-hidden">
        {!entries ? (
          <div className="grid place-items-center py-16 text-muted">
            <Spinner />
          </div>
        ) : entries.length === 0 ? (
          <Empty title="No audit events" hint={filter ? "No events match this filter." : "Activity will appear here as your team works."} />
        ) : (
          <ul className="divide-y divide-[var(--line)]">
            {entries.map((e) => (
              <AuditRow key={e.id} entry={e} />
            ))}
          </ul>
        )}
      </Glass>

      {entries && (entries.length > 0 || offset > 0) && (
        <div className="flex items-center justify-between text-sm text-muted">
          <span className="text-xs text-faint">Page {page}</span>
          <div className="flex gap-2">
            <Button
              variant="soft"
              disabled={offset === 0 || fetching}
              onClick={() => setOffset((o) => Math.max(0, o - PAGE))}
              className="!px-3 !py-1.5 text-xs"
            >
              ← Newer
            </Button>
            <Button
              variant="soft"
              disabled={!hasNext || fetching}
              onClick={() => setOffset((o) => o + PAGE)}
              className="!px-3 !py-1.5 text-xs"
            >
              Older →
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function AuditRow({ entry }: { entry: AuditEntry }) {
  const [open, setOpen] = useState(false);
  const color = actionColor(entry.action);
  const hasDetail = entry.extra_data && Object.keys(entry.extra_data).length > 0;

  return (
    <li className="px-5 py-3.5">
      <div className="flex items-center gap-4">
        <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full" style={{ background: color }} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-sm font-medium" style={{ color }}>
              {entry.action}
            </span>
            <Badge>{entry.entity_type}</Badge>
            {entry.entity_id && (
              <span className="font-mono text-[11px] text-faint">{entry.entity_id.slice(0, 8)}</span>
            )}
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-faint">
            <span>{new Date(entry.created_at).toLocaleString()}</span>
            <span>· {timeAgo(entry.created_at)}</span>
            {entry.ip_address && <span className="font-mono">· {entry.ip_address}</span>}
            {entry.user_id && <span className="font-mono">· user {entry.user_id.slice(0, 8)}</span>}
          </div>
        </div>
        {hasDetail && (
          <button
            onClick={() => setOpen((o) => !o)}
            className="shrink-0 rounded-lg px-2 py-1 text-xs text-faint transition hover:bg-[var(--fill-1)] hover:text-fg"
          >
            {open ? "Hide" : "Details"}
          </button>
        )}
      </div>
      {open && hasDetail && (
        <pre className="fade-up mt-3 overflow-x-auto rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] p-3 font-mono text-xs text-muted">
          {JSON.stringify(entry.extra_data, null, 2)}
        </pre>
      )}
    </li>
  );
}

const ACTIONS = [
  "auth.login",
  "tenant.create",
  "tenant.update",
  "user.create",
  "user.update",
  "document.upload",
  "document.delete",
  "case.create",
  "violation.review",
  "case.escalate",
];
