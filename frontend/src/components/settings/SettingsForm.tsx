"use client";

import { useState, useEffect } from "react";
import { Save, Check } from "lucide-react";
import { usePreferences, useUpdatePreferences } from "@/hooks/usePreferences";
import { useLocale } from "@/hooks/useLocale";
import { availableLocales } from "@/i18n";
import { ScannerPreferences } from "@/types/preferences";
import { REFRESH_INTERVALS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function SettingsForm() {
  const { preferences, isLoading } = usePreferences();
  const updateMutation = useUpdatePreferences();
  const { t, locale } = useLocale();
  const [saved, setSaved] = useState(false);

  const [form, setForm] = useState<ScannerPreferences>({
    language: "en",
    minSpreadPct: 0.1,
    refreshIntervalSec: 60,
    slippagePct: 0,
    feeBuyPct: 0.1,
    feeSellPct: 0.1,
    positiveNetOnly: false,
    selectedTypes: ["cex-cex", "dex-cex", "spot-perp"],
  });

  useEffect(() => {
    if (preferences) {
      setForm(preferences);
    }
  }, [preferences]);

  const handleChange = (key: keyof ScannerPreferences, value: unknown) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateMutation.mutateAsync(form);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-secondary-text">
        Loading...
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
      <div className="bg-white rounded-lg border border-border shadow-card p-6">
        <h2 className="text-lg font-semibold text-primary-text mb-4">{t.settings.language}</h2>
        <div className="grid grid-cols-2 gap-3">
          {availableLocales.map((loc) => (
            <label
              key={loc.code}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg border cursor-pointer transition-colors",
                form.language === loc.code
                  ? "border-accent-blue bg-blue-50/50"
                  : "border-border hover:bg-row-hover"
              )}
            >
              <input
                type="radio"
                name="language"
                value={loc.code}
                checked={form.language === loc.code}
                onChange={() => handleChange("language", loc.code)}
                className="w-4 h-4 text-accent-blue"
              />
              <span className="text-sm font-medium text-primary-text">{loc.label}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg border border-border shadow-card p-6">
        <h2 className="text-lg font-semibold text-primary-text mb-4">{t.settings.scannerPrefs}</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-secondary-text mb-1.5">
              {t.settings.refreshInterval}
            </label>
            <select
              value={form.refreshIntervalSec}
              onChange={(e) => handleChange("refreshIntervalSec", parseInt(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-white text-sm text-primary-text focus:outline-none focus:ring-2 focus:ring-accent-blue/20"
            >
              {REFRESH_INTERVALS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-text mb-1.5">
              {t.settings.minSpread}
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={0}
                max={5}
                step={0.1}
                value={form.minSpreadPct}
                onChange={(e) => handleChange("minSpreadPct", parseFloat(e.target.value))}
                className="flex-1 accent-accent-blue"
              />
              <span className="w-16 text-right text-sm font-medium text-primary-text tabular-nums">
                {form.minSpreadPct.toFixed(1)}%
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-text mb-1.5">
              {t.settings.slippage}
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={form.slippagePct}
                onChange={(e) => handleChange("slippagePct", parseFloat(e.target.value))}
                className="flex-1 accent-accent-blue"
              />
              <span className="w-16 text-right text-sm font-medium text-primary-text tabular-nums">
                {form.slippagePct.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-border shadow-card p-6">
        <h2 className="text-lg font-semibold text-primary-text mb-4">{t.settings.thresholds}</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-secondary-text mb-1.5">
              {t.settings.feeBuy}
            </label>
            <input
              type="number"
              min={0}
              max={10}
              step={0.01}
              value={form.feeBuyPct}
              onChange={(e) => handleChange("feeBuyPct", parseFloat(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-white text-sm text-primary-text focus:outline-none focus:ring-2 focus:ring-accent-blue/20"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-secondary-text mb-1.5">
              {t.settings.feeSell}
            </label>
            <input
              type="number"
              min={0}
              max={10}
              step={0.01}
              value={form.feeSellPct}
              onChange={(e) => handleChange("feeSellPct", parseFloat(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-white text-sm text-primary-text focus:outline-none focus:ring-2 focus:ring-accent-blue/20"
            />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={updateMutation.isPending}
          className={cn(
            "inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold text-white transition-colors",
            saved ? "bg-positive" : "bg-accent-blue hover:bg-blue-600",
            updateMutation.isPending && "opacity-70 cursor-not-allowed"
          )}
        >
          {saved ? (
            <>
              <Check className="w-4 h-4" />
              {t.settings.saved}
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              {t.settings.save}
            </>
          )}
        </button>
      </div>
    </form>
  );
}
