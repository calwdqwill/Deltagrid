"use client";

import { useLocale } from "@/hooks/useLocale";

export function InstrumentManager() {
  const { t } = useLocale();

  return (
    <div className="bg-white rounded-lg border border-border shadow-card p-6">
      <h2 className="text-lg font-semibold text-primary-text mb-2">Instruments</h2>
      <p className="text-sm text-secondary-text">
        Instrument universe management will be available in a future update.
      </p>
    </div>
  );
}
