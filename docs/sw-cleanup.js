// This file only exists to unregister old broken service workers
// It will be served once, then the SW will self-destruct
self.addEventListener('install', function() { self.skipWaiting(); });
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(names) {
      return Promise.all(names.map(function(n) { return caches.delete(n); }));
    }).then(function() {
      // Unregister ourselves
      return self.registration.unregister();
    }).then(function() {
      return self.clients.claim();
    })
  );
});
