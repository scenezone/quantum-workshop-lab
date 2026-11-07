import { WifiOff } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useI18n } from '../i18n/context';

function useOnline() {
  const [online, setOnline] = useState(() => typeof navigator === 'undefined' || navigator.onLine !== false);
  useEffect(() => {
    const update = () => setOnline(navigator.onLine !== false);
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    return () => {
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
    };
  }, []);
  return online;
}

/** Offline notice and the "new version available" prompt from the service worker. */
export default function AppStatusBanner() {
  const online = useOnline();
  const { t } = useI18n();
  const [update, setUpdate] = useState<ServiceWorker | null>(null);

  useEffect(() => {
    const onUpdate = (event: Event) => setUpdate((event as CustomEvent<ServiceWorker>).detail);
    window.addEventListener('workshop-update-ready', onUpdate);
    return () => window.removeEventListener('workshop-update-ready', onUpdate);
  }, []);

  if (online && !update) return null;
  return (
    <div className="border-b border-amber-300/20 bg-amber-300/10 px-4 py-2 text-center text-sm text-amber-100" role="status">
      {!online && <span className="inline-flex items-center gap-2"><WifiOff className="h-4 w-4" aria-hidden="true" />{t('offline.notice')}</span>}
      {online && update && <span>
        {t('update.ready')}{' '}
        <button type="button" className="underline" onClick={() => update.postMessage({ type: 'SKIP_WAITING' })}>{t('update.reload')}</button>
      </span>}
    </div>
  );
}
