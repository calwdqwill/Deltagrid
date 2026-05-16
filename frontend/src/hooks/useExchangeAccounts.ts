import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchExchangeAccounts,
  createExchangeAccount,
  deleteExchangeAccount,
  storeExchangeKeys,
  fetchConnectors,
} from "@/lib/api";
import { useExchangeAccountStore } from "@/stores/exchangeAccountStore";

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

export function useExchangeAccounts(options?: { enabled?: boolean }) {
  const { setAccounts } = useExchangeAccountStore();

  return useQuery({
    queryKey: ["exchange-accounts"],
    queryFn: async () => {
      const res = await fetchExchangeAccounts();
      const accounts = snakeToCamelObj(res.data);
      setAccounts(accounts);
      return accounts;
    },
    enabled: options?.enabled !== false,
  });
}

export function useCreateExchangeAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createExchangeAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exchange-accounts"] });
    },
  });
}

export function useDeleteExchangeAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteExchangeAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exchange-accounts"] });
    },
  });
}

export function useStoreExchangeKeys() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ accountId, data }: { accountId: string; data: Record<string, unknown> }) => {
      const res = await storeExchangeKeys(accountId, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exchange-accounts"] });
    },
  });
}

export function useConnectors() {
  return useQuery({
    queryKey: ["connectors"],
    queryFn: async () => {
      const res = await fetchConnectors();
      return snakeToCamelObj(res.data);
    },
  });
}
