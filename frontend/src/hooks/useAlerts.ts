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

export interface AlertRule {
  id: string;
  name: string;
  ruleType: string;
  symbol?: string;
  thresholdValue?: number;
  comparison: string;
  cooldownMinutes: number;
  isActive: boolean;
  severity: string;
  channels: string[];
  createdAt?: string;
  updatedAt?: string;
}

export interface AlertEvent {
  id: string;
  ruleId?: string;
  alertType: string;
  symbol?: string;
  message: string;
  severity?: string;
  triggeredAt?: string;
}

async function fetchRules() {
  const res = await api.get("/alerts/rules");
  return (snakeToCamel(res.data.data) as AlertRule[]) || [];
}

async function fetchEvents() {
  const res = await api.get("/alerts/events");
  return (snakeToCamel(res.data.data) as AlertEvent[]) || [];
}

async function createRule(data: Partial<AlertRule>) {
  const res = await api.post("/alerts/rules", camelToSnake(data as Record<string, unknown>));
  return snakeToCamel(res.data.data);
}

async function toggleRule(id: string) {
  const res = await api.post(`/alerts/rules/${id}/toggle`);
  return snakeToCamel(res.data.data);
}

async function deleteRule(id: string) {
  const res = await api.delete(`/alerts/rules/${id}`);
  return snakeToCamel(res.data.data);
}

export function useAlertRules() {
  return useQuery({
    queryKey: ["alertRules"],
    queryFn: fetchRules,
  });
}

export function useAlertEvents(limit: number = 50) {
  return useQuery({
    queryKey: ["alertEvents", limit],
    queryFn: fetchEvents,
  });
}

export function useCreateAlertRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createRule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alertRules"] }),
  });
}

export function useToggleAlertRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: toggleRule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alertRules"] }),
  });
}

export function useDeleteAlertRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteRule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alertRules"] }),
  });
}
