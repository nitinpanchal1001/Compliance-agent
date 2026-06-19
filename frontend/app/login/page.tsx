"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { Button, Glass } from "@/components/ui";
import { Scales } from "@/components/Nav";

export default function LoginPage() {
  const { login } = useAuth();
  const [mode, setMode] = useState<"signin" | "create">("signin");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // shared
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // create-org
  const [org, setOrg] = useState("");
  const [name, setName] = useState("");

  function slugify(s: string) {
    return s.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "create") {
        await api("/tenants", {
          method: "POST",
          auth: false,
          body: {
            name: org,
            slug: slugify(org),
            admin_email: email,
            admin_password: password,
            admin_full_name: name || null,
          },
        });
      }
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center px-4">
      <div className="w-full max-w-md fade-up">
        <div className="mb-8 flex flex-col items-center gap-4 text-center">
          <span className="grid h-16 w-16 place-items-center rounded-2xl bg-[linear-gradient(140deg,var(--teal),var(--violet))] shadow-[var(--shadow-lg)]">
            <Scales size={32} width={1.6} />
          </span>
          <div>
            <h1 className="font-display text-5xl leading-none">
              Themis<span className="text-teal">.</span>
            </h1>
            <p className="mt-2.5 text-sm text-muted">
              Autonomous compliance intelligence
            </p>
          </div>
        </div>

        <Glass strong className="p-6">
          <div className="mb-5 flex rounded-xl bg-[var(--fill-1)] p-1 text-sm">
            {(["signin", "create"] as const).map((m) => (
              <button
                key={m}
                onClick={() => {
                  setMode(m);
                  setError(null);
                }}
                className={`flex-1 rounded-lg px-3 py-1.5 transition ${
                  mode === m ? "glass text-fg" : "text-muted hover:text-fg"
                }`}
              >
                {m === "signin" ? "Sign in" : "Create organization"}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="flex flex-col gap-3">
            {mode === "create" && (
              <>
                <Field label="Organization name" value={org} onChange={setOrg} placeholder="Acme Legal LLP" required />
                <Field label="Your name" value={name} onChange={setName} placeholder="Jane Reviewer" />
              </>
            )}
            <Field label="Email" type="email" value={email} onChange={setEmail} placeholder="you@company.com" required />
            <Field label="Password" type="password" value={password} onChange={setPassword} placeholder="••••••••" required />

            {error && (
              <div className="rounded-lg border border-[color-mix(in_srgb,var(--crit)_35%,transparent)] bg-[color-mix(in_srgb,var(--crit)_12%,transparent)] px-3 py-2 text-sm text-crit">
                {error}
              </div>
            )}

            <Button type="submit" loading={busy} className="mt-1 w-full">
              {mode === "signin" ? "Sign in" : "Create & enter"}
            </Button>
          </form>
        </Glass>

        <p className="mt-5 text-center text-xs text-faint">
          {mode === "signin"
            ? "First time here? Create an organization to get started."
            : "You'll be the admin of this workspace."}
        </p>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted">{label}</span>
      <input
        type={type}
        value={value}
        required={required}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] px-3.5 py-2.5 text-sm text-fg outline-none transition placeholder:text-faint focus:border-[rgba(139,92,246,0.6)] focus:ring-2 focus:ring-[rgba(139,92,246,0.25)]"
      />
    </label>
  );
}
