import { useEffect } from "react";
import { useUIStore } from "@/stores/uiStore";
import { getDictionary, Dictionary } from "@/i18n";

export function useLocale(): { locale: string; t: Dictionary } {
  const { locale, setLocale } = useUIStore();

  useEffect(() => {
    const saved = localStorage.getItem("deltagrid_locale");
    if (saved && saved !== locale) {
      setLocale(saved);
    }
  }, [locale, setLocale]);

  const dictionary = getDictionary(locale);
  return { locale, t: dictionary };
}
