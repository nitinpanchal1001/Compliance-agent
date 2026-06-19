"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { NotificationConfig, TenantInfo } from "@/lib/types";
import { Glass, Badge, Button, Spinner } from "@/components/ui";

export default function SettingsPage() {
  const { me, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && me && me.role !== "admin") router.replace("/dashboard");
  }, [me, loading, router]);

  if (loading || me?.role !== "admin") {
    return (
      <div className="grid place-items-center py-32 text-muted">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <WorkspaceCard />
      <NotificationsCard />
    </div>
  );
}

// ── Workspace ──────────────────────────────────────────────

function WorkspaceCard() {
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    api<TenantInfo>("/tenants/me")
      .then((t) => {
        setTenant(t);
        setName(t.name);
      })
      .catch(() => setTenant(null));
  }, []);

  async function save() {
    setSaving(true);
    setToast(null);
    try {
      const updated = await api<TenantInfo>("/tenants/me", { method: "PATCH", body: { name } });
      setTenant(updated);
      setToast("Saved");
      setTimeout(() => setToast(null), 2000);
    } catch (e) {
      setToast(e instanceof ApiError ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  const dirty = tenant !== null && name.trim() !== tenant.name && name.trim().length > 0;

  return (
    <Glass strong className="fade-up p-6">
      <h2 className="font-display text-xl">Workspace</h2>
      <p className="mt-1 text-sm text-muted">Your organization’s identity and tenant details.</p>

      {!tenant ? (
        <div className="grid place-items-center py-10 text-muted">
          <Spinner />
        </div>
      ) : (
        <div className="mt-5 space-y-4">
          <label className="block">
            <span className="mb-1.5 block text-xs font-medium text-muted">Organization name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={inputCls}
            />
          </label>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <ReadOnly label="Slug" value={tenant.slug} mono />
            <ReadOnly label="Tenant ID" value={tenant.id} mono />
          </div>

          <div className="flex items-center gap-3">
            <Button onClick={save} loading={saving} disabled={!dirty}>
              Save changes
            </Button>
            {toast && <span className="text-sm text-muted">{toast}</span>}
          </div>
        </div>
      )}
    </Glass>
  );
}

// ── Notifications ──────────────────────────────────────────

function NotificationsCard() {
  const [config, setConfig] = useState<NotificationConfig | null>(null);
  const [enabled, setEnabled] = useState(false);
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [recipientText, setRecipientText] = useState("");
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const apply = useCallback((c: NotificationConfig) => {
    setConfig(c);
    setEnabled(c.enabled);
    setEmailEnabled(c.email_enabled);
    setRecipientText(c.email_recipients.join(", "));
  }, []);

  useEffect(() => {
    api<NotificationConfig>("/notifications/config")
      .then(apply)
      .catch(() => setConfig(null));
  }, [apply]);

  const recipients = recipientText
    .split(/[,\n]/)
    .map((s) => s.trim())
    .filter(Boolean);

  async function save() {
    setSaving(true);
    setToast(null);
    try {
      // Persisted into tenant.settings.notifications; the merge replaces the whole object.
      await api("/tenants/me", {
        method: "PATCH",
        body: {
          settings: {
            notifications: {
              enabled,
              email_enabled: emailEnabled,
              email_recipients: recipients,
              events: config?.events ?? null,
            },
          },
        },
      });
      apply(await api<NotificationConfig>("/notifications/config"));
      flash("Saved");
    } catch (e) {
      flash(e instanceof ApiError ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function sendTest() {
    setTesting(true);
    setToast(null);
    try {
      await api("/notifications/test", { method: "POST" });
      flash("Test notification enqueued — check worker logs & recipients.");
    } catch (e) {
      flash(e instanceof ApiError ? e.message : "Could not send test");
    } finally {
      setTesting(false);
    }
  }

  function flash(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  }

  return (
    <Glass className="fade-up p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-xl">Notifications</h2>
          <p className="mt-1 text-sm text-muted">
            Alert your team when high-risk cases need human review.
          </p>
        </div>
        {config &&
          (config.smtp_configured ? (
            <Badge color="var(--low)">SMTP ready</Badge>
          ) : (
            <Badge color="var(--high)">SMTP not configured</Badge>
          ))}
      </div>

      {!config ? (
        <div className="grid place-items-center py-10 text-muted">
          <Spinner />
        </div>
      ) : (
        <div className="mt-5 space-y-4">
          <Toggle
            label="Enable notifications"
            hint="Master switch for all outbound alerts."
            checked={enabled}
            onChange={setEnabled}
          />
          <Toggle
            label="Email delivery"
            hint="Send alerts to the recipients below via SMTP."
            checked={emailEnabled}
            onChange={setEmailEnabled}
            disabled={!enabled}
          />

          <label className={`block ${enabled ? "" : "opacity-50"}`}>
            <span className="mb-1.5 block text-xs font-medium text-muted">
              Recipients
              <span className="ml-1.5 font-normal text-faint">comma or newline separated</span>
            </span>
            <textarea
              value={recipientText}
              disabled={!enabled}
              onChange={(e) => setRecipientText(e.target.value)}
              rows={2}
              placeholder="risk@acme.com, compliance-lead@acme.com"
              className={inputCls + " resize-y"}
            />
            {recipients.length > 0 && (
              <span className="mt-1.5 block text-xs text-faint">
                {recipients.length} recipient{recipients.length === 1 ? "" : "s"}
              </span>
            )}
          </label>

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button onClick={save} loading={saving}>
              Save settings
            </Button>
            <Button variant="soft" onClick={sendTest} loading={testing}>
              Send test
            </Button>
            {toast && <span className="text-sm text-muted">{toast}</span>}
          </div>
        </div>
      )}
    </Glass>
  );
}

// ── Bits ───────────────────────────────────────────────────

const inputCls =
  "w-full rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] px-4 py-2.5 text-sm outline-none placeholder:text-faint focus:border-[rgba(45,212,191,0.6)] focus:ring-2 focus:ring-[rgba(45,212,191,0.2)]";

function ReadOnly({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <span className="mb-1.5 block text-xs font-medium text-muted">{label}</span>
      <div
        className={`truncate rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] px-4 py-2.5 text-sm text-faint ${
          mono ? "font-mono" : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function Toggle({
  label,
  hint,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  hint: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between gap-4 rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] px-4 py-3 ${
        disabled ? "opacity-50" : ""
      }`}
    >
      <div>
        <div className="text-sm font-medium">{label}</div>
        <div className="text-xs text-faint">{hint}</div>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className="flex h-6 w-11 shrink-0 items-center rounded-full p-0.5 transition-colors disabled:pointer-events-none"
        style={{ background: checked ? "var(--teal)" : "var(--fill-3)" }}
      >
        <span
          className="h-5 w-5 rounded-full bg-white shadow transition-transform duration-200"
          style={{ transform: checked ? "translateX(20px)" : "translateX(0)" }}
        />
      </button>
    </div>
  );
}
