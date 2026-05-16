import { Dictionary } from "./types";
export type { Dictionary } from "./types";
import { en } from "./dictionaries/en";
import { ru } from "./dictionaries/ru";

const dictionaries: Record<string, Dictionary> = {
  en,
  ru,
};

export function getDictionary(locale: string): Dictionary {
  return dictionaries[locale] || dictionaries.en;
}

export const availableLocales = [
  { code: "en", label: "English" },
  { code: "ru", label: "Русский" },
];
