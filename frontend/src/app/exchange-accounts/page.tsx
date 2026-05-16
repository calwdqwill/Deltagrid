"use client";

import { useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useLocale } from "@/hooks/useLocale";
import { useExchangeAccounts, useDeleteExchangeAccount } from "@/hooks/useExchangeAccounts";
import AddExchangeModal from "@/components/exchange/AddExchangeModal";
import { Shell } from "@/components/layout/Shell";
import { Plus, Trash2, Link2, Link2Off, Shield } from "lucide-react";

export default function ExchangeAccountsPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuthStore();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: accounts, isLoading } = useExchangeAccounts({ enabled: isAuthenticated });
  const deleteAccount = useDeleteExchangeAccount();

  if (!isAuthenticated) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-slate-500">Please sign in to manage exchange accounts.</p>
      </div>
    );
  }

  return (
    <Shell>
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t.exchangeAccounts.title}</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus size={16} />
          {t.exchangeAccounts.addAccount}
        </button>
      </div>

      {isLoading && <p className="text-slate-500">Loading...</p>}

      {!isLoading && (!accounts || accounts.length === 0) && (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
          <Link2Off className="mx-auto mb-3 text-slate-300" size={40} />
          <p className="text-slate-500">{t.exchangeAccounts.noAccounts}</p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {accounts?.map((account: any) => (
          <div
            key={account.id}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
          >
            <div className="mb-3 flex items-start justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                  <Link2 size={16} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 capitalize">{account.exchangeName}</h3>
                  <p className="text-xs text-slate-500">{account.accountLabel}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  if (confirm(t.exchangeAccounts.deleteConfirm)) {
                    deleteAccount.mutate(account.id);
                  }
                }}
                className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
              >
                <Trash2 size={14} />
              </button>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">{t.exchangeAccounts.type}</span>
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 uppercase">
                  {account.accountType}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">{t.exchangeAccounts.status}</span>
                <span
                  className={`flex items-center gap-1 text-xs font-medium ${
                    account.hasKeys ? "text-green-600" : "text-amber-600"
                  }`}
                >
                  <Shield size={12} />
                  {account.hasKeys ? t.exchangeAccounts.connected : t.exchangeAccounts.notConnected}
                </span>
              </div>
              {account.isTestnet && (
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">{t.exchangeAccounts.testnet}</span>
                  <span className="text-xs text-blue-600">Yes</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <AddExchangeModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
    </Shell>
  );
}
