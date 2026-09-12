(() => {
  const DOI = '10.1007/s11625-026-01896-8';
  const host = document.getElementById('bibliography-content');
  if (!host) return;

  const isEnglish = (document.documentElement.lang || '').toLowerCase().startsWith('en');
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

  const enrichments = [
    {
      id: 'rivages-media',
      title: 'Rivages Normands 2100: transdisciplinary co-constructed knowledge for land-use adaptation to groundwater rise along Normandy coastline',
      fr: '<strong>Autour du projet :</strong> <a href="https://oseren.univ-rennes.fr/rivages-normands-2100-articles-de-presse" target="_blank" rel="noopener">OSERen — articles de presse, interviews et ressources autour de RIVAGES Normands 2100</a>',
      en: '<strong>Project context:</strong> <a href="https://oseren.univ-rennes.fr/rivages-normands-2100-articles-de-presse" target="_blank" rel="noopener">OSERen — press coverage, interviews and resources on RIVAGES Normands 2100</a>'
    },
    {
      id: 'pyrenees-outreach',
      title: 'Projected climate change impacts on groundwater–surface water connectivity in a compartmentalized mountain headwater bedrock aquifer',
      fr: '<strong>Autour de cette publication :</strong> <a href="https://oseren.univ-rennes.fr/actualites/des-sources-en-sursis-les-tetes-de-bassin-versant-des-pyrenees-dans-un-monde-plus-chaud" target="_blank" rel="noopener">OSERen — Des sources en sursis : les têtes de bassin versant des Pyrénées dans un monde plus chaud</a>',
      en: '<strong>About this publication:</strong> <a href="https://oseren.univ-rennes.fr/actualites/des-sources-en-sursis-les-tetes-de-bassin-versant-des-pyrenees-dans-un-monde-plus-chaud" target="_blank" rel="noopener">OSERen — Des sources en sursis: Pyrenean headwaters in a warmer world</a>'
    },
    {
      id: 'researcher-roles-outreach',
      title: 'The diversity of researchers’ roles in sustainability science: the influence of project characteristics',
      fr: '<strong>Autour de cette publication :</strong> <a href="https://oseren.univ-rennes.fr/actualites/la-diversite-des-roles-des-chercheurs-dans-la-science-de-la-durabilite" target="_blank" rel="noopener">OSERen — La diversité des rôles des chercheurs dans la science de la durabilité</a>',
      en: '<strong>About this publication:</strong> <a href="https://oseren.univ-rennes.fr/actualites/la-diversite-des-roles-des-chercheurs-dans-la-science-de-la-durabilite" target="_blank" rel="noopener">OSERen — The diversity of researchers’ roles in sustainability science</a>'
    },
    {
      id: 'hess-highlight',
      title: 'Calibration of groundwater seepage against the spatial distribution of the stream network to assess catchment-scale hydraulic properties',
      fr: '<strong>Distinction éditoriale :</strong> <a href="https://hess.copernicus.org/articles/27/3221/2023/" target="_blank" rel="noopener">Highlight paper</a> — <span class="smallcaps">Hydrology and Earth System Sciences</span>.',
      en: '<strong>Editorial distinction:</strong> <a href="https://hess.copernicus.org/articles/27/3221/2023/" target="_blank" rel="noopener">Highlight paper</a> — <span class="smallcaps">Hydrology and Earth System Sciences</span>.'
    },
    {
      id: 'deep-denitrification-outreach',
      title: 'Deep denitrification: Stream and groundwater biogeochemistry reveal contrasted but connected worlds above and below',
      fr: '<strong>Autour de cette publication :</strong> <a href="https://oseren.univ-rennes.fr/actualites/denitrification-profonde-biogeochimie-eaux-constraste" target="_blank" rel="noopener">OSERen — Dénitrification profonde : la biogéochimie des cours d’eau et des eaux souterraines révèle des mondes contrastés… mais connectés</a>',
      en: '<strong>About this publication:</strong> <a href="https://oseren.univ-rennes.fr/actualites/denitrification-profonde-biogeochimie-eaux-constraste" target="_blank" rel="noopener">OSERen — Deep denitrification: contrasted but connected surface- and groundwater worlds</a>'
    },
    {
      id: 'agricultural-legacy-outreach',
      title: 'A hillslope-scale aquifer-model to determine past agricultural legacy and future nitrate concentrations in rivers',
      fr: '<strong>Autour de cette publication :</strong> <a href="https://oseren.univ-rennes.fr/actualites/quel-est-le-role-et-lheritage-des-pratiques-agricoles-passees-sur-levolution-et-le-futur" target="_blank" rel="noopener">OSERen — Quel est le rôle et l’héritage des pratiques agricoles passées sur l’évolution et le futur des concentrations en nitrate dans les rivières ?</a>',
      en: '<strong>About this publication:</strong> <a href="https://oseren.univ-rennes.fr/actualites/quel-est-le-role-et-lheritage-des-pratiques-agricoles-passees-sur-levolution-et-le-futur" target="_blank" rel="noopener">OSERen — The legacy of past agricultural practices for present and future river nitrate concentrations</a>'
    },
    {
      id: 'nitrate-recovery-outreach',
      title: 'What do we need to predict groundwater nitrate recovery trajectories?',
      fr: '<strong>Autour de cette publication :</strong> <a href="https://geosciences.univ-rennes.fr/actualites/de-quoi-avons-nous-besoin-pour-predire-la-resilience-des-eaux-souterraines-aux" target="_blank" rel="noopener">Géosciences Rennes — De quoi avons-nous besoin pour prédire la résilience des eaux souterraines aux contaminations par les nitrates ?</a>',
      en: '<strong>About this publication:</strong> <a href="https://geosciences.univ-rennes.fr/actualites/de-quoi-avons-nous-besoin-pour-predire-la-resilience-des-eaux-souterraines-aux" target="_blank" rel="noopener">Géosciences Rennes — What do we need to predict groundwater recovery from nitrate contamination?</a>'
    },
    {
      id: 'pnas-outreach',
      title: 'Stratification of reactivity determines nitrate removal in groundwater',
      fr: '<strong>Autour de cette publication :</strong> <a href="https://www.espace-sciences.org/sciences-ouest/370/actualite/l-eau-souterraine-lavee-des-nitrates" target="_blank" rel="noopener">Espace des sciences — L’eau souterraine lavée des nitrates</a> · <a href="https://oseren.univ-rennes.fr/actualites/losur-booste-linterdisciplinarite-et-construit-des-ponts-entre-les-unites" target="_blank" rel="noopener">OSERen — focus sur cette publication</a>',
      en: '<strong>About this publication:</strong> <a href="https://www.espace-sciences.org/sciences-ouest/370/actualite/l-eau-souterraine-lavee-des-nitrates" target="_blank" rel="noopener">Espace des sciences — L’eau souterraine lavée des nitrates</a> · <a href="https://oseren.univ-rennes.fr/actualites/losur-booste-linterdisciplinarite-et-construit-des-ponts-entre-les-unites" target="_blank" rel="noopener">OSERen — feature on this paper</a>'
    }
  ];

  const applyEnrichments = () => {
    const entries = [...host.querySelectorAll('li')];
    enrichments.forEach(item => {
      const key = normalize(item.title);
      const entry = entries.find(li => normalize(li.textContent).includes(key));
      if (!entry || entry.querySelector(`[data-bib-enrichment="${item.id}"]`)) return;
      const note = document.createElement('div');
      note.className = 'pub-meta';
      note.dataset.bibEnrichment = item.id;
      note.innerHTML = isEnglish ? item.en : item.fr;
      entry.appendChild(note);
    });
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
    } finally {
      applyEnrichments();
    }
  };

  const observer = new MutationObserver(() => applyUpdate());
  observer.observe(host, { attributes: true, childList: true, subtree: true });
  applyUpdate();
})();