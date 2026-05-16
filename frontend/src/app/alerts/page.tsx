"use client";

import { useState } from "react";
import { Shell } from "@/components/layout/Shell";
import { useAlertRules, useAlertEvents, useToggleAlertRule, useDeleteAlertRule, useCreateAlertRule } from "@/hooks/useAlerts";
import { useLocale } from "@/hooks/useLocale";
import { cn } from "@/lib/utils";
import { Bell, Trash2, ToggleLeft, ToggleRight, Plus, X } from "lucide-react";

export default function AlertsPage() {
  const { t } = useLocale();
  const { data: rules, isLoading: rulesLoading } = useAlertRules();
  const { data: events, isLoading: eventsLoading } = useAlertEvents(20);
  const toggle = useToggleAlertRule();
  const remove = useDeleteAlertRule();
  const create = useCreateAlertRule();

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "",
    ruleType: "price_above",
    symbol: "",
    thresholdValue: "",
    comparison: "gte",
    cooldownMinutes: 60,
    severity: "info",
    channels: ["email"],
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    create.mutate(
      {
        name: form.name,
        ruleType: form.ruleType,
        symbol: form.symbol || undefined,
        thresholdValue: form.thresholdValue ? parseFloat(form.thresholdValue) : undefined,
        comparison: form.comparison,
        cooldownMinutes: form.cooldownMinutes,
        severity: form.severity,
        channels: form.channels,
      },
      {
        onSuccess: () => {
          setShowForm(false);
          setForm({ name: "", ruleType: "price_above", symbol: "", thresholdValue: "", comparison: "gte", cooldownMinutes: 60, severity: "info", channels: ["email"] });
        },
      }
    );
  };

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-primary-text">Alert Rules</h1>
          <button
            onClick={() => setShowForm(!showForm)}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-accent-blue text-white hover:bg-blue-600 transition-colors"
          >
            {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            {showForm ? "Cancel" : "Add Rule"}
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="space-y-3 p-4 rounded-lg border border-border bg-white">
            <div className="grid grid-cols-2 gap-3">
              <input
                required
                placeholder="Rule name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="px-3 py-2 rounded border border-border text-sm"
              />
              <select
                value={form.ruleType}
                onChange={(e) => setForm({ ...form, ruleType: e.target.value })}
                className="px-3 py-2 rounded border border-border text-sm"
              >
                <option value="price_above">Price above</option>
                <option value="price_below">Price below</option>
                <option value="funding_rate_spike">Funding rate spike</option>
                <option value="oi_spike">Open interest spike</option>
                <option value="spread_alert">Spread alert</option>
              </select>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <input
                placeholder="Symbol (e.g. BTC/USDT)"
                value={form.symbol}
                onChange={(e) => setForm({ ...form, symbol: e.target.value })}
                className="px-3 py-2 rounded border border-border text-sm"
              />
              <input
                type="number"
                step="any"
                placeholder="Threshold"
                value={form.thresholdValue}
                onChange={(e) => setForm({ ...form, thresholdValue: e.target.value })}
                className="px-3 py-2 rounded border border-border text-sm"
              />
              <select
                value={form.comparison}
                onChange={(e) => setForm({ ...form, comparison: e.target.value })}
                className="px-3 py-2 rounded border border-border text-sm"
              >
                <option value="gte">≥</option>
                <option value="lte">≤</option>
                <option value="eq">=</option>
              </select>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="number"
                placeholder="Cooldown (min)"
                value={form.cooldownMinutes}
                onChange={(e) => setForm({ ...form, cooldownMinutes: parseInt(e.target.value) || 60 })}
                className="w-32 px-3 py-2 rounded border border-border text-sm"
              />
              <select
                value={form.severity}
                onChange={(e) => setForm({ ...form, severity: e.target.value })}
                className="px-3 py-2 rounded border border-border text-sm"
              >
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={create.isPending}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium bg-accent-blue text-white hover:bg-blue-600 transition-colors",
                create.isPending && "opacity-70 cursor-not-allowed"
              )}
            >
              {create.isPending ? "Saving..." : "Save Rule"}
            </button>
          </form>
        )}

        {rulesLoading ? (
          <div className="text-sm text-secondary-text">Loading...</div>
        ) : !rules || rules.length === 0 ? (
          <div className="text-sm text-secondary-text">No alert rules yet.</div>
        ) : (
          <div className="space-y-2">
            {rules.map((rule) => (
              <div
                key={rule.id}
                className="flex items-center justify-between px-4 py-3 rounded-lg border border-border bg-white"
              >
                <div className="space-y-0.5">
                  <div className="text-sm font-medium text-primary-text">{rule.name}</div>
                  <div className="text-xs text-secondary-text">
                    {rule.ruleType} {rule.symbol ? `· ${rule.symbol}` : ""} · {rule.comparison} {rule.thresholdValue}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => toggle.mutate(rule.id)}
                    className="p-2 rounded-lg hover:bg-row-hover text-secondary-text"
                  >
                    {rule.isActive ? (
                      <ToggleRight className="w-5 h-5 text-green-600" />
                    ) : (
                      <ToggleLeft className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                  <button
                    onClick={() => remove.mutate(rule.id)}
                    className="p-2 rounded-lg hover:bg-red-50 text-secondary-text hover:text-red-600"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="pt-4 border-t border-border">
          <h2 className="text-base font-semibold text-primary-text mb-3">Recent Alerts</h2>
          {eventsLoading ? (
            <div className="text-sm text-secondary-text">Loading...</div>
          ) : !events || events.length === 0 ? (
            <div className="text-sm text-secondary-text">No alerts triggered yet.</div>
          ) : (
            <div className="space-y-2">
              {events.map((event) => (
                <div
                  key={event.id}
                  className="flex items-start gap-3 px-4 py-3 rounded-lg border border-border bg-white"
                >
                  <Bell className="w-4 h-4 text-accent-blue mt-0.5 shrink-0" />
                  <div className="space-y-0.5">
                    <div className="text-sm text-primary-text">{event.message}</div>
                    <div className="text-xs text-secondary-text">
                      {event.alertType} {event.symbol ? `· ${event.symbol}` : ""} · {event.severity}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Shell>
  );
}
