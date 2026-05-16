import { useQuery } from "@tanstack/react-query";
import { fetchTreasuryEntities, fetchBtcHoldings, fetchTokenizationPlatforms } from "@/lib/api";

export function useTreasuryEntities(entityType?: string) {
  return useQuery({
    queryKey: ["treasuryEntities", entityType],
    queryFn: async () => {
      const res = await fetchTreasuryEntities(entityType);
      return res.data ?? [];
    },
    staleTime: 1000 * 60 * 30,
  });
}

export function useBtcHoldings() {
  return useQuery({
    queryKey: ["btcHoldings"],
    queryFn: async () => {
      const res = await fetchBtcHoldings();
      return res.data ?? [];
    },
    staleTime: 1000 * 60 * 30,
  });
}

export function useTokenizationPlatforms() {
  return useQuery({
    queryKey: ["tokenizationPlatforms"],
    queryFn: async () => {
      const res = await fetchTokenizationPlatforms();
      return res.data ?? [];
    },
    staleTime: 1000 * 60 * 30,
  });
}
