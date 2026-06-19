"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Sidebar, Topbar } from "@/components/Nav";
import { Spinner } from "@/components/ui";

const TITLES: { match: (p: string) => boolean; title: string }[] = [
  { match: (p) => p.startsWith("/dashboard"), title: "Overview" },
  { match: (p) => p.startsWith("/documents"), title: "Documents" },
  { match: (p) => /^\/cases\/[^/]+$/.test(p), title: "Case detail" },
  { match: (p) => p.startsWith("/cases"), title: "Cases" },
  { match: (p) => p.startsWith("/policies"), title: "Policy corpus" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { me, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !me) router.replace("/login");
  }, [me, loading, router]);

  if (loading || !me) {
    return (
      <div className="grid min-h-screen place-items-center text-muted">
        <Spinner />
      </div>
    );
  }

  const title = TITLES.find((t) => t.match(pathname))?.title ?? "Overview";

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title={title} />
        <main className="flex-1 px-5 pb-12">{children}</main>
      </div>
    </div>
  );
}
