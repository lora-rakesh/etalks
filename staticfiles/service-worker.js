const CACHE_NAME = 'aihr4u-cache-v1';
const urlsToCache = ['/', '/static/css/base.css','/static/css/index.css','/static/css/dashboard.css'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)));
});
self.addEventListener('fetch', e => {
  e.respondWith(caches.match(e.request).then(res => res || fetch(e.request)));
});