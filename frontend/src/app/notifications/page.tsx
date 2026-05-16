"use client";

import { Shell } from "@/components/layout/Shell";
import { useNotificationPreferences, useUpdateNotificationPreferences } from "@/hooks/useNotifications";
import { useLocale } from "@/hooks/useLocale";
import { cn } from "@/lib/utils";
import { Mail, Bell, Shield } from "lucide-react";

export default function NotificationsPage() {
  const { t } = useLocale();
  const { data: prefs, isLoading } = useNotificationPreferences();
  const update = useUpdateNotificationPreferences();

  if (isLoading) {
    return (
      <Shell>
        <div className="text-sm text-secondary-text">Loading...</div>
      </Shell>
    );
  }

  const p = prefs;

  return (
    <Shell>
      <div className="max-w-xl space-y-6">
        <h1 className="text-lg font-semibold text-primary-text">Notification Preferences</h1>

        <div className="space-y-4">
          <Section title="Channels" icon={<Mail className="w-4 h-4" />}>
            <ToggleRow
              label="Email notifications"
              checked={p?.emailEnabled ?? true}
              onChange={(v) => update.mutate({ emailEnabled: v })}
            />
            <ToggleRow
              label="Web push notifications"
              checked={p?.webPushEnabled ?? false}
              onChange={(v) => update.mutate({ webPushEnabled: v })}
            />
            <ToggleRow
              label="Telegram notifications"
              checked={p?.telegramEnabled ?? false}
              onChange={(v) => update.mutate({ telegramEnabled: v })}
            />
          </Section>

          <Section title="Alert Categories" icon={<Bell className="w-4 h-4" />}>
            <ToggleRow
              label="Market alerts"
              checked={p?.marketAlertsEnabled ?? true}
              onChange={(v) => update.mutate({ marketAlertsEnabled: v })}
            />
            <ToggleRow
              label="Execution alerts"
              checked={p?.executionAlertsEnabled ?? true}
              onChange={(v) => update.mutate({ executionAlertsEnabled: v })}
            />
            <ToggleRow
              label="Risk alerts"
              checked={p?.riskAlertsEnabled ?? true}
              onChange={(v) => update.mutate({ riskAlertsEnabled: v })}
            />
            <ToggleRow
              label="RWA alerts"
              checked={p?.rwaAlertsEnabled ?? true}
              onChange={(v) => update.mutate({ rwaAlertsEnabled: v })}
            />
          </Section>

          <Section title="Quiet Hours" icon={<Shield className="w-4 h-4" />}>
            <div className="flex items-center gap-4">
              <input
                type="number"
                min={0}
                max={23}
                value={p?.quietHoursStart ?? ""}
                onChange={(e) => update.mutate({ quietHoursStart: e.target.value ? parseInt(e.target.value) : undefined })}
                placeholder="Start"
                className="w-20 px-2 py-1.5 rounded border border-border text-sm"
              />
              <span className="text-sm text-secondary-text">to</span>
              <input
                type="number"
                min={0}
                max={23}
                value={p?.quietHoursEnd ?? ""}
                onChange={(e) => update.mutate({ quietHoursEnd: e.target.value ? parseInt(e.target.value) : undefined })}
                placeholder="End"
                className="w-20 px-2 py-1.5 rounded border border-border text-sm"
              />
            </div>
          </Section>
        </div>
      </div>
    </Shell>
  );
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-primary-text">
        {icon}
        {title}
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between px-3 py-2 rounded-lg border border-border bg-white">
      <span className="text-sm text-primary-text">{label}</span>
      <button
        onClick={() => onChange(!checked)}
        className={cn(
          "relative inline-flex h-5 w-9 items-center rounded-full transition-colors",
          checked ? "bg-accent-blue" : "bg-gray-200"
        )}
      >
        <span
          className={cn(
            "inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform",
            checked ? "translate-x-5" : "translate-x-1"
          )}
        />
      </button>
    </div>
  );
}
