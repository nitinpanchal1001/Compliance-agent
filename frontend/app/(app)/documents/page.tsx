"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Document } from "@/lib/types";
import { Glass, Badge, Button, Spinner, Empty } from "@/components/ui";
import { UploadZone } from "@/components/UploadZone";
import { DOC_STATUS_COLOR, bytes, timeAgo } from "@/lib/format";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[] | null>(null);
  const [analyzing, setAnalyzing] = useState<string | null>(null);
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
