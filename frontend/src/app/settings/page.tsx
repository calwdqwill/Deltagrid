"use client";

import { Shell } from "@/components/layout/Shell";
import { SettingsForm } from "@/components/settings/SettingsForm";
import { useLocale } from "@/hooks/useLocale";

export default function SettingsPage() {
  const { t } = useLocale();

  return (
    <Shell>
      <div className="max-w-3xl">
        <h1 className="text-2xl font-bold text-primary-text mb-6">{t.settings.title}</h1>
        <SettingsForm />
      </div>
    </Shell>
  );
}
