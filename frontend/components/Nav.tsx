"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";
import { initials } from "@/lib/format";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: IconGrid },
  { href: "/documents", label: "Documents", icon: IconDoc },
  { href: "/cases", label: "Cases", icon: IconShield },
  { href: "/policies", label: "Policies", icon: IconBook },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden md:flex md:w-60 shrink-0 flex-col gap-2 p-4">
      <Link href="/dashboard" className="mb-5 flex items-center gap-2.5 px-2 py-2">
        <Monogram />
        <span className="font-display text-lg tracking-tight">
          Themis<span className="text-teal">.</span>
        </span>
      </Link>

      <nav className="flex flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                active
                  ? "glass text-fg"
                  : "text-muted hover:text-fg hover:bg-[var(--fill-1)]"
              }`}
            >
              {active && (
                <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-[linear-gradient(var(--teal),var(--violet))]" />
              )}
              <Icon className={active ? "text-teal" : "text-faint group-hover:text-muted"} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto px-2">
        <div className="flex items-center gap-2 rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] px-3 py-2 text-xs text-muted">
          <span className="pulse-dot h-2 w-2 rounded-full bg-teal" />
          <span>Live · agents online</span>
        </div>
      </div>
    </aside>
  );
}

export function Topbar({ title }: { title: string }) {
  const { me, logout } = useAuth();
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-4 px-5 py-5">
      <h1 className="font-display text-2xl md:text-[1.7rem] leading-none">{title}</h1>
      <div className="flex items-center gap-2.5">
        <ThemeToggle />
        {me && (
          <div className="hidden items-center gap-2.5 rounded-full glass px-2 py-1.5 pr-3.5 sm:flex">
            <span className="grid h-7 w-7 place-items-center rounded-full bg-[linear-gradient(135deg,var(--teal),var(--violet))] text-[11px] font-semibold text-white">
              {initials(me.full_name, me.email)}
            </span>
            <div className="leading-tight">
              <div className="text-xs font-medium">{me.full_name ?? me.email}</div>
              <div className="text-[10px] uppercase tracking-[0.12em] text-faint">{me.role}</div>
            </div>
          </div>
        )}
        <button
          onClick={logout}
          className="rounded-xl px-3 py-2 text-sm text-muted transition hover:bg-[var(--fill-1)] hover:text-fg"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const dark = theme === "dark";
  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      title={dark ? "Switch to light" : "Switch to dark"}
      className="relative grid h-9 w-9 place-items-center rounded-xl border border-[var(--glass-border)] glass text-muted transition hover:text-fg"
    >
      <span className="theme-knob" style={{ transform: dark ? "rotate(0deg)" : "rotate(180deg)" }}>
        {dark ? <IconMoon /> : <IconSun />}
      </span>
    </button>
  );
}

export function Scales({ size = 17, stroke = "white", width = 1.7 }: { size?: number; stroke?: string; width?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth={width} strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 4.5v15" />
      <path d="M8.5 19.5h7" />
      <path d="M4 7.5h16" />
      <path d="M4 7.5v3.5" />
      <path d="M20 7.5v3.5" />
      <path d="M1.5 11a3 3 0 0 0 5 0" />
      <path d="M17.5 11a3 3 0 0 0 5 0" />
      <circle cx="12" cy="4.3" r="0.7" fill={stroke} stroke="none" />
    </svg>
  );
}

function Monogram() {
  return (
    <span className="grid h-8 w-8 place-items-center rounded-[10px] bg-[linear-gradient(140deg,var(--teal),var(--violet))] shadow-[var(--shadow)]">
      <Scales />
    </span>
  );
}

function IconSun() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4" />
    </svg>
  );
}
function IconMoon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
    </svg>
  );
}

// ── tiny inline icons ──
function IconGrid({ className = "" }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" />
    </svg>
  );
}
function IconDoc({ className = "" }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 3v4a1 1 0 0 0 1 1h4" /><path d="M5 3h9l5 5v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" />
    </svg>
  );
}
function IconShield({ className = "" }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 3 5 6v5c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6l-7-3Z" /><path d="m9 12 2 2 4-4" />
    </svg>
  );
}
function IconBook({ className = "" }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5Z" /><path d="M19 17H6a2 2 0 0 0-2 2" />
    </svg>
  );
}
