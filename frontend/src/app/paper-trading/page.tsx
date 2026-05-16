"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { usePaperAccounts, useCreatePaperAccount, usePaperTrades, usePortfolio } from "@/hooks/usePaperTrading";
import { usePaperStore } from "@/stores/paperStore";
import { useAuthStore } from "@/stores/authStore";
import { useLocale } from "@/hooks/useLocale";
import { cn, formatPrice } from "@/lib/utils";
import { Plus, TrendingUp, Wallet, BarChart3 } from "lucide-react";

export default function PaperTradingPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { t } = useLocale();
  const { accounts, selectedAccountId, selectAccount } = usePaperStore();
  const { isLoading: accountsLoading } = usePaperAccounts({ enabled: isAuthenticated });
  const createAccount = useCreatePaperAccount();
  const { data: trades, isLoading: tradesLoading } = usePaperTrades(selectedAccountId);
  const { data: portfolio } = usePortfolio(selectedAccountId);
  const [showNewAccount, setShowNewAccount] = useState(false);
  const [newName, setNewName] = useState("Demo Account");

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, router]);

  const selectedAccount = accounts.find((a) => a.id === selectedAccountId);

  return (
    <Shell>
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary-text">{t.paper.title}</h1>
          <button
            onClick={() => setShowNewAccount(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-blue text-white text-sm font-medium hover:bg-blue-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Account
          </button>
        </div>

        {showNewAccount && (
          <div className="bg-white rounded-lg border border-border p-4 space-y-3">
            <h3 className="font-semibold text-primary-text">Create Demo Account</h3>
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="px-3 py-2 rounded-lg border border-border text-sm"
                placeholder="Account name"
              />
              <button
                onClick={() => {
                  createAccount.mutate({ name: newName, initial_balance: 10000 });
                  setShowNewAccount(false);
                }}
                className="px-4 py-2 rounded-lg bg-accent-blue text-white text-sm font-medium"
              >
                Create
              </button>
            </div>
          </div>
        )}

        {accountsLoading ? (
          <div className="text-secondary-text">Loading accounts...</div>
        ) : accounts.length === 0 ? (
          <div className="text-secondary-text">No paper trading accounts. Create one to start.</div>
        ) : (
          <>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {accounts.map((acc) => (
                <button
                  key={acc.id}
                  onClick={() => selectAccount(acc.id)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-3 rounded-lg border text-left min-w-[200px] transition-colors",
                    selectedAccountId === acc.id
                      ? "border-accent-blue bg-blue-50/50"
                      : "border-border bg-white hover:bg-row-hover"
                  )}
                >
                  <Wallet className="w-5 h-5 text-accent-blue" />
                  <div>
                    <div className="font-medium text-primary-text text-sm">{acc.name}</div>
                    <div className="text-xs text-secondary-text">${formatPrice(acc.currentBalance)}</div>
                  </div>
                </button>
              ))}
            </div>

            {selectedAccount && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg border border-border p-4">
                  <div className="flex items-center gap-2 text-secondary-text text-sm mb-1">
                    <Wallet className="w-4 h-4" />
                    {t.paper.balance}
                  </div>
                  <div className="text-2xl font-bold text-primary-text">${formatPrice(selectedAccount.currentBalance)}</div>
                </div>
                <div className="bg-white rounded-lg border border-border p-4">
                  <div className="flex items-center gap-2 text-secondary-text text-sm mb-1">
                    <TrendingUp className="w-4 h-4" />
                    {t.paper.pnl}
                  </div>
                  <div className={cn("text-2xl font-bold", ((portfolio?.totalPnl as number | undefined) ?? 0) >= 0 ? "text-positive" : "text-negative")}>
                    {portfolio?.totalPnl !== undefined ? `+${formatPrice(portfolio.totalPnl as number)}` : "$0.00"}
                  </div>
                </div>
                <div className="bg-white rounded-lg border border-border p-4">
                  <div className="flex items-center gap-2 text-secondary-text text-sm mb-1">
                    <BarChart3 className="w-4 h-4" />
                    {t.paper.trades}
                  </div>
                  <div className="text-2xl font-bold text-primary-text">
                    {(portfolio?.openTrades as number | undefined) ?? 0} <span className="text-sm font-normal text-secondary-text">open</span>
                  </div>
                </div>
              </div>
            )}

            {tradesLoading ? (
              <div className="text-secondary-text">Loading trades...</div>
            ) : trades && trades.length > 0 ? (
              <div className="bg-white rounded-lg border border-border overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50/50 border-b border-border">
                    <tr>
                      <th className="px-4 py-3 text-left text-secondary-text">Strategy</th>
                      <th className="px-4 py-3 text-left text-secondary-text">Instrument</th>
                      <th className="px-4 py-3 text-left text-secondary-text">Side</th>
                      <th className="px-4 py-3 text-right text-secondary-text">Entry</th>
                      <th className="px-4 py-3 text-right text-secondary-text">PnL</th>
                      <th className="px-4 py-3 text-left text-secondary-text">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {trades.map((trade: any) => (
                      <tr key={trade.id} className="hover:bg-row-hover">
                        <td className="px-4 py-3 font-medium text-primary-text">{trade.strategy}</td>
                        <td className="px-4 py-3 text-secondary-text">{trade.instrumentId}</td>
                        <td className="px-4 py-3">
                          <span className={cn(
                            "px-2 py-0.5 rounded text-xs font-medium",
                            trade.side === "buy" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
                          )}>
                            {trade.side}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums">{formatPrice(trade.entryPrice)}</td>
                        <td className={cn("px-4 py-3 text-right tabular-nums font-medium", (trade.pnl || 0) >= 0 ? "text-positive" : "text-negative")}>
                          {trade.pnl !== undefined ? `${trade.pnl >= 0 ? "+" : ""}${formatPrice(trade.pnl)}` : "—"}
                        </td>
                        <td className="px-4 py-3">
                          <span className={cn(
                            "px-2 py-0.5 rounded text-xs font-medium",
                            trade.status === "open" ? "bg-amber-50 text-amber-700" : "bg-gray-100 text-secondary-text"
                          )}>
                            {trade.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : selectedAccount ? (
              <div className="text-secondary-text">No trades yet for this account.</div>
            ) : null}
          </>
        )}
      </div>
    </Shell>
  );
}
