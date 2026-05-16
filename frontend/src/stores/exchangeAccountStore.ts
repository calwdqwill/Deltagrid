"use client";

import { create } from "zustand";

export interface ExchangeAccount {
  id: string;
  exchangeName: string;
  accountLabel: string;
  accountType: string;
  isActive: boolean;
  isDefault: boolean;
  hasKeys: boolean;
  createdAt: string;
  updatedAt: string;
}

interface ExchangeAccountState {
  accounts: ExchangeAccount[];
  selectedAccountId: string | null;
  setAccounts: (accounts: ExchangeAccount[]) => void;
  selectAccount: (id: string | null) => void;
  addAccount: (account: ExchangeAccount) => void;
  removeAccount: (id: string) => void;
}

export const useExchangeAccountStore = create<ExchangeAccountState>((set) => ({
  accounts: [],
  selectedAccountId: null,
  setAccounts: (accounts) => set({ accounts }),
  selectAccount: (id) => set({ selectedAccountId: id }),
  addAccount: (account) => set((state) => ({ accounts: [account, ...state.accounts] })),
  removeAccount: (id) =>
    set((state) => ({
      accounts: state.accounts.filter((a) => a.id !== id),
      selectedAccountId: state.selectedAccountId === id ? null : state.selectedAccountId,
    })),
}));
