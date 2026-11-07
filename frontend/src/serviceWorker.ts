/** Registers public/sw.js in production builds so lessons keep working on poor venue Wi-Fi. */
export function registerServiceWorker() {
  if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return;
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then((registration) => {
      const announce = (worker: ServiceWorker | null) => {
        if (worker && navigator.serviceWorker.controller) {
          window.dispatchEvent(new CustomEvent('workshop-update-ready', { detail: worker }));
        }
      };
      announce(registration.waiting);
      registration.addEventListener('updatefound', () => {
        const installing = registration.installing;
        installing?.addEventListener('statechange', () => {
          if (installing.state === 'installed') announce(installing);
        });
      });
    }).catch(() => {
      // The app works normally without offline support.
    });
    let reloading = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (reloading) return;
      reloading = true;
      window.location.reload();
    });
  });
}
