"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchTrending, fetchGainers, fetchLosers, fetchGlobal, fetchFearGreed, fetchNewListings, fetchFundingRates } from "@/lib/api";

export function useMarketData(refetchInterval = 60000) {
  const trendingQuery = useQuery({
    queryKey: ["market", "trending"],
    queryFn: async () => {
      const res = await fetchTrending();
      return res.data;
    },
    refetchInterval,
    staleTime: 30000,
  });

  const gainersQuery = useQuery({
    queryKey: ["market", "gainers"],
    queryFn: async () => {
      const res = await fetchGainers();
      return res.data;
    },
    refetchInterval,
    staleTime: 30000,
  });

  const losersQuery = useQuery({
    queryKey: ["market", "losers"],
    queryFn: async () => {
      const res = await fetchLosers();
      return res.data;
    },
    refetchInterval,
    staleTime: 30000,
  });

  const globalQuery = useQuery({
    queryKey: ["market", "global"],
    queryFn: async () => {
      const res = await fetchGlobal();
      return res.data;
    },
    refetchInterval,
    staleTime: 30000,
  });

  const fearGreedQuery = useQuery({
    queryKey: ["market", "fear-greed"],
    queryFn: async () => {
      const res = await fetchFearGreed();
      return res.data;
    },
    refetchInterval: 3600000,
    staleTime: 1800000,
  });

  const newListingsQuery = useQuery({
    queryKey: ["market", "new-listings"],
    queryFn: async () => {
      const res = await fetchNewListings();
      return res.data;
    },
    refetchInterval,
    staleTime: 30000,
  });

  const fundingRatesQuery = useQuery({
    queryKey: ["market", "funding-rates"],
    queryFn: async () => {
      const res = await fetchFundingRates();
      return res.data;
    },
    refetchInterval: 300000,
    staleTime: 120000,
  });

  const isLoading =
    trendingQuery.isLoading ||
    gainersQuery.isLoading ||
    losersQuery.isLoading ||
    globalQuery.isLoading ||
    fearGreedQuery.isLoading ||
    newListingsQuery.isLoading ||
    fundingRatesQuery.isLoading;

  const isError =
    trendingQuery.isError ||
    gainersQuery.isError ||
    losersQuery.isError ||
    globalQuery.isError ||
    fearGreedQuery.isError ||
    newListingsQuery.isError ||
    fundingRatesQuery.isError;

  return {
    trending: trendingQuery.data ?? [],
    gainers: gainersQuery.data ?? [],
    losers: losersQuery.data ?? [],
    global: globalQuery.data ?? null,
    fearGreed: fearGreedQuery.data ?? [],
    newListings: newListingsQuery.data ?? [],
    fundingRates: fundingRatesQuery.data ?? [],
    isLoading,
    isError,
    refetch: () => {
      trendingQuery.refetch();
      gainersQuery.refetch();
      losersQuery.refetch();
      globalQuery.refetch();
      fearGreedQuery.refetch();
      newListingsQuery.refetch();
      fundingRatesQuery.refetch();
    },
  };
}
