"use client";

import { create } from "zustand";

export interface PaperAccount {
  id: string;
  name: string;
  initialBalance: number;
  currentBalance: number;
  currency: string;
}

export interface PaperTrade {
  id: string;
  strategy: string;
  instrumentId: string;
  side: string;
  entryPrice: number;
  exitPrice?: number;
  quantity: number;
  status: string;
  pnl?: number;
  openedAt: string;
}

interface PaperState {
  accounts: PaperAccount[];
  selectedAccountId: string | null;
  trades: PaperTrade[];
  portfolio: {
    currentBalance: number;
    totalPnl: number;
    openTrades: number;
    closedTrades: number;
  } | null;
  setAccounts: (accounts: PaperAccount[]) => void;
  selectAccount: (id: string | null) => void;
  setTrades: (trades: PaperTrade[]) => void;
  setPortfolio: (portfolio: PaperState["portfolio"]) => void;
  addTrade: (trade: PaperTrade) => void;
}

export const usePaperStore = create<PaperState>((set) => ({
  accounts: [],
  selectedAccountId: null,
  trades: [],
  portfolio: null,
  setAccounts: (accounts) => set({ accounts }),
  selectAccount: (id) => set({ selectedAccountId: id }),
  setTrades: (trades) => set({ trades }),
  setPortfolio: (portfolio) => set({ portfolio }),
  addTrade: (trade) => set((state) => ({ trades: [trade, ...state.trades] })),
}));
