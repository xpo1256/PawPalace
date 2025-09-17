self.addEventListener('install', (event) => {
  event.waitUntil(caches.open('pawpalace-v1').then((cache) => cache.addAll([
    '/',
  ])));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});

// Show notifications if a push comes (placeholder – requires Web Push setup)
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'PawPalace';
  const options = {
    body: data.body || '',
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-192.png'
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

