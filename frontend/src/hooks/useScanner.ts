import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { fetchScanner, toggleFavorite, togglePinned } from "@/lib/api";
import { useScannerStore } from "@/stores/scannerStore";
import { usePreferenceStore } from "@/stores/preferenceStore";

export function useScannerData(refreshInterval: number = 60) {
  const { filters, setData, setLoading, setError, setFilteredRecords } = useScannerStore();
  const { favorites, pinned } = usePreferenceStore();

  const query = useQuery({
    queryKey: ["scanner", filters],
    queryFn: async () => {
      const params: Record<string, unknown> = {};
      if (filters.type && filters.type !== "all") params.type = filters.type;
      if (filters.minSpread > 0) params.min_spread = filters.minSpread;
      if (filters.minVolume) params.min_volume = filters.minVolume;
      if (filters.search) params.search = filters.search;
      if (filters.positiveNetOnly) params.positive_net_only = true;

      const res = await fetchScanner(params);
      return res.data;
    },
    refetchInterval: refreshInterval * 1000,
    refetchIntervalInBackground: false,
  });

  useEffect(() => {
    setLoading(query.isLoading);
    if (query.isError) {
      setError(true, (query.error as Error)?.message || "Unknown error");
    } else {
      setError(false, "");
    }
    if (query.data) {
      setData(query.data);
      let records = query.data.records;

      // Client-side filter for favorites/pinned tabs
      if (filters.type === "favorites") {
        records = records.filter((r) => favorites.has(r.id) || r.isFavorite);
      }
      if (filters.type === "pinned") {
        records = records.filter((r) => pinned.has(r.id) || r.isPinned);
      }

      setFilteredRecords(records);
    }
  }, [query.data, query.isLoading, query.isError, filters, favorites, pinned, setData, setLoading, setError, setFilteredRecords]);

  return query;
}

export function useToggleFavorite() {
  const queryClient = useQueryClient();
  const { toggleFavoriteLocal } = usePreferenceStore();

  return useMutation({
    mutationFn: async (instrumentId: string) => {
      toggleFavoriteLocal(instrumentId);
      const res = await toggleFavorite(instrumentId);
      return res.data;
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["scanner"] });
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
    },
  });
}

export function useTogglePinned() {
  const queryClient = useQueryClient();
  const { togglePinnedLocal } = usePreferenceStore();

  return useMutation({
    mutationFn: async (instrumentId: string) => {
      togglePinnedLocal(instrumentId);
      const res = await togglePinned(instrumentId);
      return res.data;
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["scanner"] });
      queryClient.invalidateQueries({ queryKey: ["pinned"] });
    },
  });
}
