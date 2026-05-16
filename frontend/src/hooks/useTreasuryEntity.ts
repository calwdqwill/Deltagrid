import { useQuery } from "@tanstack/react-query";
import { fetchTreasuryEntity } from "@/lib/api";

export interface TreasuryEntityDetail {
  id: string;
  entityType: string;
  name: string;
  ticker?: string;
  sector?: string;
  description?: string;
  websiteUrl?: string;
  isActive: boolean;
  latestSnapshot?: {
    btcHoldings: number | null;
    btcValueUsd: number | null;
    btcPerShare: number | null;
    source: string;
    sourceQuality: string;
    reportDate: string | null;
  };
  createdAt?: string;
  updatedAt?: string;
}

export function useTreasuryEntity(id: string) {
  return useQuery<TreasuryEntityDetail>({
    queryKey: ["treasuryEntity", id],
    queryFn: async () => {
      const res = await fetchTreasuryEntity(id);
      return res.data as unknown as TreasuryEntityDetail;
    },
    enabled: !!id,
    staleTime: 1000 * 60 * 30,
  });
}
