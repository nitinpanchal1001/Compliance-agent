"use client";

import { useEffect, useRef, useState } from "react";

interface Tab<T extends string> {
  key: T;
  label: string;
}

/** Horizontal pill tabs with a single highlight that glides (PS5-style)
 *  between the active tab, animating position + width with a springy ease. */
export function SlideTabs<T extends string>({
  tabs,
  value,
  onChange,
  className = "",
}: {
  tabs: Tab<T>[];
  value: T;
  onChange: (key: T) => void;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const settled = useRef(false);
  const [pill, setPill] = useState({ left: 0, top: 0, width: 0, height: 0, visible: false, instant: true });

  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const active = root.querySelector<HTMLElement>('button[data-active="true"]');
    if (active) {
      setPill({
        left: active.offsetLeft,
        top: active.offsetTop,
        width: active.offsetWidth,
        height: active.offsetHeight,
        visible: true,
        instant: !settled.current, // first placement snaps; later ones glide
      });
      settled.current = true;
    } else {
      setPill((p) => ({ ...p, visible: false }));
    }
  }, [value, tabs]);

  return (
    <div ref={ref} className={`relative inline-flex flex-wrap gap-1.5 ${className}`}>
      <span
        aria-hidden
        className={`tab-pill glass pointer-events-none absolute left-0 top-0 z-0 rounded-xl ${
          pill.instant ? "tab-pill-instant" : ""
        }`}
        style={{
          transform: `translate(${pill.left}px, ${pill.top}px)`,
          width: pill.width,
          height: pill.height,
          opacity: pill.visible ? 1 : 0,
        }}
      />
      {tabs.map((t) => {
        const active = t.key === value;
        return (
          <button
            key={t.key}
            data-active={active}
            onClick={() => onChange(t.key)}
            className={`relative z-10 rounded-xl px-3.5 py-1.5 text-sm transition-colors duration-200 ${
              active ? "text-fg" : "text-muted hover:text-fg hover:bg-[var(--fill-1)]"
            }`}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}
