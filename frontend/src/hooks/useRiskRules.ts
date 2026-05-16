import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchRiskRules,
  createRiskRule,
  deleteRiskRule,
  dryRunRiskCheck,
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

export function useRiskRules(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["risk-rules"],
    queryFn: async () => {
      const res = await fetchRiskRules();
      return snakeToCamelObj(res.data);
    },
    enabled: options?.enabled !== false,
  });
}

export function useCreateRiskRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createRiskRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["risk-rules"] });
    },
  });
}

export function useDeleteRiskRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteRiskRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["risk-rules"] });
    },
  });
}

export function useDryRunRiskCheck() {
  return useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await dryRunRiskCheck(data);
      return snakeToCamelObj(res.data);
    },
  });
}
