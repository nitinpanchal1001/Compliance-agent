import { ReactNode, ButtonHTMLAttributes } from "react";

export function Glass({
  children,
  className = "",
  strong = false,
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  strong?: boolean;
  hover?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl ${strong ? "glass-strong" : "glass"} ${
        hover ? "glass-hover" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}

export function Badge({
  children,
  color,
  className = "",
}: {
  children: ReactNode;
  color?: string;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${className}`}
      style={
        color
          ? {
              color,
              background: `color-mix(in srgb, ${color} 14%, transparent)`,
              border: `1px solid color-mix(in srgb, ${color} 35%, transparent)`,
            }
          : {
              color: "var(--muted)",
              background: "var(--fill-1)",
              border: "1px solid var(--glass-border)",
            }
      }
    >
      {children}
    </span>
  );
}

type BtnProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "danger" | "soft";
  loading?: boolean;
};

export function Button({
  children,
  variant = "primary",
  loading = false,
  className = "",
  disabled,
  ...rest
}: BtnProps) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none";
  const styles: Record<string, string> = {
    primary:
      "text-white shadow-[0_8px_30px_-10px_rgba(139,92,246,0.8)] bg-[linear-gradient(100deg,var(--violet),var(--blue))] hover:brightness-110",
    soft: "text-fg bg-[var(--fill-2)] border border-[var(--glass-border)] hover:bg-[var(--fill-3)]",
    ghost: "text-muted hover:text-fg hover:bg-[var(--line)]",
    danger:
      "text-white bg-[linear-gradient(100deg,var(--crit),var(--pink))] hover:brightness-110",
  };
  return (
    <button
      className={`${base} ${styles[variant]} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <Spinner className="h-4 w-4" />}
      {children}
    </button>
  );
}

export function Spinner({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={`spin ${className}`} viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function Empty({ icon, title, hint }: { icon?: ReactNode; title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      {icon && <div className="text-4xl opacity-60">{icon}</div>}
      <div className="text-fg font-medium">{title}</div>
      {hint && <div className="text-sm text-muted max-w-sm">{hint}</div>}
    </div>
  );
}
