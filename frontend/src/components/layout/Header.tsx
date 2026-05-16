"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { RefreshCw, Globe, Activity } from "lucide-react";
import { useUIStore } from "@/stores/uiStore";
import { useScannerStore } from "@/stores/scannerStore";
import { useLocale } from "@/hooks/useLocale";
import { availableLocales } from "@/i18n";
import { cn } from "@/lib/utils";
import { UserMenu } from "@/components/auth/UserMenu";
import { LoginModal } from "@/components/auth/LoginModal";

const PAGE_TITLE_MAP: Record<string, string> = {
  "/": "scanner.title",
  "/market": "market.title",
  "/paper-trading": "paper.title",
  "/execution": "execution.title",
  "/exchange-accounts": "exchangeAccounts.title",
  "/risk-rules": "risk.title",
  "/alerts": "alerts.title",
  "/notifications": "notifications.title",
  "/profile": "profile.title",
  "/settings": "settings.title",
  "/rwa": "rwa.title",
  "/treasury": "treasury.title",
};

function getPageTitleKey(pathname: string): string {
  return PAGE_TITLE_MAP[pathname] || "scanner.title";
}

function getPageTitle(t: any, pathname: string): string {
  const key = getPageTitleKey(pathname);
  const parts = key.split(".");
  let obj = t;
  for (const part of parts) {
    obj = obj?.[part];
    if (obj === undefined) return "";
  }
  return obj;
}

export function Header() {
  const pathname = usePathname();
  const { locale, setLocale } = useUIStore();
  const { isLoading, data } = useScannerStore();
  const { t } = useLocale();
  const [loginOpen, setLoginOpen] = useState(false);

  const isFallback = data?.meta.isFallback;
  const hasStale = data && Object.keys(data.meta.dataStatusCounts).some((k) => k === "stale");
  const isScannerPage = pathname === "/";

  return (
    <>
      <header className="flex items-center justify-between h-16 px-6 bg-white border-b border-border">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold text-primary-text">{getPageTitle(t, pathname)}</h1>
          {isScannerPage && (
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
                  isFallback || hasStale
                    ? "bg-amber-50 text-amber-700"
                    : "bg-emerald-50 text-emerald-700"
                )}
              >
                <Activity className="w-3.5 h-3.5" />
                {isFallback
                  ? t.status.fallback
                  : hasStale
                  ? t.status.stale
                  : t.status.live}
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => window.location.reload()}
            disabled={isLoading}
            className={cn(
              "inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border border-border hover:bg-row-hover transition-colors",
              isLoading && "opacity-50 cursor-not-allowed"
            )}
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            {t.scanner.refresh}
          </button>

          <div className="relative">
            <select
              value={locale}
              onChange={(e) => setLocale(e.target.value)}
              className="appearance-none pl-9 pr-8 py-2 rounded-lg border border-border bg-white text-sm font-medium text-primary-text hover:bg-row-hover cursor-pointer focus:outline-none focus:ring-2 focus:ring-accent-blue/20"
            >
              {availableLocales.map((loc) => (
                <option key={loc.code} value={loc.code}>
                  {loc.label}
                </option>
              ))}
            </select>
            <Globe className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-text pointer-events-none" />
          </div>

          <UserMenu onLoginClick={() => setLoginOpen(true)} />
        </div>
      </header>

      <LoginModal isOpen={loginOpen} onClose={() => setLoginOpen(false)} />
    </>
  );
}
