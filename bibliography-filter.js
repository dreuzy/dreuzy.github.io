(() => {
  const host = document.getElementById('bibliography-content');
  const form = document.getElementById('bibliography-filters');
  if (!host || !form) return;

  const search = document.getElementById('bib-search');
  const type = document.getElementById('bib-type');
  const year = document.getElementById('bib-year');
  const count = document.getElementById('bibliography-count');
  const entries = [...host.querySelectorAll('li[data-bib-id]')];
  const language = document.documentElement.lang === 'fr' ? 'fr' : 'en';

  const normalize = value => (value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase()
    .replace(/\s+/g, ' ')
    .trim();

  [...new Set(entries.map(entry => entry.dataset.bibYear).filter(Boolean))]
    .sort((a, b) => Number(b) - Number(a))
    .forEach(value => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      year.append(option);
    });

  const apply = () => {
    const words = normalize(search.value);
    const selectedType = type.value;
    const selectedYear = year.value;
    let visible = 0;
    entries.forEach(entry => {
      const matches = (!words || normalize(entry.textContent).includes(words)) &&
        (!selectedType || entry.dataset.bibSection === selectedType) &&
        (!selectedYear || entry.dataset.bibYear === selectedYear);
      entry.classList.toggle('bib-filter-hidden', !matches);
      if (matches) visible += 1;
    });

    host.querySelectorAll('ol[data-bib-section], ul[data-bib-section]').forEach(list => {
      const listVisible = [...list.querySelectorAll(':scope > li[data-bib-id]')]
        .some(entry => !entry.classList.contains('bib-filter-hidden'));
      list.classList.toggle('bib-filter-hidden', !listVisible);
      const groupHeading = document.getElementById(list.dataset.bibGroup);
      if (groupHeading?.dataset.bibHeading === 'group') {
        groupHeading.classList.toggle('bib-filter-hidden', !listVisible);
      }
    });
    host.querySelectorAll('h2[data-bib-heading="section"]').forEach(heading => {
      const sectionVisible = entries.some(entry => entry.dataset.bibSection === heading.id &&
        !entry.classList.contains('bib-filter-hidden'));
      heading.classList.toggle('bib-filter-hidden', !sectionVisible);
    });
    count.textContent = language === 'fr'
      ? `${visible} référence${visible > 1 ? 's' : ''} affichée${visible > 1 ? 's' : ''}`
      : `${visible} reference${visible === 1 ? '' : 's'} shown`;
  };

  form.addEventListener('input', apply);
  form.addEventListener('reset', () => setTimeout(apply, 0));
  apply();
})();
