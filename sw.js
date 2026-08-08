/* Офлайн-режим реестра ЮСИ.
   Меняя index.html, увеличьте номер версии — иначе браузер отдаст старую копию. */
const V='usi-v6';
const CORE=['./','./index.html','./data.json','./manifest.webmanifest',
            './icon-192.png','./icon-512.png','./apple-touch-icon.png'];

self.addEventListener('install',e=>{
  e.waitUntil(caches.open(V).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k))))
    .then(()=>self.clients.claim()));
});
self.addEventListener('fetch',e=>{
  const url=new URL(e.request.url);
  if(e.request.method!=='GET') return;
  // счётчики — мимо кэша
  if(/counterapi|countapi/.test(url.href)) return;
  // данные реестра: всегда сеть, кэш только как аварийный запас
  if(url.pathname.endsWith('data.json')){
    e.respondWith(fetch(e.request).then(r=>{
      const copy=r.clone(); caches.open(V).then(c=>c.put(e.request,copy)); return r;
    }).catch(()=>caches.match(e.request)));
    return;
  }
  // свои файлы: сначала сеть, при отказе — кэш
  if(url.origin===location.origin){
    e.respondWith(
      fetch(e.request).then(r=>{
        const copy=r.clone();caches.open(V).then(c=>c.put(e.request,copy));return r;
      }).catch(()=>caches.match(e.request).then(r=>r||caches.match('./index.html')))
    );
  }
});
