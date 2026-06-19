"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
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

const ADMIN_NAV = [
  { href: "/team", label: "Team", icon: IconUsers },
  { href: "/audit", label: "Audit log", icon: IconScroll },
  { href: "/settings", label: "Settings", icon: IconGear },
];

// ── Collapse / mobile-drawer state, shared by Sidebar + Topbar ──

interface SidebarState {
  collapsed: boolean;
  toggleCollapsed: () => void;
  mobileOpen: boolean;
  setMobileOpen: (v: boolean) => void;
}

const SidebarCtx = createContext<SidebarState | null>(null);
const COLLAPSE_KEY = "ca_sidebar_collapsed";

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  // Restore the persisted desktop collapse preference.
  useEffect(() => {
    if (localStorage.getItem(COLLAPSE_KEY) === "1") setCollapsed(true);
  }, []);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((c) => {
      const next = !c;
      localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0");
      return next;
    });
  }, []);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // Lock background scroll while the drawer is open.
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <SidebarCtx.Provider value={{ collapsed, toggleCollapsed, mobileOpen, setMobileOpen }}>
      {children}
    </SidebarCtx.Provider>
  );
}

function useSidebar() {
  const ctx = useContext(SidebarCtx);
  if (!ctx) throw new Error("useSidebar must be used within SidebarProvider");
  return ctx;
}

export function Sidebar() {
  const { collapsed, mobileOpen, setMobileOpen } = useSidebar();

  return (
    <>
      {/* Desktop rail — collapses to an icon-only column */}
      <aside
        className={`hidden shrink-0 flex-col gap-2 overflow-hidden p-4 transition-[width] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] md:flex ${
          collapsed ? "md:w-[5.25rem]" : "md:w-60"
        }`}
      >
        <SidebarBody collapsed={collapsed} />
      </aside>

      {/* Mobile drawer + backdrop */}
      <div className="md:hidden">
        <div
          onClick={() => setMobileOpen(false)}
          aria-hidden
          className={`fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity duration-300 ${
            mobileOpen ? "opacity-100" : "pointer-events-none opacity-0"
          }`}
        />
        <aside
          className={`fixed left-0 top-0 z-50 flex h-full w-72 flex-col gap-2 overflow-y-auto p-4 glass-strong transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            mobileOpen ? "translate-x-0" : "-translate-x-full"
          }`}
          aria-hidden={!mobileOpen}
        >
          <SidebarBody collapsed={false} onNavigate={() => setMobileOpen(false)} showClose />
        </aside>
      </div>
    </>
  );
}

