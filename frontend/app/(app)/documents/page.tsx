"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Document, DownloadInfo } from "@/lib/types";
import { Glass, Badge, Button, Spinner, Empty } from "@/components/ui";
import { UploadZone } from "@/components/UploadZone";
import { DOC_STATUS_COLOR, bytes, timeAgo } from "@/lib/format";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[] | null>(null);
  const [analyzing, setAnalyzing] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const { me } = useAuth();
  const canManage = me?.role === "admin" || me?.role === "reviewer";
  const router = useRouter();
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async () => {
    try {
      setDocs(await api<Document[]>("/documents"));
    } catch {
      setDocs([]);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Poll while anything is still ingesting.
  useEffect(() => {
    if (!docs) return;
    const busy = docs.some((d) => d.status === "pending" || d.status === "processing");
    if (busy) {
      timer.current = setTimeout(load, 2500);
      return () => {
        if (timer.current) clearTimeout(timer.current);
      };
    }
  }, [docs, load]);

  async function analyze(doc: Document) {
    setAnalyzing(doc.id);
    try {
      const c = await api<{ id: string }>("/cases", {
        method: "POST",
        body: { document_id: doc.id },
      });
      router.push(`/cases/${c.id}`);
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "Failed to start analysis");
      setAnalyzing(null);
    }
  }

  async function download(doc: Document) {
    setBusyId(doc.id);
    try {
      const { url } = await api<DownloadInfo>(`/documents/${doc.id}/download`);
      window.open(url, "_blank", "noopener");
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "Failed to generate download link");
    } finally {
      setBusyId(null);
    }
  }

  async function remove(doc: Document) {
    if (!confirm(`Delete “${doc.name}”? This also removes any analysis cases. This cannot be undone.`)) {
      return;
    }
    setBusyId(doc.id);
    try {
      await api(`/documents/${doc.id}`, { method: "DELETE" });
      setDocs((prev) => (prev ?? []).filter((d) => d.id !== doc.id));
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "Failed to delete document");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div className="fade-up">
        <UploadZone onUploaded={(d) => setDocs((prev) => [d, ...(prev ?? [])])} />
      </div>

      <Glass className="fade-up overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4">
          <h2 className="text-sm font-semibold text-muted">Library</h2>
          {docs && <span className="text-xs text-faint">{docs.length} documents</span>}
        </div>

        {!docs ? (
          <div className="grid place-items-center py-16 text-muted">
            <Spinner />
          </div>
        ) : docs.length === 0 ? (
          <Empty title="No documents yet" hint="Upload a contract, policy, email, or call transcript to begin." />
        ) : (
          <ul className="divide-y divide-[var(--line)]">
            {docs.map((d) => (
              <li key={d.id} className="flex items-center gap-4 px-5 py-3.5">
                <FileGlyph type={d.file_type} />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{d.name}</div>
                  <div className="text-xs text-faint">
                    {d.file_type.toUpperCase()} · {bytes(d.size_bytes)}
                    {d.page_count ? ` · ${d.page_count}p` : ""} · {timeAgo(d.created_at)}
                  </div>
                </div>
                <StatusPill status={d.status} />
                {d.status === "ready" && (
                  <Button
                    variant="soft"
                    loading={analyzing === d.id}
                    onClick={() => analyze(d)}
                    className="!px-3 !py-1.5 text-xs"
                  >
                    Analyze
                  </Button>
                )}
                <IconAction
                  label="Download original"
                  onClick={() => download(d)}
                  disabled={busyId === d.id}
                >
                  <IconDownload />
                </IconAction>
                {canManage && (
                  <IconAction
                    label="Delete document"
                    danger
                    onClick={() => remove(d)}
                    disabled={busyId === d.id}
                  >
                    <IconTrash />
                  </IconAction>
                )}
              </li>
            ))}
          </ul>
        )}
      </Glass>
    </div>
  );
}

function StatusPill({ status }: { status: Document["status"] }) {
  const color = DOC_STATUS_COLOR[status];
  const animating = status === "pending" || status === "processing";
  return (
    <Badge color={color}>
      <span
        className={`h-1.5 w-1.5 rounded-full ${animating ? "pulse-dot" : ""}`}
        style={{ background: color }}
      />
      {status}
    </Badge>
  );
}

function IconAction({
  children,
  label,
  onClick,
  disabled,
  danger,
}: {
  children: React.ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className={`grid h-8 w-8 place-items-center rounded-lg border border-transparent text-faint transition hover:border-[var(--glass-border)] hover:bg-[var(--fill-1)] disabled:opacity-40 disabled:pointer-events-none ${
        danger ? "hover:!text-crit" : "hover:text-fg"
      }`}
    >
      {children}
    </button>
  );
}

function IconDownload() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="M7 10l5 5 5-5" /><path d="M12 15V3" />
    </svg>
  );
}

function IconTrash() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 6h18" /><path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" /><path d="M10 11v6M14 11v6" />
    </svg>
  );
}

function FileGlyph({ type }: { type: Document["file_type"] }) {
  const abbr: Record<string, string> = { pdf: "PDF", email: "EML", slack: "SLK", audio: "WAV", text: "TXT", other: "DOC" };
  const tint: Record<string, string> = {
    pdf: "var(--crit)",
    email: "var(--blue)",
    slack: "var(--violet)",
    audio: "var(--high)",
    text: "var(--teal)",
    other: "var(--faint)",
  };
  const c = tint[type] ?? "var(--faint)";
  return (
    <span
      className="grid h-10 w-11 shrink-0 place-items-center rounded-lg font-mono text-[10px] font-semibold tracking-wider"
      style={{ color: c, background: `color-mix(in srgb, ${c} 12%, transparent)`, border: `1px solid color-mix(in srgb, ${c} 28%, transparent)` }}
    >
      {abbr[type] ?? "DOC"}
    </span>
  );
}
