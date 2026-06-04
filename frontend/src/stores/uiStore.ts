import { create } from "zustand";

export interface WorkspaceTab {
  id: string;
  label: string;
  href: string;
  context?: string;
}

interface UIState {
  sidebarOpen: boolean;
  detailOpen: boolean;
  locale: string;
  workspaceTabs: WorkspaceTab[];
  activeWorkspaceTabId: string;
  toggleSidebar: () => void;
  setDetailOpen: (open: boolean) => void;
  setLocale: (locale: string) => void;
  openWorkspaceTab: (tab: WorkspaceTab) => void;
  closeWorkspaceTab: (id: string) => void;
  setActiveWorkspaceTab: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  detailOpen: false,
  locale: "en",
  workspaceTabs: [
    {
      id: "market-overview",
      label: "Market Overview",
      href: "/market",
      context: "Command Center",
    },
  ],
  activeWorkspaceTabId: "market-overview",
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setDetailOpen: (detailOpen) => set({ detailOpen }),
  setLocale: (locale) => {
    localStorage.setItem("deltagrid_locale", locale);
    set({ locale });
  },
  openWorkspaceTab: (tab) =>
    set((state) => {
      const exists = state.workspaceTabs.some((item) => item.id === tab.id);
      return {
        workspaceTabs: exists ? state.workspaceTabs : [...state.workspaceTabs, tab],
        activeWorkspaceTabId: tab.id,
      };
    }),
  closeWorkspaceTab: (id) =>
    set((state) => {
      const nextTabs = state.workspaceTabs.filter((tab) => tab.id !== id);
      const fallback = nextTabs[0] ?? {
        id: "market-overview",
        label: "Market Overview",
        href: "/market",
        context: "Command Center",
      };
      return {
        workspaceTabs: nextTabs.length > 0 ? nextTabs : [fallback],
        activeWorkspaceTabId:
          state.activeWorkspaceTabId === id ? fallback.id : state.activeWorkspaceTabId,
      };
    }),
  setActiveWorkspaceTab: (id) => set({ activeWorkspaceTabId: id }),
}));
