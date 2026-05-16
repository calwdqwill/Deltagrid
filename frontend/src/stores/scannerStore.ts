import { create } from "zustand";
import { ScannerRecord, ScannerFilters, ScannerListResponse } from "@/types/scanner";

interface ScannerState {
  data: ScannerListResponse | null;
  filteredRecords: ScannerRecord[];
  isLoading: boolean;
  isError: boolean;
  errorMessage: string;
  filters: ScannerFilters;
  selectedRecordId: string | null;
  setData: (data: ScannerListResponse | null) => void;
  setFilteredRecords: (records: ScannerRecord[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: boolean, message?: string) => void;
  setFilters: (filters: Partial<ScannerFilters>) => void;
  setSelectedRecordId: (id: string | null) => void;
}

export const useScannerStore = create<ScannerState>((set) => ({
  data: null,
  filteredRecords: [],
  isLoading: false,
  isError: false,
  errorMessage: "",
  filters: {
    type: "all",
    minSpread: 0.1,
    search: "",
    positiveNetOnly: false,
  },
  selectedRecordId: null,
  setData: (data) => set({ data }),
  setFilteredRecords: (filteredRecords) => set({ filteredRecords }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (isError, errorMessage = "") => set({ isError, errorMessage }),
  setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),
  setSelectedRecordId: (selectedRecordId) => set({ selectedRecordId }),
}));
