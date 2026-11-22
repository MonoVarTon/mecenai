/* Mecenai concierge widget. Add to a page: <script src="/mecenai-widget.js" defer></script>
   The chat lives in an iframe from the Mecenai service, so the host site's styles and scripts stay untouched. */
(function () {
  if (window.__mecenai) return; window.__mecenai = true;
  var BASE = 'https://mecenai.onrender.com';
  var m = location.pathname.match(/^\/gallery\/([a-z0-9-]+)\/?$/);
  var art = m ? m[1] : '';
  var lang = (document.documentElement.lang || navigator.language || 'en').slice(0, 2);
  var css = document.createElement('style');
  css.textContent =
    '.mcn-btn{position:fixed;right:22px;bottom:22px;z-index:2147483000;background:#17150f;color:#efe8dc;border:1px solid #c9a96e;' +
    'border-radius:999px;padding:12px 18px;font:500 14px/1 Inter,system-ui,sans-serif;cursor:pointer;box-shadow:0 8px 30px rgba(0,0,0,.35)}' +
    '.mcn-btn:hover{background:#c9a96e;color:#17150f}' +
    '.mcn-panel{position:fixed;right:22px;bottom:84px;width:380px;height:min(620px,calc(100vh - 110px));z-index:2147483000;' +
    'border:1px solid #2b271f;border-radius:16px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.45);background:#17150f;display:none}' +
    '.mcn-panel.on{display:block}.mcn-panel iframe{width:100%;height:100%;border:0}' +
    '.mcn-wait{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#a39a8a;font:14px Inter,sans-serif;text-align:center;padding:20px}' +
    '@media (max-width:600px){.mcn-panel{right:0;bottom:0;width:100vw;height:100dvh;border-radius:0}.mcn-btn{right:14px;bottom:14px}}';
  document.head.appendChild(css);
  var labels = { ru: 'Спросить о картине', ar: 'اسأل عن لوحة', en: 'Ask about a painting' };
  var waits = { ru: 'Консьерж просыпается… до минуты', ar: 'المساعد يستيقظ… حتى دقيقة', en: 'The concierge is waking up… up to a minute' };
  var L = labels[lang] ? lang : 'en';
  var btn = document.createElement('button');
  btn.className = 'mcn-btn'; btn.type = 'button'; btn.textContent = '✦ ' + labels[L];
  var panel = document.createElement('div'); panel.className = 'mcn-panel';
  panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-label', labels[L]);
  var frame = null;
  function open() {
    if (!frame) {
      var wait = document.createElement('div'); wait.className = 'mcn-wait'; wait.textContent = waits[L];
      panel.appendChild(wait);
      frame = document.createElement('iframe');
      frame.title = labels[L];
      frame.src = BASE + '/embed?lang=' + L + (art ? '&art=' + encodeURIComponent(art) : '');
      frame.onload = function () { wait.remove(); };
      panel.appendChild(frame);
    }
    panel.classList.add('on'); btn.style.display = 'none';
  }
  function close() { panel.classList.remove('on'); btn.style.display = ''; }
  btn.onclick = open;
  window.addEventListener('message', function (e) {
    if (e.origin === BASE && e.data && e.data.mecenai === 'close') close();
  });
  document.body.appendChild(panel); document.body.appendChild(btn);
})();
