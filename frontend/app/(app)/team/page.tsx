"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Role, UserRow } from "@/lib/types";
import { Glass, Badge, Button, Spinner, Empty } from "@/components/ui";
import { initials } from "@/lib/format";

const ROLES: { value: Role; label: string; hint: string; color: string }[] = [
  { value: "admin", label: "Admin", hint: "Full access — manage team, settings, audit", color: "var(--violet)" },
  { value: "reviewer", label: "Reviewer", hint: "Upload, analyze, adjudicate violations", color: "var(--blue)" },
  { value: "viewer", label: "Viewer", hint: "Read-only access to cases and reports", color: "var(--teal)" },
];

const ROLE_META = Object.fromEntries(ROLES.map((r) => [r.value, r]));

export default function TeamPage() {
  const { me, loading } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<UserRow[] | null>(null);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    try {
      setUsers(await api<UserRow[]>("/users"));
    } catch {
      setUsers([]);
    }
  }, []);

  useEffect(() => {
    if (!loading && me && me.role !== "admin") router.replace("/dashboard");
  }, [me, loading, router]);

  useEffect(() => {
    if (me?.role === "admin") load();
  }, [me, load]);

  if (loading || me?.role !== "admin") {
    return (
      <div className="grid place-items-center py-32 text-muted">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <Glass strong className="fade-up flex flex-wrap items-center justify-between gap-3 p-6">
        <div>
          <h2 className="font-display text-xl">Team members</h2>
          <p className="mt-1 text-sm text-muted">
            Invite colleagues and control what they can do across the workspace.
          </p>
        </div>
        <Button onClick={() => setCreating(true)}>+ Invite member</Button>
      </Glass>

      <Glass className="fade-up overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4">
          <h3 className="text-sm font-semibold text-muted">Members</h3>
          {users && <span className="text-xs text-faint">{users.length} total</span>}
        </div>
        {!users ? (
          <div className="grid place-items-center py-16 text-muted">
            <Spinner />
          </div>
        ) : users.length === 0 ? (
          <Empty title="No members yet" hint="Invite your first teammate to collaborate." />
        ) : (
          <ul className="divide-y divide-[var(--line)]">
            {users.map((u) => (
              <UserRowItem
                key={u.id}
                user={u}
                isSelf={u.id === me.id}
                onChange={(updated) =>
                  setUsers((prev) => (prev ?? []).map((x) => (x.id === updated.id ? updated : x)))
                }
              />
            ))}
          </ul>
        )}
      </Glass>

      {creating && (
        <InviteModal
          onClose={() => setCreating(false)}
          onCreated={(u) => {
            setUsers((prev) => [u, ...(prev ?? [])]);
            setCreating(false);
          }}
        />
      )}
    </div>
  );
}

function UserRowItem({
  user,
  isSelf,
  onChange,
}: {
  user: UserRow;
  isSelf: boolean;
  onChange: (u: UserRow) => void;
}) {
  const [saving, setSaving] = useState(false);
  const meta = ROLE_META[user.role];

  async function patch(body: Partial<{ role: Role; is_active: boolean }>) {
    setSaving(true);
    try {
      onChange(await api<UserRow>(`/users/${user.id}`, { method: "PATCH", body }));
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "Update failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <li className={`flex items-center gap-4 px-5 py-3.5 ${user.is_active ? "" : "opacity-60"}`}>
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[linear-gradient(135deg,var(--teal),var(--violet))] text-xs font-semibold text-white">
        {initials(user.full_name, user.email)}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium">{user.full_name ?? user.email}</span>
          {isSelf && <span className="text-[10px] uppercase tracking-wider text-faint">you</span>}
        </div>
        <div className="truncate text-xs text-faint">{user.email}</div>
      </div>

      {!user.is_active && <Badge color="var(--crit)">disabled</Badge>}

      {isSelf ? (
        <Badge color={meta.color}>{meta.label}</Badge>
      ) : (
        <>
          <select
            value={user.role}
            disabled={saving}
            onChange={(e) => patch({ role: e.target.value as Role })}
            className="rounded-lg border border-[var(--glass-border)] bg-[var(--fill-1)] px-2.5 py-1.5 text-xs text-fg outline-none focus:border-[rgba(45,212,191,0.6)]"
          >
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
          <Button
            variant={user.is_active ? "ghost" : "soft"}
            loading={saving}
            onClick={() => patch({ is_active: !user.is_active })}
            className="!px-3 !py-1.5 text-xs"
          >
            {user.is_active ? "Disable" : "Enable"}
          </Button>
        </>
      )}
    </li>
  );
}

function InviteModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (u: UserRow) => void;
}) {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("viewer");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const u = await api<UserRow>("/users", {
        method: "POST",
        body: { email, password, full_name: fullName || null, role },
      });
      onCreated(u);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create user");
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <Glass strong className="fade-up w-full max-w-md p-6">
        {/* stop backdrop click from closing when interacting with the form */}
        <div onClick={(e) => e.stopPropagation()}>
          <h3 className="font-display text-lg">Invite a member</h3>
          <p className="mt-1 text-sm text-muted">
            Set a temporary password — they can change it after signing in.
          </p>

          <form onSubmit={submit} className="mt-5 space-y-3.5">
            <Field label="Full name (optional)">
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ada Lovelace"
                className={inputCls}
              />
            </Field>
            <Field label="Email">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ada@acme.com"
                className={inputCls}
              />
            </Field>
            <Field label="Temporary password">
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
                className={inputCls}
              />
            </Field>
            <Field label="Role">
              <div className="grid gap-2">
                {ROLES.map((r) => (
                  <label
                    key={r.value}
                    className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition ${
                      role === r.value
                        ? "border-[var(--line-strong)] bg-[var(--fill-1)]"
                        : "border-[var(--glass-border)] hover:bg-[var(--fill-1)]"
                    }`}
                  >
                    <input
                      type="radio"
                      name="role"
                      checked={role === r.value}
                      onChange={() => setRole(r.value)}
                      className="mt-0.5 accent-[var(--violet)]"
                    />
                    <span>
                      <span className="text-sm font-medium" style={{ color: r.color }}>
                        {r.label}
                      </span>
                      <span className="block text-xs text-faint">{r.hint}</span>
                    </span>
                  </label>
                ))}
              </div>
            </Field>

            {error && <p className="text-sm text-crit">{error}</p>}

            <div className="flex justify-end gap-2 pt-1">
              <Button type="button" variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" loading={submitting}>
                Create member
              </Button>
            </div>
          </form>
        </div>
      </Glass>
    </div>
  );
}

const inputCls =
  "w-full rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] px-4 py-2.5 text-sm outline-none placeholder:text-faint focus:border-[rgba(45,212,191,0.6)] focus:ring-2 focus:ring-[rgba(45,212,191,0.2)]";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-muted">{label}</span>
      {children}
    </label>
  );
}
