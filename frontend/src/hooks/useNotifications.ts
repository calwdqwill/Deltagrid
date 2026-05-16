import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { snakeToCamel } from "@/lib/api";

function camelToSnake(obj: Record<string, unknown>): Record<string, unknown> {
  if (Array.isArray(obj)) return obj.map(camelToSnake) as unknown as Record<string, unknown>;
  if (obj === null || typeof obj !== "object") return obj;
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
    result[snakeKey] = camelToSnake(value as Record<string, unknown>);
  }
  return result;
}

export interface NotificationPreferences {
  id: string;
  userId: string;
  emailEnabled: boolean;
  emailAddress?: string;
  webPushEnabled: boolean;
  webPushSubscriptionJson?: string;
  telegramEnabled: boolean;
  telegramChatId?: string;
  marketAlertsEnabled: boolean;
  executionAlertsEnabled: boolean;
  riskAlertsEnabled: boolean;
  rwaAlertsEnabled: boolean;
  minSeverity: string;
  quietHoursStart?: number;
  quietHoursEnd?: number;
}

async function fetchPreferences() {
  const res = await api.get("/notifications/preferences");
  return snakeToCamel(res.data.data) as NotificationPreferences;
}

async function updatePreferences(data: Partial<NotificationPreferences>) {
  const res = await api.put("/notifications/preferences", camelToSnake(data as Record<string, unknown>));
  return snakeToCamel(res.data.data) as NotificationPreferences;
}

async function subscribeWebPush(subscriptionJson: string) {
  const res = await api.post("/notifications/web-push/subscribe", { subscription_json: subscriptionJson });
  return res.data.data;
}

async function unsubscribeWebPush() {
  const res = await api.post("/notifications/web-push/unsubscribe");
  return res.data.data;
}

export function useNotificationPreferences() {
  return useQuery({
    queryKey: ["notificationPreferences"],
    queryFn: fetchPreferences,
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updatePreferences,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notificationPreferences"] }),
  });
}

export function useWebPushSubscription() {
  const queryClient = useQueryClient();
  return {
    subscribe: useMutation({
      mutationFn: subscribeWebPush,
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notificationPreferences"] }),
    }),
    unsubscribe: useMutation({
      mutationFn: unsubscribeWebPush,
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notificationPreferences"] }),
    }),
  };
}
