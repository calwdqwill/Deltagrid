import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createOrderIntent,
  fetchOrderIntents,
  confirmOrderIntent,
  cancelOrderIntent,
  fetchOrders,
  fetchOrderEvents,
} from "@/lib/api";

function snakeToCamelObj(obj: any): any {
  if (Array.isArray(obj)) return obj.map(snakeToCamelObj);
  if (obj === null || typeof obj !== "object") return obj;
  const result: any = {};
  for (const [key, value] of Object.entries(obj)) {
    const camelKey = key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase());
    result[camelKey] = snakeToCamelObj(value);
  }
  return result;
}

export function useOrderIntents(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["order-intents"],
    queryFn: async () => {
      const res = await fetchOrderIntents();
      return snakeToCamelObj(res.data);
    },
    enabled: options?.enabled !== false,
  });
}

export function useCreateOrderIntent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createOrderIntent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order-intents"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useConfirmOrderIntent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, isLive }: { id: string; isLive: boolean }) => {
      const res = await confirmOrderIntent(id, isLive);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order-intents"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useCancelOrderIntent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await cancelOrderIntent(id);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order-intents"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useOrders(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["orders"],
    queryFn: async () => {
      const res = await fetchOrders();
      return snakeToCamelObj(res.data);
    },
    enabled: options?.enabled !== false,
  });
}

export function useOrderEvents(orderId: string | null) {
  return useQuery({
    queryKey: ["order-events", orderId],
    queryFn: async () => {
      if (!orderId) return [];
      const res = await fetchOrderEvents(orderId);
      return snakeToCamelObj(res.data);
    },
    enabled: !!orderId,
  });
}
