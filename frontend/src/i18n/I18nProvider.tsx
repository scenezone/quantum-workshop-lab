import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { I18nContext, pickInitialLocale, STORAGE_KEY } from './context';
import { en, LOCALES, type MessageKey } from './messages';

export default function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState(pickInitialLocale);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = LOCALES[locale]?.dir ?? 'ltr';
  }, [locale]);

  const setLocale = useCallback((next: string) => {
    if (!LOCALES[next]) return;
    setLocaleState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // The choice still applies for this page when storage is unavailable.
    }
  }, []);

  const t = useCallback((key: MessageKey) => LOCALES[locale]?.messages[key] ?? en[key], [locale]);
  const value = useMemo(() => ({ locale, setLocale, t, locales: Object.entries(LOCALES).map(([id, item]) => ({ id, label: item.label })) }),
    [locale, setLocale, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
