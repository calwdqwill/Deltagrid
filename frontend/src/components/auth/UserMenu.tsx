"use client";

import { useState } from "react";
import { User, LogOut, ChevronDown } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { useLocale } from "@/hooks/useLocale";
import { cn } from "@/lib/utils";

interface UserMenuProps {
  onLoginClick: () => void;
}

export function UserMenu({ onLoginClick }: UserMenuProps) {
  const { user, isAuthenticated, logout } = useAuthStore();
  const { t } = useLocale();
  const [open, setOpen] = useState(false);

  if (!isAuthenticated) {
    return (
      <button
        onClick={onLoginClick}
        className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-white/10 bg-black/20 px-3 text-xs font-medium text-slate-300 transition-colors hover:bg-white/[0.06] hover:text-white"
      >
        <User className="w-4 h-4" />
        {t.nav.login}
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-white/10 bg-black/20 px-3 text-xs font-medium text-slate-300 transition-colors hover:bg-white/[0.06] hover:text-white"
      >
        <div className="w-6 h-6 rounded-full bg-indigo-500 flex items-center justify-center text-white text-xs font-bold">
          {(user?.username || user?.email || "U")[0].toUpperCase()}
        </div>
        <span className="max-w-[100px] truncate">{user?.username || user?.email}</span>
        <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-2 w-48 rounded-lg border border-white/10 bg-[#0D1322] shadow-2xl z-50 py-1">
            <div className="px-4 py-2 border-b border-white/10">
              <div className="text-sm font-medium text-slate-100 truncate">
                {user?.username || user?.email}
              </div>
              <div className="text-xs text-slate-500 capitalize">{user?.plan}</div>
            </div>
            <button
              onClick={() => {
                logout();
                setOpen(false);
              }}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-rose-300 hover:bg-rose-500/10 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              {t.nav.logout}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
