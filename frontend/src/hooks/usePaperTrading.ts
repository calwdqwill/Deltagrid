import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createPaperAccount,
  fetchPaperAccounts,
  fetchPaperTrades,
  createPaperTrade,
  closePaperTrade,
  fetchPortfolio,
} from "@/lib/api";
import { usePaperStore } from "@/stores/paperStore";

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

export function usePaperAccounts(options?: { enabled?: boolean }) {
  const { setAccounts } = usePaperStore();

  return useQuery({
    queryKey: ["paper-accounts"],
    queryFn: async () => {
      const res = await fetchPaperAccounts();
      const accounts = snakeToCamelObj(res.data);
      setAccounts(accounts);
      return accounts;
    },
    enabled: options?.enabled !== false,
  });
}

export function useCreatePaperAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createPaperAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["paper-accounts"] });
    },
  });
}

export function usePaperTrades(accountId: string | null) {
  const { setTrades } = usePaperStore();

  return useQuery({
    queryKey: ["paper-trades", accountId],
    queryFn: async () => {
      if (!accountId) return [];
      const res = await fetchPaperTrades(accountId);
      const trades = snakeToCamelObj(res.data);
      setTrades(trades);
      return trades;
    },
    enabled: !!accountId,
  });
}

export function useCreatePaperTrade() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ accountId, trade }: { accountId: string; trade: Record<string, unknown> }) => {
      const res = await createPaperTrade(accountId, trade);
      return res.data;
    },
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["paper-trades", vars.accountId] });
      queryClient.invalidateQueries({ queryKey: ["paper-portfolio", vars.accountId] });
    },
  });
}

export function useClosePaperTrade() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ accountId, tradeId, exitPrice }: { accountId: string; tradeId: string; exitPrice: number }) => {
      const res = await closePaperTrade(accountId, tradeId, exitPrice);
      return res.data;
    },
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["paper-trades", vars.accountId] });
      queryClient.invalidateQueries({ queryKey: ["paper-portfolio", vars.accountId] });
    },
  });
}

export function usePortfolio(accountId: string | null) {
  const { setPortfolio } = usePaperStore();

  return useQuery({
    queryKey: ["paper-portfolio", accountId],
    queryFn: async () => {
      if (!accountId) return null;
      const res = await fetchPortfolio(accountId);
      const portfolio = snakeToCamelObj(res.data);
      setPortfolio(portfolio);
      return portfolio;
    },
    enabled: !!accountId,
  });
}
