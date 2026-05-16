"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface User {
  id: string;
  email: string | null;
  username: string | null;
  plan: string;
  featureFlags?: Record<string, string>;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  hasFeature: (key: string) => boolean;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setRefreshToken: (token: string | null) => void;
  login: (user: User, token: string, refreshToken?: string) => void;
  logout: () => void;
}

function isValidToken(token: unknown): token is string {
  return typeof token === "string" && token.split(".").length === 3;
}

function parseFeatureFlagValue(value: string | undefined): boolean {
  if (value === undefined || value === null) return false;
  const lowered = String(value).toLowerCase();
  return lowered === "true" || lowered === "1" || lowered === "enabled" || lowered === "yes";
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      hasFeature: (key: string) => {
        const flags = get().user?.featureFlags;
        if (!flags) return false;
        return parseFeatureFlagValue(flags[key]);
      },
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token }),
      setRefreshToken: (refreshToken) => set({ refreshToken }),
      login: (user, token, refreshToken) =>
        set({ user, token, refreshToken: refreshToken || null, isAuthenticated: true }),
      logout: () =>
        set({ user: null, token: null, refreshToken: null, isAuthenticated: false }),
    }),
    {
      name: "deltagrid_auth",
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        if (state && !isValidToken(state.token)) {
          state.token = null;
          state.refreshToken = null;
          state.user = null;
          state.isAuthenticated = false;
        }
      },
    }
  )
);
