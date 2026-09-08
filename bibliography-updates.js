(() => {
  const DOI = '10.1007/s11625-026-01896-8';
  const host = document.getElementById('bibliography-content');
  if (!host) return;

  const normalize = value => (value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
  const isHeading = el => /^H[1-6]$/.test(el?.tagName || '');
  const initials = given => (given || '')
    .split(/\s+/)
    .filter(Boolean)
    .map(token => token
      .split('-')
      .filter(Boolean)
      .map(part => `${part.charAt(0).toUpperCase()}.`)
      .join('-'))
    .join(' ');
  const authorName = author => [initials(author.given), author.family || ''].filter(Boolean).join(' ').trim();
  const yearFrom = meta => {
    const candidates = [meta.published, meta['published-online'], meta['published-print'], meta.issued];
    for (const candidate of candidates) {
      const year = candidate?.['date-parts']?.[0]?.[0];
      if (year) return year;
    }
    return 2026;
  };

  let applied = false;
  const applyUpdate = async () => {
    if (applied || host.getAttribute('aria-busy') !== 'false') return;
    applied = true;

    try {
      const response = await fetch(`https://api.crossref.org/works/${encodeURIComponent(DOI)}`);
      if (!response.ok) throw new Error(`Crossref HTTP ${response.status}`);
      const meta = (await response.json())?.message || {};
      const title = (meta.title?.[0] || '').replace(/<[^>]*>/g, '').trim();
      if (!title) throw new Error('Missing title in Crossref metadata');

      const authors = (meta.author || []).map(authorName).filter(Boolean).join(', ');
      const year = yearFrom(meta);
      const journal = meta['container-title']?.[0] || 'Sustainability Science';
      const volume = meta.volume ? `, ${meta.volume}` : '';
      const issue = meta.issue ? `(${meta.issue})` : '';
      const locator = meta.page
        ? `, ${meta.page}`
        : meta['article-number']
          ? `, article ${meta['article-number']}`
          : '';
      const titleKey = normalize(title);

      // Remove the former submitted / under-review occurrence, or a duplicate DOI entry.
      host.querySelectorAll('li,p').forEach(entry => {
        const text = normalize(entry.textContent);
        const hasSameTitle = titleKey && text.includes(titleKey);
        const hasSameDoi = [...entry.querySelectorAll('a')]
          .some(link => (link.href || '').toLowerCase().includes(DOI.toLowerCase()));
        if (hasSameTitle || hasSameDoi) entry.remove();
      });

      const headings = [...host.querySelectorAll('h2,h3,h4,h5,h6')];
      const publishedHeading = headings.find(heading => {
        const label = normalize(heading.textContent);
        return label === 'publies' || label === 'published';
      });
      if (!publishedHeading) throw new Error('Published section not found');

      let list = publishedHeading.nextElementSibling;
      while (list && !['OL', 'UL'].includes(list.tagName) && !isHeading(list)) list = list.nextElementSibling;
      if (!list || isHeading(list)) {
        list = document.createElement('ol');
        publishedHeading.insertAdjacentElement('afterend', list);
      }

      const li = document.createElement('li');
      li.append(document.createTextNode(`${authors || 'M. Le Mesnil et al.'} (${year}), `));

      const link = document.createElement('a');
      link.href = `https://doi.org/${DOI}`;
      link.target = '_blank';
      link.rel = 'noopener';
      link.textContent = title;
      li.append(link);
      li.append(document.createTextNode('. '));

      const journalSpan = document.createElement('span');
      journalSpan.className = 'smallcaps';
      journalSpan.textContent = journal;
      li.append(journalSpan);
      li.append(document.createTextNode(`${volume}${issue}${locator}.`));

      list.prepend(li);
    } catch (error) {
      console.warn(`Bibliography update failed for DOI ${DOI}`, error);
    }
  };

  const observer = new MutationObserver(() => applyUpdate());
  observer.observe(host, { attributes: true, childList: true, subtree: true });
  applyUpdate();
})();
