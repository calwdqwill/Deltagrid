"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Settings, ChevronLeft, ChevronRight, TrendingUp, User, Activity, Zap, Link2, Shield, Bell, Mail, Landmark, Building2 } from "lucide-react";
import { useUIStore } from "@/stores/uiStore";
import { useLocale } from "@/hooks/useLocale";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const pathname = usePathname();
  const { t } = useLocale();
  const { isAuthenticated } = useAuthStore();

  const navItems = [
    { href: "/", label: t.nav.scanner, icon: BarChart3 },
    { href: "/market", label: t.nav.market, icon: Activity },
    { href: "/rwa", label: t.nav.rwa, icon: Landmark },
    { href: "/treasury", label: t.nav.treasury, icon: Building2 },
    ...(isAuthenticated
      ? [
          { href: "/paper-trading", label: t.nav.paperTrading, icon: TrendingUp },
          { href: "/execution", label: t.nav.execution, icon: Zap },
          { href: "/exchange-accounts", label: t.nav.exchangeAccounts, icon: Link2 },
          { href: "/risk-rules", label: t.nav.riskRules, icon: Shield },
          { href: "/alerts", label: t.nav.alerts || "Alerts", icon: Bell },
          { href: "/notifications", label: t.nav.notifications || "Notifications", icon: Mail },
          { href: "/profile", label: t.nav.profile, icon: User },
        ]
      : []),
    { href: "/settings", label: t.nav.settings, icon: Settings },
  ];

  return (
    <aside
      className={cn(
        "flex flex-col bg-white border-r border-border h-screen transition-all duration-200",
        sidebarOpen ? "w-60" : "w-16"
      )}
    >
      <div className="flex items-center justify-between h-16 px-4 border-b border-border">
        {sidebarOpen && (
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-accent-blue flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="font-semibold text-primary-text">{t.app.name}</span>
          </Link>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-md hover:bg-row-hover text-secondary-text"
        >
          {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
      </div>

      <nav className="flex-1 py-4 px-2 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-accent-blue/10 text-accent-blue"
                  : "text-secondary-text hover:bg-row-hover hover:text-primary-text"
              )}
              title={!sidebarOpen ? item.label : undefined}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
