const CACHE_NAME = "flask-pwa-v1";
const urlsToCache = [
  "/",
    "/static/css/account.css",
    "/static/css/dashboard.css",
    "/static/css/history.css",
    "/static/css/lang_select.css",
    "/static/css/login.css",
    "/static/css/logo.css",
    "/static/css/mainpage.css",
  "/static/css/register.css",
  "/static/js/home.js",
  "/static/js/script.js",
  "/static/imges/tamilapp.png",
];

// Install
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

// Fetch
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});