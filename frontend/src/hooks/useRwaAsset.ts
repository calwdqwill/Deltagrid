import { useQuery } from "@tanstack/react-query";
import { fetchRwaAsset } from "@/lib/api";

export interface RwaAssetDetail {
  id: string;
  symbol: string;
  name: string;
  category: string;
  assetClass: string;
  issuer?: string;
  blockchain?: string;
  contractAddress?: string;
  decimals?: number;
  isActive: boolean;
  isExecutable: boolean;
  latestSnapshot?: {
    priceUsd: number | null;
    navUsd: number | null;
    marketCapUsd: number | null;
    source: string;
    sourceQuality: string;
    fetchedAt: string;
  };
  createdAt?: string;
  updatedAt?: string;
}

export function useRwaAsset(id: string) {
  return useQuery<RwaAssetDetail>({
    queryKey: ["rwaAsset", id],
    queryFn: async () => {
      const res = await fetchRwaAsset(id);
      return res.data as unknown as RwaAssetDetail;
    },
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}
