import { create } from "zustand";
import { ScannerPreferences } from "@/types/preferences";

interface PreferenceState {
  preferences: ScannerPreferences | null;
  favorites: Set<string>;
  pinned: Set<string>;
  setPreferences: (prefs: ScannerPreferences) => void;
  setFavorites: (ids: string[]) => void;
  setPinned: (ids: string[]) => void;
  toggleFavoriteLocal: (id: string) => void;
  togglePinnedLocal: (id: string) => void;
}

export const usePreferenceStore = create<PreferenceState>((set) => ({
  preferences: null,
  favorites: new Set(),
  pinned: new Set(),
  setPreferences: (preferences) => set({ preferences }),
  setFavorites: (ids) => set({ favorites: new Set(ids) }),
  setPinned: (ids) => set({ pinned: new Set(ids) }),
  toggleFavoriteLocal: (id) =>
    set((state) => {
      const next = new Set(state.favorites);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { favorites: next };
    }),
  togglePinnedLocal: (id) =>
    set((state) => {
      const next = new Set(state.pinned);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { pinned: next };
    }),
}));
