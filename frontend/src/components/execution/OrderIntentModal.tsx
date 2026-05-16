"use client";

import { useState } from "react";
import { useLocale } from "@/hooks/useLocale";
import { useAuthStore } from "@/stores/authStore";
import { useExchangeAccounts } from "@/hooks/useExchangeAccounts";
import { useCreateOrderIntent, useConfirmOrderIntent } from "@/hooks/useExecution";
import { useDryRunRiskCheck } from "@/hooks/useRiskRules";
import { X, ShieldAlert, Zap, FlaskConical } from "lucide-react";

interface OrderIntentModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultSymbol?: string;
  defaultSide?: string;
}

export default function OrderIntentModal({ isOpen, onClose, defaultSymbol = "BTC/USDT", defaultSide = "buy" }: OrderIntentModalProps) {
  const { t } = useLocale();
  const { isAuthenticated } = useAuthStore();
  const [accountId, setAccountId] = useState("");
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [side, setSide] = useState(defaultSide);
  const [orderType, setOrderType] = useState("market");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [isLive, setIsLive] = useState(false);
  const [riskResult, setRiskResult] = useState<any>(null);
  const [createdIntentId, setCreatedIntentId] = useState<string | null>(null);
  const [step, setStep] = useState<1 | 2>(1);

  const { data: accounts } = useExchangeAccounts({ enabled: isAuthenticated });
  const createIntent = useCreateOrderIntent();
  const confirmIntent = useConfirmOrderIntent();
  const dryRunCheck = useDryRunRiskCheck();

  if (!isOpen) return null;

  const handleRiskCheck = async () => {
    if (!accountId || !quantity) return;
    const result = await dryRunCheck.mutateAsync({
      accountId,
      symbol,
      side,
      orderType,
      quantity: parseFloat(quantity),
      price: price ? parseFloat(price) : undefined,
    });
    setRiskResult(result);
  };

  const handleCreateIntent = async () => {
    const res = await createIntent.mutateAsync({
      accountId,
      symbol,
      side,
      orderType,
      quantity: parseFloat(quantity),
      price: price ? parseFloat(price) : undefined,
    });
    if ((res as any).data?.id) {
      setCreatedIntentId((res as any).data.id);
      setStep(2);
    }
  };

  const handleConfirm = async () => {
    if (!createdIntentId) return;
    await confirmIntent.mutateAsync({ id: createdIntentId, isLive });
    onClose();
    resetForm();
  };

  const resetForm = () => {
    setAccountId("");
    setSymbol(defaultSymbol);
    setSide(defaultSide);
    setOrderType("market");
    setQuantity("");
    setPrice("");
    setIsLive(false);
    setRiskResult(null);
    setCreatedIntentId(null);
    setStep(1);
  };

  const activeAccounts = accounts?.filter((a: any) => a.hasKeys) || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">{t.execution.newIntent}</h2>
          <button onClick={onClose} className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Account</label>
              <select
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
              >
                <option value="">Select account...</option>
                {activeAccounts.map((a: any) => (
                  <option key={a.id} value={a.id}>
                    {a.exchangeName} — {a.accountLabel}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Symbol</label>
                <input
                  type="text"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Side</label>
                <select
                  value={side}
                  onChange={(e) => setSide(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                >
                  <option value="buy">Buy</option>
                  <option value="sell">Sell</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Type</label>
                <select
                  value={orderType}
                  onChange={(e) => setOrderType(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                >
                  <option value="market">Market</option>
                  <option value="limit">Limit</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Quantity</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
            {orderType === "limit" && (
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Price</label>
                <input
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>
            )}

            <button
              onClick={handleRiskCheck}
              disabled={dryRunCheck.isPending || !accountId || !quantity}
              className="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              {dryRunCheck.isPending ? "Checking..." : "Preview Risk Check"}
            </button>

            {riskResult && (
              <div
                className={`rounded-lg border p-3 text-sm ${
                  riskResult.passed
                    ? "border-green-200 bg-green-50 text-green-800"
                    : "border-red-200 bg-red-50 text-red-800"
                }`}
              >
                <div className="flex items-center gap-2 font-medium">
                  {riskResult.passed ? <ShieldAlert size={14} /> : <ShieldAlert size={14} />}
                  {riskResult.passed ? "Risk check passed" : "Risk check blocked"}
                </div>
                {riskResult.message && <p className="mt-1 text-xs">{riskResult.message}</p>}
              </div>
            )}

            <button
              onClick={handleCreateIntent}
              disabled={createIntent.isPending || !accountId || !quantity}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createIntent.isPending ? "Creating..." : "Create Intent"}
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600">Review and confirm your order intent.</p>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Symbol</span><span className="font-medium">{symbol}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Side</span><span className="font-medium capitalize">{side}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Type</span><span className="font-medium capitalize">{orderType}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Quantity</span><span className="font-medium">{quantity}</span></div>
            </div>

            <label className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              <input
                type="checkbox"
                checked={isLive}
                onChange={(e) => setIsLive(e.target.checked)}
                className="rounded border-amber-300"
              />
              <Zap size={14} />
              <span className="font-medium">{t.execution.liveTrading}</span>
            </label>
            {!isLive && (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <FlaskConical size={12} />
                Default mode: Dry Run. Order will be rejected safely.
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={() => setStep(1)}
                className="flex-1 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Back
              </button>
              <button
                onClick={handleConfirm}
                disabled={confirmIntent.isPending}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {confirmIntent.isPending ? "Confirming..." : t.execution.confirmIntent}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
