"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Policy, PolicyMatch } from "@/lib/types";
import { Glass, Badge, Button, Spinner, Empty } from "@/components/ui";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<Policy[] | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PolicyMatch[] | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    api<Policy[]>("/policies").then(setPolicies).catch(() => setPolicies([]));
  }, []);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    try {
      setResults(await api<PolicyMatch[]>("/policies/search", { method: "POST", body: { query, top_k: 6 } }));
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* semantic search */}
      <Glass strong className="fade-up p-6">
        <h2 className="text-sm font-semibold text-muted">Semantic policy search</h2>
        <p className="mt-1 text-xs text-faint">
          Describe a scenario in plain language — the RAG agent finds the most relevant clauses.
        </p>
        <form onSubmit={search} className="mt-4 flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. storing credit card numbers in plaintext"
            className="flex-1 rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] px-4 py-2.5 text-sm outline-none placeholder:text-faint focus:border-[rgba(45,212,191,0.6)] focus:ring-2 focus:ring-[rgba(45,212,191,0.2)]"
          />
          <Button type="submit" loading={searching}>Search</Button>
        </form>

        {results && (
          <div className="mt-5 space-y-2.5">
            {results.length === 0 ? (
              <p className="text-sm text-muted">No matches.</p>
            ) : (
              results.map((m, i) => (
                <div key={i} className="fade-up rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] p-4">
                  <div className="flex items-center gap-2">
                    <Badge color="var(--teal)">{m.regulation}</Badge>
                    <span className="font-mono text-xs text-teal">{m.citation}</span>
                    <span className="ml-auto font-mono text-xs text-faint">{(m.score * 100).toFixed(0)}% match</span>
                  </div>
                  <p className="mt-2 text-sm text-muted">{m.text}</p>
                  <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-[var(--line)]">
                    <div className="h-full rounded-full bg-teal" style={{ width: `${Math.min(100, m.score * 100)}%` }} />
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </Glass>

      {/* corpus */}
      <div>
        <h2 className="fade-up mb-3 text-sm font-semibold text-muted">Policy corpus</h2>
        {!policies ? (
          <div className="grid place-items-center py-16 text-muted">
            <Spinner />
          </div>
        ) : policies.length === 0 ? (
          <Glass className="fade-up">
            <Empty title="No policies seeded" hint="Run `make seed-policies` on the backend to load the corpus." />
          </Glass>
        ) : (
          <div className="grid gap-3.5 sm:grid-cols-2">
            {policies.map((p) => (
              <Glass key={p.id} hover className="fade-up p-5">
                <div className="flex items-center gap-2">
                  <span className="grid h-10 w-10 place-items-center rounded-xl bg-[linear-gradient(135deg,var(--teal),var(--violet))] text-sm font-bold text-white">
                    {p.regulation.slice(0, 2)}
                  </span>
                  <div>
                    <div className="font-semibold">{p.regulation}</div>
                    <div className="text-xs text-faint">{p.jurisdiction ?? "—"}</div>
                  </div>
                  <Badge className="ml-auto">{p.scope}</Badge>
                </div>
                <div className="mt-3 text-sm text-muted">{p.title}</div>
                <div className="mt-3 flex items-center justify-between text-xs text-faint">
                  <span>{p.clause_count} clauses</span>
                  {p.source && <span className="truncate">{p.source}</span>}
                </div>
              </Glass>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
