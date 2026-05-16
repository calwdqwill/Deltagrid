"use client";

import { Search } from "lucide-react";
import { useScannerStore } from "@/stores/scannerStore";
import { useLocale } from "@/hooks/useLocale";
import { useDebounce } from "@/hooks/useDebounce";
import { useEffect, useState } from "react";

export function SearchBar() {
  const { filters, setFilters } = useScannerStore();
  const { t } = useLocale();
  const [value, setValue] = useState(filters.search);
  const debounced = useDebounce(value, 300);

  useEffect(() => {
    setFilters({ search: debounced });
  }, [debounced, setFilters]);

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-text" />
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={t.scanner.searchPlaceholder}
        className="w-72 pl-9 pr-4 py-2 rounded-lg border border-border bg-white text-sm text-primary-text placeholder:text-secondary-text focus:outline-none focus:ring-2 focus:ring-accent-blue/20 focus:border-accent-blue"
      />
    </div>
  );
}
