"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  Activity,
  BarChart3,
  CandlestickChart,
  ChevronLeft,
  ChevronRight,
  FlaskConical,
  Grid3X3,
  Layers3,
  LineChart,
  Network,
  Orbit,
  RadioTower,
  Search,
} from "lucide-react";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";

type NavChild = {
  label: string;
  view: string;
};

type NavItem = {
  href: string;
  label: string;
  icon: typeof Activity;
  children?: NavChild[];
};

const navItems: NavItem[] = [
  { href: "/market", label: "Market Overview", icon: Activity },
  {
    href: "/perp-dex",
    label: "Perp DEX",
    icon: RadioTower,
    children: [
      { label: "Overview", view: "overview" },
      { label: "Venues", view: "venues" },
      { label: "Open Interest", view: "open-interest" },
      { label: "Liquidity", view: "liquidity" },
      { label: "Opportunities", view: "opportunities" },
    ],
  },
  { href: "/assets", label: "Assets", icon: Layers3 },
  {
    href: "/funding",
    label: "Funding",
    icon: Orbit,
    children: [
      { label: "Overview", view: "overview" },
      { label: "Funding History", view: "history" },
      { label: "Perp DEX Funding", view: "perp-dex" },
      { label: "Funding Arbitrage", view: "arbitrage" },
      { label: "Funding Matrix", view: "matrix" },
      { label: "Predicted Funding", view: "predicted" },
      { label: "Long / Short Legs", view: "legs" },
    ],
  },
  { href: "/arbitrage-scanner", label: "Arbitrage Scanner", icon: Network },
  { href: "/market-matrix", label: "Market Matrix", icon: Grid3X3 },
  { href: "/charts", label: "Charts", icon: CandlestickChart },
  { href: "/strategy-lab", label: "Strategy Lab", icon: FlaskConical },
];

function isActivePath(pathname: string, href: string) {
  if (href === "/market") return pathname === "/market" || pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

function viewHref(href: string, view: string) {
  return view === "overview" ? href : `${href}?view=${view}`;
}

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeView = searchParams.get("view") ?? "overview";

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-white/10 bg-[#070A12] text-slate-300 transition-all duration-200",
        sidebarOpen ? "w-64" : "w-[72px]"
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-4">
        {sidebarOpen && (
          <Link href="/market" className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-indigo-300/30 bg-gradient-to-br from-cyan-400/18 via-indigo-500/30 to-fuchsia-500/28">
              <BarChart3 className="h-5 w-5 text-cyan-200" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-[0.08em] text-white">DELTA GRID</div>
              <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500">Research terminal</div>
            </div>
          </Link>
        )}
        <button
          onClick={toggleSidebar}
          className="rounded-md border border-white/10 p-1.5 text-slate-500 transition-colors hover:bg-white/[0.06] hover:text-slate-200"
          type="button"
          aria-label="Toggle sidebar"
        >
          {sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <div className="space-y-1">
          {navItems.map((item) => {
            const active = isActivePath(pathname, item.href);
            return (
              <div key={item.href}>
                <Link
                  href={item.href}
                  title={!sidebarOpen ? item.label : undefined}
                  className={cn(
                    "flex min-h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors",
                    active
                      ? "border border-indigo-400/25 bg-indigo-500/18 text-white shadow-[inset_3px_0_0_rgba(129,140,248,0.9)]"
                      : "text-slate-400 hover:bg-white/[0.05] hover:text-slate-100"
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {sidebarOpen && <span>{item.label}</span>}
                </Link>

                {sidebarOpen && active && item.children && (
                  <div className="ml-5 mt-1 border-l border-white/10 py-1 pl-4">
                    {item.children.map((child) => (
                      <Link
                        key={child.view}
                        href={viewHref(item.href, child.view)}
                        aria-current={activeView === child.view ? "page" : undefined}
                        className={cn(
                          "relative flex min-h-7 items-center rounded-md px-2 text-xs transition-colors",
                          activeView === child.view ? "text-indigo-200" : "text-slate-500 hover:text-slate-200"
                        )}
                      >
                        <span className="absolute -left-4 top-1/2 h-px w-3 bg-white/10" />
                        {child.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </nav>

      <div className="border-t border-white/10 p-3">
        {sidebarOpen ? (
          <div className="rounded-lg border border-white/10 bg-white/[0.035] p-3">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
              <Search className="h-3.5 w-3.5 text-cyan-300" />
              Workspace Search
            </div>
            <div className="mt-2 text-[11px] leading-4 text-slate-500">Assets, markets, strategies</div>
          </div>
        ) : (
          <div className="flex justify-center rounded-lg border border-white/10 bg-white/[0.035] p-2">
            <Search className="h-4 w-4 text-slate-500" />
          </div>
        )}
      </div>
    </aside>
  );
}
