import { create } from "zustand";

interface UIState {
  sidebarOpen: boolean;
  detailOpen: boolean;
  locale: string;
  toggleSidebar: () => void;
  setDetailOpen: (open: boolean) => void;
  setLocale: (locale: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  detailOpen: false,
  locale: "en",
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setDetailOpen: (detailOpen) => set({ detailOpen }),
  setLocale: (locale) => {
    localStorage.setItem("deltagrid_locale", locale);
    set({ locale });
  },
}));
