"use client";

import { useState } from "react";
import { useLocale } from "@/hooks/useLocale";
import { useCreateExchangeAccount, useStoreExchangeKeys } from "@/hooks/useExchangeAccounts";
import { useConnectors } from "@/hooks/useExchangeAccounts";
import { X, Eye, EyeOff } from "lucide-react";

interface AddExchangeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const EXCHANGE_OPTIONS = [
  { value: "binance", label: "Binance" },
  { value: "bybit", label: "Bybit" },
  { value: "okx", label: "OKX" },
  { value: "hyperliquid", label: "Hyperliquid" },
  { value: "aster", label: "Aster" },
];

export default function AddExchangeModal({ isOpen, onClose }: AddExchangeModalProps) {
  const { t } = useLocale();
  const [step, setStep] = useState<1 | 2>(1);
  const [exchangeName, setExchangeName] = useState("binance");
  const [accountLabel, setAccountLabel] = useState("Main");
  const [accountType, setAccountType] = useState("spot");
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [passphrase, setPassphrase] = useState("");
  const [isTestnet, setIsTestnet] = useState(false);
  const [showSecret, setShowSecret] = useState(false);
  const [createdAccountId, setCreatedAccountId] = useState<string | null>(null);

  const createAccount = useCreateExchangeAccount();
  const storeKeys = useStoreExchangeKeys();

  if (!isOpen) return null;

  const needsPassphrase = exchangeName === "okx";

  const handleCreateAccount = async () => {
    const res = await createAccount.mutateAsync({
      exchangeName,
      accountLabel,
      accountType,
    });
    if (res.data && (res.data as any).id) {
      setCreatedAccountId((res.data as any).id);
      setStep(2);
    }
  };

  const handleStoreKeys = async () => {
    if (!createdAccountId) return;
    const payload: Record<string, unknown> = {
      apiKey,
      apiSecret,
      isTestnet,
    };
    if (needsPassphrase && passphrase) {
      payload.passphrase = passphrase;
    }
    await storeKeys.mutateAsync({ accountId: createdAccountId, data: payload });
    onClose();
    resetForm();
  };

  const resetForm = () => {
    setStep(1);
    setExchangeName("binance");
    setAccountLabel("Main");
    setAccountType("spot");
    setApiKey("");
    setApiSecret("");
    setPassphrase("");
    setIsTestnet(false);
    setCreatedAccountId(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">{t.exchangeAccounts.addAccount}</h2>
          <button onClick={onClose} className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">{t.exchangeAccounts.exchange}</label>
              <select
                value={exchangeName}
                onChange={(e) => setExchangeName(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
              >
                {EXCHANGE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">{t.exchangeAccounts.label}</label>
              <input
                type="text"
                value={accountLabel}
                onChange={(e) => setAccountLabel(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">{t.exchangeAccounts.type}</label>
              <select
                value={accountType}
                onChange={(e) => setAccountType(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
              >
                <option value="spot">Spot</option>
                <option value="perp">Perp</option>
                <option value="margin">Margin</option>
              </select>
            </div>
            <button
              onClick={handleCreateAccount}
              disabled={createAccount.isPending}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createAccount.isPending ? "..." : "Next"}
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <p className="text-sm text-slate-500">Enter API credentials for {exchangeName}</p>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">{t.exchangeAccounts.apiKey}</label>
              <input
                type="text"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">{t.exchangeAccounts.apiSecret}</label>
              <div className="relative">
                <input
                  type={showSecret ? "text" : "password"}
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 pr-10 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowSecret(!showSecret)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showSecret ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            {needsPassphrase && (
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">{t.exchangeAccounts.passphrase}</label>
                <input
                  type="password"
                  value={passphrase}
                  onChange={(e) => setPassphrase(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>
            )}
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={isTestnet}
                onChange={(e) => setIsTestnet(e.target.checked)}
                className="rounded border-slate-300"
              />
              {t.exchangeAccounts.testnet}
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setStep(1)}
                className="flex-1 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Back
              </button>
              <button
                onClick={handleStoreKeys}
                disabled={storeKeys.isPending || !apiKey || !apiSecret}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {storeKeys.isPending ? "..." : "Save"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
