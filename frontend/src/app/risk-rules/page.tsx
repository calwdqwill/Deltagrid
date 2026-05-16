"use client";

import { useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useLocale } from "@/hooks/useLocale";
import { useRiskRules, useCreateRiskRule, useDeleteRiskRule } from "@/hooks/useRiskRules";
import { Shell } from "@/components/layout/Shell";
import { Plus, Trash2, Shield, ShieldAlert, ShieldCheck } from "lucide-react";

const RULE_TYPE_OPTIONS = [
  { value: "max_position_size", label: "Max Position Size" },
  { value: "max_exposure_usd", label: "Max Exposure (USD)" },
  { value: "max_order_size", label: "Max Order Size" },
  { value: "kill_switch", label: "Kill Switch" },
];

const ACTION_OPTIONS = [
  { value: "block", label: "Block" },
  { value: "warn", label: "Warn" },
];

export default function RiskRulesPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuthStore();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [ruleType, setRuleType] = useState("max_position_size");
  const [threshold, setThreshold] = useState("");
  const [action, setAction] = useState("block");
  const [symbol, setSymbol] = useState("");

  const { data: rules, isLoading } = useRiskRules({ enabled: isAuthenticated });
  const createRule = useCreateRiskRule();
  const deleteRule = useDeleteRiskRule();

  if (!isAuthenticated) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-slate-500">Please sign in to manage risk rules.</p>
      </div>
    );
  }

  const handleCreate = async () => {
    await createRule.mutateAsync({
      ruleType,
      thresholdValue: parseFloat(threshold),
      action,
      symbol: symbol || undefined,
    });
    setIsFormOpen(false);
    setRuleType("max_position_size");
    setThreshold("");
    setAction("block");
    setSymbol("");
  };

  return (
    <Shell>
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t.risk.title}</h1>
        <button
          onClick={() => setIsFormOpen(!isFormOpen)}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus size={16} />
          {t.risk.addRule}
        </button>
      </div>

      {isFormOpen && (
        <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold text-slate-900">New Risk Rule</h3>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Rule Type</label>
              <select
                value={ruleType}
                onChange={(e) => setRuleType(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
              >
                {RULE_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Threshold</label>
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Action</label>
              <select
                value={action}
                onChange={(e) => setAction(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
              >
                {ACTION_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="mt-4">
            <label className="mb-1 block text-sm font-medium text-slate-700">Symbol (optional)</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="e.g. BTC/USDT"
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <button
              onClick={() => setIsFormOpen(false)}
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={createRule.isPending || !threshold}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createRule.isPending ? "Saving..." : "Save Rule"}
            </button>
          </div>
        </div>
      )}

      {isLoading && <p className="text-slate-500">Loading...</p>}

      {!isLoading && (!rules || rules.length === 0) && (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
          <Shield className="mx-auto mb-3 text-slate-300" size={40} />
          <p className="text-slate-500">{t.risk.noRules}</p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {rules?.map((rule: any) => (
          <div
            key={rule.id}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="mb-3 flex items-start justify-between">
              <div className="flex items-center gap-2">
                {rule.isActive ? (
                  <ShieldCheck size={18} className="text-green-500" />
                ) : (
                  <ShieldAlert size={18} className="text-slate-400" />
                )}
                <span className="text-sm font-semibold text-slate-900">{rule.ruleType}</span>
              </div>
              <button
                onClick={() => {
                  if (confirm("Delete this rule?")) {
                    deleteRule.mutate(rule.id);
                  }
                }}
                className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
              >
                <Trash2 size={14} />
              </button>
            </div>
            <div className="space-y-1 text-sm text-slate-600">
              <div className="flex justify-between">
                <span>Threshold</span>
                <span className="font-medium text-slate-900">{rule.thresholdValue}</span>
              </div>
              <div className="flex justify-between">
                <span>Action</span>
                <span className={`font-medium ${rule.action === "block" ? "text-red-600" : "text-amber-600"}`}>
                  {rule.action === "block" ? t.risk.actionBlock : t.risk.actionWarn}
                </span>
              </div>
              {rule.symbol && (
                <div className="flex justify-between">
                  <span>Symbol</span>
                  <span className="font-medium text-slate-900">{rule.symbol}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
    </Shell>
  );
}
