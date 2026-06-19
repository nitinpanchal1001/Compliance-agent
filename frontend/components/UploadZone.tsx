"use client";

import { useRef, useState, DragEvent } from "react";
import { api } from "@/lib/api";
import type { Document } from "@/lib/types";
import { Spinner } from "./ui";

export function UploadZone({ onUploaded }: { onUploaded: (d: Document) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function upload(file: File) {
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const doc = await api<Document>("/documents", {
        method: "POST",
        body: form,
        isForm: true,
      });
      onUploaded(doc);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDrag(false);
    const file = e.dataTransfer.files?.[0];
    if (file) upload(file);
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`group flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border border-dashed p-10 text-center transition ${
          drag
            ? "border-teal bg-[rgba(45,212,191,0.07)] ring-glow"
            : "border-[var(--glass-border)] hover:border-[var(--line-strong)] hover:bg-[var(--fill-1)]"
        }`}
      >
        <div className="grid h-12 w-12 place-items-center rounded-full bg-[linear-gradient(135deg,var(--teal),var(--violet))] text-white shadow-[0_8px_30px_-8px_var(--violet)]">
          {busy ? <Spinner className="h-5 w-5" /> : <ArrowUp />}
        </div>
        <div>
          <div className="font-medium">
            {busy ? "Uploading…" : "Drop a document or click to browse"}
          </div>
          <div className="mt-1 text-xs text-muted">
            PDF · text · email (.eml) · Slack export (.json) · audio
          </div>
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) upload(f);
          e.target.value = "";
        }}
      />
      {error && <p className="mt-2 text-sm text-crit">{error}</p>}
    </div>
  );
}

function ArrowUp() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 19V6" /><path d="m6 11 6-6 6 6" />
    </svg>
  );
}