function SidebarBody({
  collapsed,
  onNavigate,
  showClose = false,
}: {
  collapsed: boolean;
  onNavigate?: () => void;
  showClose?: boolean;
}) {
  const pathname = usePathname();
  const { me } = useAuth();
  const { toggleCollapsed, setMobileOpen } = useSidebar();
  const isAdmin = me?.role === "admin";

  const navRef = useRef<HTMLElement>(null);
  const settled = useRef(false);
  const [pill, setPill] = useState({ top: 0, height: 0, visible: false, instant: true });

  // Slide a single highlight to whichever item is active (PS5-style).
  useEffect(() => {
    const nav = navRef.current;
    if (!nav) return;
    const active = nav.querySelector<HTMLElement>('a[data-active="true"]');
    if (active) {
      setPill({
        top: active.offsetTop,
        height: active.offsetHeight,
        visible: true,
        instant: !settled.current, // first placement snaps; later ones glide
      });
      settled.current = true;
    } else {
      setPill((p) => ({ ...p, visible: false }));
    }
  }, [pathname, isAdmin, collapsed]);

  return (
    <>
      <div className={`mb-5 flex items-center px-2 py-2 ${collapsed ? "justify-center" : "gap-2.5"}`}>
        <Link
          href="/dashboard"
          onClick={onNavigate}
          className={`flex items-center ${collapsed ? "" : "gap-2.5"}`}
        >
          <Monogram />
          {!collapsed && (
            <span className="font-display text-lg tracking-tight">
              Themis<span className="text-teal">.</span>
            </span>
          )}
        </Link>
        {showClose && (
          <button
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
            className="ml-auto grid h-9 w-9 place-items-center rounded-xl text-muted transition hover:bg-[var(--fill-1)] hover:text-fg"
          >
            <IconClose />
          </button>
        )}
      </div>

      <nav ref={navRef} className="relative flex flex-col gap-1">
        <span
          aria-hidden
          className={`nav-pill glass pointer-events-none absolute inset-x-0 z-0 rounded-xl ${
            pill.instant ? "nav-pill-instant" : ""
          }`}
          style={{
            transform: `translateY(${pill.top}px)`,
            height: pill.height,
            opacity: pill.visible ? 1 : 0,
          }}
        >
          <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-[linear-gradient(var(--teal),var(--violet))]" />
        </span>

        {NAV.map((item) => (
          <NavItem key={item.href} {...item} pathname={pathname} collapsed={collapsed} onNavigate={onNavigate} />
        ))}

        {isAdmin && (
          <>
            {!collapsed ? (
              <div className="mb-1 mt-5 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
                Workspace
              </div>
            ) : (
              <div className="mx-3 my-3 h-px bg-[var(--line)]" />
            )}
            {ADMIN_NAV.map((item) => (
              <NavItem key={item.href} {...item} pathname={pathname} collapsed={collapsed} onNavigate={onNavigate} />
            ))}
          </>
        )}
      </nav>

      <div className="mt-auto flex flex-col gap-2 px-1">
        {!collapsed && (
          <div className="flex items-center gap-2 rounded-xl border border-[var(--glass-border)] bg-[var(--fill-1)] px-3 py-2 text-xs text-muted">
            <span className="pulse-dot h-2 w-2 rounded-full bg-teal" />
            <span>Live · agents online</span>
          </div>
        )}
        {/* Collapse toggle — desktop only */}
        <button
          onClick={toggleCollapsed}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={`hidden items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-muted transition hover:bg-[var(--fill-1)] hover:text-fg md:flex ${
            collapsed ? "justify-center" : ""
          }`}
        >
          <IconChevron className={`transition-transform duration-300 ${collapsed ? "rotate-180" : ""}`} />
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </>
  );
}

function NavItem({
  href,
  label,
  icon: Icon,
  pathname,
  collapsed = false,
  onNavigate,
}: {
  href: string;
  label: string;
  icon: (p: { className?: string }) => React.ReactNode;
  pathname: string;
  collapsed?: boolean;
  onNavigate?: () => void;
}) {
  const active = pathname === href || pathname.startsWith(href + "/");
  return (
    <Link
      href={href}
      onClick={onNavigate}
      data-active={active}
      title={collapsed ? label : undefined}
      className={`group relative z-10 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors duration-200 ${
        collapsed ? "justify-center" : ""
      } ${active ? "text-fg" : "text-muted hover:text-fg hover:bg-[var(--fill-1)]"}`}
    >
      <Icon
        className={`shrink-0 transition-colors duration-200 ${
          active ? "text-teal" : "text-faint group-hover:text-muted"
        }`}
      />
      {!collapsed && <span className="whitespace-nowrap">{label}</span>}
    </Link>
  );
}

export function Topbar({ title }: { title: string }) {
  const { me, logout } = useAuth();
  const { setMobileOpen } = useSidebar();
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-4 px-5 py-5">
      <div className="flex min-w-0 items-center gap-3">
        <button
          onClick={() => setMobileOpen(true)}
          aria-label="Open menu"
          className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-[var(--glass-border)] glass text-muted transition hover:text-fg md:hidden"
        >
          <IconMenu />
        </button>
        <h1 className="truncate font-display text-2xl leading-none md:text-[1.7rem]">{title}</h1>
      </div>
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
function IconUsers({ className = "" }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
function IconScroll({ className = "" }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 21h9a3 3 0 0 0 3-3V9a2 2 0 0 0-2-2h-2" /><path d="M19 17V5a2 2 0 0 0-2-2H4" />
      <path d="M4 3a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h2V5a2 2 0 0 0-2-2Z" /><path d="M9 8h6M9 12h6M9 16h4" />
    </svg>
  );
}
function IconGear({ className = "" }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" />
    </svg>
  );
}
function IconMenu() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M3 6h18M3 12h18M3 18h18" />
    </svg>
  );
}
function IconClose() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}
function IconChevron({ className = "" }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 18l-6-6 6-6" />
    </svg>
  );
}
