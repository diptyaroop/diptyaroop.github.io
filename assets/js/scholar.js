/* Load verified metrics from this repository, never scrape Scholar in a visitor's browser. */
(() => {
  const verified = document.querySelector('#scholar-verified');
  const stale = document.querySelector('#scholar-stale');
  if (!verified) return;
  const sources = ['assets/data/scholar.json'];
  // Raw GitHub supports CORS and receives bot commits without a Pages rebuild.
  if (location.hostname === 'diptyaroop.github.io') {
    sources.unshift('https://raw.githubusercontent.com/diptyaroop/diptyaroop.github.io/master/assets/data/scholar.json');
  }
  let newest = Date.parse(verified.dateTime);
  const updateAge = () => {
    stale.textContent = Date.now() - newest > 2 * 86400000 ? ' · Last known values; see Scholar for the latest.' : '';
  };
  async function refresh() {
    for (const source of sources) {
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 10000);
        let response;
        let data;
        try {
          response = await fetch(source, { cache: 'no-store', signal: controller.signal });
          if (!response.ok) throw new Error('Metrics unavailable');
          data = await response.json();
        } finally { clearTimeout(timer); }
        const checked = Date.parse(data.checked_at);
        if (data.scholar_id !== 'QkURxEAAAAAJ' || !Number.isInteger(data.citations) || data.citations < 0 ||
            !Number.isInteger(data.h_index) || data.h_index < 0 || data.h_index ** 2 > data.citations ||
            !Number.isFinite(checked) || checked > Date.now() + 300000 || checked < newest) continue;
        document.querySelector('[data-scholar="citations"]').textContent = data.citations.toLocaleString('en-US');
        document.querySelector('[data-scholar="h_index"]').textContent = String(data.h_index);
        verified.dateTime = data.checked_at;
        verified.textContent = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(checked));
        newest = checked;
        updateAge();
        // Try the local fallback when the remote snapshot is stale.
        if (Date.now() - checked <= 2 * 86400000) return;
      } catch (_) { /* Preserve the labeled last-known values on network/parse failures. */ }
    }
    updateAge();
  }
  updateAge();
  refresh();
  // Keep long-lived tabs up to date as well as newly opened pages.
  setInterval(() => { if (!document.hidden) refresh(); }, 30 * 60 * 1000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
})();
