(() => {
  const host = document.getElementById('bibliography-content');
  if (!host) return;

  const normalize = value => (value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[–—]/g, '-')
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  const doiFromEntry = entry => {
    for (const link of entry.querySelectorAll('a[href]')) {
      const href = link.getAttribute('href') || '';
      const match = href.match(/doi\.org\/(10\.\d{4,9}\/[^?#\s]+)/i);
      if (match) return decodeURIComponent(match[1]).toLowerCase();
    }
    const match = entry.textContent.match(/\b(10\.\d{4,9}\/[^\s<>]+)/i);
    return match ? match[1].replace(/[.,;)]$/, '').toLowerCase() : '';
  };

  const titleFromEntry = entry => {
    const links = [...entry.querySelectorAll('a[href]')].filter(link => {
      const href = link.getAttribute('href') || '';
      return !/hal\.science|archives-ouvertes\.fr/i.test(href);
    });
    if (links.length) return links[0].textContent.trim();

    const text = entry.textContent.replace(/\s+/g, ' ').trim();
    const afterYear = text.match(/\(\d{4}\),?\s*(.+?)(?:\.\s+[A-ZÀ-ÖØ-Ý][^.]{2,}|$)/);
    return (afterYear?.[1] || text).trim();
  };

  const enrichWithHal = async () => {
    try {
      const params = new URLSearchParams({
        q: 'authFullName_s:"Jean-Raynald de Dreuzy"',
        fl: 'title_s,uri_s,doiId_s',
        rows: '500',
        wt: 'json'
      });
      const response = await fetch(`https://api.archives-ouvertes.fr/search/?${params.toString()}`);
      if (!response.ok) return;
      const docs = (await response.json())?.response?.docs || [];

      const byDoi = new Map();
      const byTitle = new Map();
      docs.forEach(doc => {
        const uri = doc.uri_s;
        if (!uri) return;
        const titles = Array.isArray(doc.title_s) ? doc.title_s : [doc.title_s];
        titles.filter(Boolean).forEach(title => byTitle.set(normalize(title), uri));
        const dois = Array.isArray(doc.doiId_s) ? doc.doiId_s : [doc.doiId_s];
        dois.filter(Boolean).forEach(doi => byDoi.set(String(doi).toLowerCase(), uri));
      });

      host.querySelectorAll('li, p').forEach(entry => {
        if (entry.querySelector('.hal-link') || !entry.textContent.trim()) return;
        const title = titleFromEntry(entry);
        const doi = doiFromEntry(entry);
        const exact = (doi && byDoi.get(doi)) || byTitle.get(normalize(title));
        if (!exact) return;

        const link = document.createElement('a');
        link.className = 'hal-link';
        link.href = exact;
        link.target = '_blank';
        link.rel = 'noopener';
        link.textContent = '[HAL]';
        entry.append(document.createTextNode(' '), link);
      });
    } catch (_) {
      // HAL is optional: bibliography remains fully usable if the service is unavailable.
    }
  };

  const scheduleEnrichment = () => {
    const run = () => setTimeout(enrichWithHal, 600);
    if ('requestIdleCallback' in window) requestIdleCallback(run, { timeout: 1500 });
    else run();
  };

  if (host.getAttribute('aria-busy') === 'false') {
    scheduleEnrichment();
  } else {
    const readyObserver = new MutationObserver(() => {
      if (host.getAttribute('aria-busy') !== 'false') return;
      readyObserver.disconnect();
      scheduleEnrichment();
    });
    readyObserver.observe(host, { attributes: true, attributeFilter: ['aria-busy'] });
  }
})();
