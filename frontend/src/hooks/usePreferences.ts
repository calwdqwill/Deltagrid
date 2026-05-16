import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { fetchPreferences, updatePreferences, fetchFavorites, fetchPinned } from "@/lib/api";
import { usePreferenceStore } from "@/stores/preferenceStore";
import { ScannerPreferences } from "@/types/preferences";

export function usePreferences() {
  const { setPreferences, setFavorites, setPinned } = usePreferenceStore();

  const prefsQuery = useQuery({
    queryKey: ["preferences"],
    queryFn: async () => {
      const res = await fetchPreferences();
      return res.data;
    },
  });

  const favQuery = useQuery({
    queryKey: ["favorites"],
    queryFn: async () => {
      const res = await fetchFavorites();
      return res.data.instrumentIds;
    },
  });

  const pinnedQuery = useQuery({
    queryKey: ["pinned"],
    queryFn: async () => {
      const res = await fetchPinned();
      return res.data.instrumentIds;
    },
  });

  useEffect(() => {
    if (prefsQuery.data) setPreferences(prefsQuery.data);
  }, [prefsQuery.data, setPreferences]);

  useEffect(() => {
    if (favQuery.data) setFavorites(favQuery.data);
  }, [favQuery.data, setFavorites]);

  useEffect(() => {
    if (pinnedQuery.data) setPinned(pinnedQuery.data);
  }, [pinnedQuery.data, setPinned]);

  return {
    preferences: prefsQuery.data,
    isLoading: prefsQuery.isLoading || favQuery.isLoading || pinnedQuery.isLoading,
  };
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (prefs: ScannerPreferences) => {
      const res = await updatePreferences(prefs);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
    },
  });
}
