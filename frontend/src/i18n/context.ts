import { createContext, useContext } from 'react';
import { en, LOCALES, type MessageKey } from './messages';

export const STORAGE_KEY = 'quantum-workshop-locale-v1';

export interface I18nValue {
  locale: string;
  setLocale: (locale: string) => void;
  t: (key: MessageKey) => string;
  locales: { id: string; label: string }[];
}

export const I18nContext = createContext<I18nValue | null>(null);

export function pickInitialLocale(): string {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && LOCALES[saved]) return saved;
  } catch {
    // Fall back to the browser language.
  }
  const preferred = typeof navigator !== 'undefined' ? navigator.languages ?? [navigator.language] : [];
  for (const language of preferred) {
    const base = language?.toLowerCase().split('-')[0];
    if (base && LOCALES[base]) return base;
  }
  return 'en';
}

const fallback: I18nValue = { locale: 'en', setLocale: () => undefined, t: (key) => en[key], locales: [{ id: 'en', label: 'English' }] };

/** Works without a provider (for isolated component tests), defaulting to English. */
export function useI18n(): I18nValue {
  return useContext(I18nContext) ?? fallback;
}
