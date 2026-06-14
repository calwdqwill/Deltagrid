"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Bell, CircleDot, Plus, Search, X } from "lucide-react";
import { useUIStore, WorkspaceTab } from "@/stores/uiStore";
import { cn } from "@/lib/utils";
import { UserMenu } from "@/components/auth/UserMenu";
import { LoginModal } from "@/components/auth/LoginModal";

const routeTabs: Array<{ match: (path: string) => boolean; tab: WorkspaceTab }> = [
  {
    match: (path) => path === "/" || path === "/market",
    tab: { id: "market-overview", label: "Market Overview", href: "/market", context: "Command Center" },
  },
  {
    match: (path) => path.startsWith("/perp-dex"),
    tab: { id: "perp-dex-overview", label: "Perp DEX", href: "/perp-dex", context: "Overview" },
  },
  {
    match: (path) => path.startsWith("/assets"),
    tab: { id: "assets", label: "Assets", href: "/assets", context: "Deep Dive" },
  },
  {
    match: (path) => path.startsWith("/funding"),
    tab: { id: "funding-overview", label: "Funding", href: "/funding", context: "Overview" },
  },
  {
    match: (path) => path.startsWith("/arbitrage-scanner"),
    tab: { id: "arbitrage-scanner", label: "Arbitrage Scanner", href: "/arbitrage-scanner", context: "Non-funding" },
  },
  {
    match: (path) => path.startsWith("/market-matrix"),
    tab: { id: "market-matrix", label: "Market Matrix", href: "/market-matrix", context: "Perps" },
  },
  {
    match: (path) => path.startsWith("/charts"),
    tab: { id: "charts", label: "Charts", href: "/charts", context: "Live Streams" },
  },
  {
    match: (path) => path.startsWith("/strategy-lab"),
    tab: { id: "strategy-lab", label: "Strategy Lab", href: "/strategy-lab", context: "Readiness" },
  },
];

function getTabForPath(pathname: string): WorkspaceTab {
  return (
    routeTabs.find((item) => item.match(pathname))?.tab ?? {
      id: "market-overview",
      label: "Market Overview",
      href: "/market",
      context: "Command Center",
    }
  );
}

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const [loginOpen, setLoginOpen] = useState(false);
  const { workspaceTabs, activeWorkspaceTabId, openWorkspaceTab, closeWorkspaceTab, setActiveWorkspaceTab } =
    useUIStore();

  const currentTab = useMemo(() => getTabForPath(pathname), [pathname]);

  useEffect(() => {
    openWorkspaceTab(currentTab);
  }, [currentTab, openWorkspaceTab]);

  const handleClose = (id: string) => {
    const remaining = workspaceTabs.filter((tab) => tab.id !== id);
    const fallback = remaining[0] ?? { href: "/market", id: "market-overview" };
    closeWorkspaceTab(id);
    if (id === activeWorkspaceTabId) {
      router.push(fallback.href);
    }
  };

  return (
    <>
      <header className="flex h-16 items-center gap-3 border-b border-white/10 bg-[#090E19] px-4">
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <div className="flex min-w-0 items-center gap-1 overflow-x-auto rounded-lg border border-white/10 bg-black/20 p-1">
            {workspaceTabs.map((tab) => {
              const active = activeWorkspaceTabId === tab.id;
              return (
                <div
                  key={tab.id}
                  className={cn(
                    "group flex min-h-9 shrink-0 items-center rounded-md border text-xs transition-colors",
                    active
                      ? "border-indigo-400/40 bg-indigo-500/22 text-white"
                      : "border-transparent text-slate-400 hover:bg-white/[0.05] hover:text-slate-100"
                  )}
                >
                  <Link
                    href={tab.href}
                    onClick={() => setActiveWorkspaceTab(tab.id)}
                    className="flex items-center gap-2 px-3"
                  >
                    <CircleDot className={cn("h-3 w-3", active ? "text-cyan-300" : "text-slate-600")} />
                    <span className="font-medium">{tab.label}</span>
                    {tab.context && <span className="hidden text-slate-500 xl:inline">{tab.context}</span>}
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleClose(tab.id)}
                    className="mr-1 rounded p-1 text-slate-500 opacity-70 transition-colors hover:bg-white/10 hover:text-slate-100 group-hover:opacity-100"
                    aria-label={`Close ${tab.label}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              );
            })}
            <button
              type="button"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-white/[0.06] hover:text-slate-100"
              aria-label="Open workspace tab"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="hidden min-w-[300px] items-center rounded-lg border border-white/10 bg-black/20 px-3 py-2 lg:flex">
          <Search className="mr-2 h-4 w-4 text-slate-600" />
          <input
            className="w-full bg-transparent text-xs text-slate-200 outline-none placeholder:text-slate-600"
            placeholder="Search assets, markets, metrics..."
          />
        </div>

        <button
          type="button"
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-black/20 text-slate-400 transition-colors hover:bg-white/[0.06] hover:text-slate-100"
          aria-label="Alerts"
        >
          <Bell className="h-4 w-4" />
        </button>

        <UserMenu onLoginClick={() => setLoginOpen(true)} />
      </header>

      <LoginModal isOpen={loginOpen} onClose={() => setLoginOpen(false)} />
    </>
  );
}
