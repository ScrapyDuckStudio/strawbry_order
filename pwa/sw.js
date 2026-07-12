const CACHE_NAME = 'strawberry-pwa-v1';
const STREAMLIT_URL = 'https://scrapyduckstudio-strawbry-order.streamlit.app';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

// Network first — we don't cache the Streamlit app itself
self.addEventListener('fetch', (event) => {
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});

// Push notification
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  event.waitUntil(
    self.registration.showNotification(data.title || '🍓 New Order!', {
      body: data.body || 'A new order has been placed.',
      icon: './icon-192.png',
      badge: './icon-192.png',
      tag: data.tag || 'strawberry-order',
      vibrate: [200, 100, 200],
      requireInteraction: true,
    })
  );
});

// Click notification → open/focus app
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
      if (list.length > 0) return list[0].focus();
      return self.clients.openWindow('./index.html');
    })
  );
});
