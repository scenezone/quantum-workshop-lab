/* Quantum Workshop Lab service worker: offline lessons and app shell. */
const VERSION = 'v1';
const SHELL = `workshop-shell-${VERSION}`;
const ASSETS = `workshop-assets-${VERSION}`;
const DATA = `workshop-data-${VERSION}`;
const SHELL_FILES = ['/', '/index.html', '/manifest.webmanifest', '/quantum-icon.svg'];

// Read-only content that is safe to show from cache when the network is down.
const CACHEABLE_API = [
  /^\/api\/lessons$/,
  /^\/api\/lessons\/[^/]+$/,
  /^\/api\/experiments$/,
  /^\/api\/experiments\/[^/]+\/evolution$/,
  /^\/api\/config\/public$/,
  /^\/api\/challenges$/,
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(SHELL).then((cache) => cache.addAll(SHELL_FILES)));
});

self.addEventListener('activate', (event) => {
  const keep = new Set([SHELL, ASSETS, DATA]);
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => !keep.has(key)).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

async function networkFirst(request, cacheName, fallbackUrl) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(fallbackUrl || request, response.clone());
    return response;
  } catch (error) {
    const cached = await cache.match(fallbackUrl || request);
    if (cached) return cached;
    throw error;
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(ASSETS);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) cache.put(request, response.clone());
  return response;
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    // Every route is the single-page app; cache index.html as the offline shell.
    event.respondWith(networkFirst(request, SHELL, '/index.html'));
  } else if (url.pathname.startsWith('/assets/')) {
    // Vite fingerprints these files, so a cached copy never goes stale.
    event.respondWith(cacheFirst(request));
  } else if (CACHEABLE_API.some((pattern) => pattern.test(url.pathname))) {
    event.respondWith(networkFirst(request, DATA));
  }
  // Everything else, including simulations, hardware jobs, and sessions, uses the network only.
});
