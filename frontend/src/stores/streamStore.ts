"use client";

import { create } from "zustand";

export interface StreamTick {
  eventType: string;
  symbol: string;
  price: number;
  priceChange24hPct: number | null;
  volume24h: number | null;
  high24h: number | null;
  low24h: number | null;
  source: string;
  timestamp: number | null;
}

interface StreamState {
  connected: boolean;
  ticks: Record<string, StreamTick>;
  lastPingAt: number | null;
  setConnected: (connected: boolean) => void;
  addTick: (tick: StreamTick) => void;
  setLastPing: (ts: number) => void;
}

export const useStreamStore = create<StreamState>((set) => ({
  connected: false,
  ticks: {},
  lastPingAt: null,
  setConnected: (connected) => set({ connected }),
  addTick: (tick) =>
    set((state) => ({
      ticks: { ...state.ticks, [tick.symbol]: tick },
    })),
  setLastPing: (ts) => set({ lastPingAt: ts }),
}));
