import { useQuery } from "@tanstack/react-query";
import { fetchRwaAssets, fetchRwaCategories } from "@/lib/api";

export function useRwaAssets(category?: string) {
  return useQuery({
    queryKey: ["rwaAssets", category],
    queryFn: async () => {
      const res = await fetchRwaAssets(category);
      return res.data ?? [];
    },
    staleTime: 1000 * 60 * 5,
  });
}

export function useRwaCategories() {
  return useQuery({
    queryKey: ["rwaCategories"],
    queryFn: async () => {
      const res = await fetchRwaCategories();
      return res.data ?? [];
    },
    staleTime: 1000 * 60 * 5,
  });
}
