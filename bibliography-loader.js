(() => {
  const script = document.currentScript;
  const lang = script?.dataset.lang === 'en' ? 'en' : 'fr';
  const root = script?.dataset.root || '';

  const normalize = value => (value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
  const isHeading = el => /^H[1-6]$/.test(el?.tagName || '');
  const headingLevel = el => Number((el?.tagName || 'H6').slice(1));
  const sectionNodes = heading => {
    const out = [];
    const level = headingLevel(heading);
    let node = heading.nextElementSibling;
    while (node) {
      if (isHeading(node) && headingLevel(node) <= level) break;
      out.push(node);
      node = node.nextElementSibling;
    }
    return out;
  };
  const removeSection = heading => {
    sectionNodes(heading).forEach(node => node.remove());
    heading.remove();
  };
  const replaceOlWithUl = ol => {
    const ul = document.createElement('ul');
    ul.className = `${ol.className || ''} bib-unnumbered`.trim();
    [...ol.attributes].forEach(attr => { if (attr.name !== 'class') ul.setAttribute(attr.name, attr.value); });
    while (ol.firstChild) ul.appendChild(ol.firstChild);
    ol.replaceWith(ul);
    return ul;
  };
  const makeSectionUnnumbered = heading => {
    sectionNodes(heading).forEach(node => {
      if (node.tagName === 'OL') replaceOlWithUl(node);
      node.querySelectorAll?.('ol').forEach(replaceOlWithUl);
      if (node.tagName === 'UL') node.classList.add('bib-unnumbered');
      node.querySelectorAll?.('ul').forEach(list => list.classList.add('bib-unnumbered'));
      if (node.matches?.('p')) node.innerHTML = node.innerHTML.replace(/^\s*\d+\.\s*/, '');
    });
  };
  const getFollowingList = heading => {
    let list = heading.nextElementSibling;
    while (list && !['OL', 'UL'].includes(list.tagName) && !isHeading(list)) list = list.nextElementSibling;
    if (!list || isHeading(list)) {
      list = document.createElement('ul');
      list.className = 'bib-unnumbered';
      heading.insertAdjacentElement('afterend', list);
    } else if (list.tagName === 'OL') list = replaceOlWithUl(list);
    else list.classList.add('bib-unnumbered');
    return list;
  };

  (async () => {
    const host = document.getElementById('bibliography-content');
    if (!host) return;
    try {
      const files = Array.from({ length: 5 }, (_, i) => `${root}bibliographie-payload-0${i + 1}.txt`);
      const parts = await Promise.all(files.map(async file => {
        const response = await fetch(file);
        if (!response.ok) throw new Error(file);
        return response.text();
      }));
      const b64 = parts.join('').replace(/\s+/g, '');
      const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
      if (!('DecompressionStream' in window)) throw new Error('gzip unsupported');
      const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
      host.innerHTML = await new Response(stream).text();

      host.querySelectorAll('li,p').forEach(entry => {
        entry.innerHTML = entry.innerHTML
          .replaceAll('From Aqua Incognita to Aqua Cognita', 'Headwater catchments: from aqua incognita to aqua cognita')
          .replaceAll('PyAge: an extensible toolkit for lumped-parameter modeling of tracer-derived groundwater ages', 'PyAges: an extensible toolkit for lumped-parameter modeling of tracer-derived groundwater ages');
      });

      host.querySelectorAll('li,p').forEach(entry => {
        const text = normalize(entry.textContent);
        if (text.includes('reading the aquifer in the stream: a unified framework to infer subsurface denitrification from low flow stream chemistry')) {
          entry.innerHTML = entry.innerHTML.replace(/Environmental Science Letters\s*,?\s*/gi, '');
          entry.querySelectorAll('span,em,i').forEach(el => {
            if (!normalize(el.textContent)) el.remove();
          });
        }
      });

      const unwanted = [
        'towards a more comprehensive representation of hydrosystems in water footprint assessments',
        'technical note: hydromodpy',
        'groundwater flow contributions to streamflows predicted by a hydrogeomorphological wetness index: insights from synthetic experiments',
        'an integrated double-continuum approach for simulating coupled vertical richards flows and lateral boussinesq flows',
        'functional archetypes of shallow aquifers for sustaining stream low flows: balancing storage and transmissivity'
      ];
      host.querySelectorAll('li,p').forEach(entry => {
        const text = normalize(entry.textContent);
        if (unwanted.some(title => text.includes(title))) entry.remove();
      });

      [...host.querySelectorAll('h2,h3,h4,h5,h6')].forEach(heading => {
        const title = normalize(heading.textContent);
        if (title.includes('abandon') || title.includes('abandoned') || title.includes('en preparation') || title.includes('in preparation')) removeSection(heading);
      });

      if (lang === 'en') {
        const sectionTitles = {
          'articles-dans-des-revues-a-comite-de-lecture': 'Peer-reviewed journal articles',
          'chapitre-douvrage': 'Book chapter',
          'rapports-et-autres-publications': 'Reports and other publications',
          'proceedings-references-dans-web-of-knowledge': 'Proceedings indexed in Web of Knowledge',
          'proceedings-non-references-dans-web-of-knowledge': 'Proceedings not indexed in Web of Knowledge',
          'abstracts-de-colloques': 'Conference abstracts'
        };
        Object.entries(sectionTitles).forEach(([id, title]) => {
          const el = host.querySelector(`#${id}`);
          if (el) el.textContent = title;
        });
      }

      let headings = [...host.querySelectorAll('h2,h3,h4,h5,h6')];
      let submittedHeading = headings.find(h => {
        const t = normalize(h.textContent);
        return t.includes('soumis') || t.includes('submitted');
      });
      if (!submittedHeading) {
        const articleHeading = host.querySelector('#articles-dans-des-revues-a-comite-de-lecture');
        if (articleHeading) {
          submittedHeading = document.createElement('h3');
          submittedHeading.textContent = lang === 'en' ? 'Submitted' : 'Soumis';
          articleHeading.insertAdjacentElement('afterend', submittedHeading);
        }
      }

      if (submittedHeading) {
        const prepHeading = document.createElement('h3');
        prepHeading.textContent = lang === 'en' ? 'In preparation' : 'En préparation';
        const prepList = document.createElement('ul');
        prepList.className = 'bib-unnumbered';
        const items = lang === 'en' ? [
          'J. Marçais, J.-R. de Dreuzy, H. V. Gupta, Groundwater flow contributions to streamflows predicted by a hydrogeomorphological wetness index: insights from synthetic experiments. <span class="smallcaps">Comptes Rendus Géoscience — Sciences de la Planète</span>, in preparation.',
          'K. Brenner, Y. Qiang, J. Marçais, J.-R. de Dreuzy, An Integrated Double-Continuum Approach for Simulating Coupled Vertical Richards Flows and Lateral Boussinesq Flows. <span class="smallcaps">Advances in Water Resources</span>, in preparation.',
          'T. Touzeau et al., Functional archetypes of shallow aquifers for sustaining stream low flows: balancing storage and transmissivity. <span class="smallcaps">Comptes Rendus Géoscience — Sciences de la Planète</span>, in preparation.',
          'R. Abhervé et al., Stream networks reveal shallow aquifer transmissivity across European crystalline bedrock headwater catchments. <span class="smallcaps">Geophysical Research Letters</span>, in preparation.',
          'B. Boivin et al., Identifying inflow, evaporation and seepage from reservoir water-level dynamics for water-resource management. <span class="smallcaps">Water Resources Research</span>, in preparation.',
          'E. Le Carrer et al., Pesticide dynamics in agricultural catchments, in preparation.',
          'I. Issolah et al., A generic software architecture for aquifer simulation, in preparation.'
        ] : [
          'J. Marçais, J.-R. de Dreuzy, H. V. Gupta, Groundwater flow contributions to streamflows predicted by a hydrogeomorphological wetness index: insights from synthetic experiments. <span class="smallcaps">Comptes Rendus Géoscience — Sciences de la Planète</span>, en préparation.',
          'K. Brenner, Y. Qiang, J. Marçais, J.-R. de Dreuzy, An Integrated Double-Continuum Approach for Simulating Coupled Vertical Richards Flows and Lateral Boussinesq Flows. <span class="smallcaps">Advances in Water Resources</span>, en préparation.',
          'T. Touzeau et al., Functional archetypes of shallow aquifers for sustaining stream low flows: balancing storage and transmissivity. <span class="smallcaps">Comptes Rendus Géoscience — Sciences de la Planète</span>, en préparation.',
          'R. Abhervé et al., Stream networks reveal shallow aquifer transmissivity across European crystalline bedrock headwater catchments. <span class="smallcaps">Geophysical Research Letters</span>, en préparation.',
          'B. Boivin et al., Identifying inflow, evaporation and seepage from reservoir water-level dynamics for water-resource management. <span class="smallcaps">Water Resources Research</span>, en préparation.',
          'E. Le Carrer et al., Pesticide dynamics in agricultural catchments, en préparation.',
          'I. Issolah et al., A generic software architecture for aquifer simulation, en préparation.'
        ];
        items.forEach(html => {
          const li = document.createElement('li');
          li.innerHTML = html;
          prepList.appendChild(li);
        });
        submittedHeading.insertAdjacentElement('beforebegin', prepHeading);
        prepHeading.insertAdjacentElement('afterend', prepList);

        const submittedList = getFollowingList(submittedHeading);
        const hostText = () => normalize(host.textContent);
        if (!hostText().includes('pyages: an extensible toolkit for lumped-parameter modeling of tracer-derived groundwater ages')) {
          const li = document.createElement('li');
          li.innerHTML = lang === 'en'
            ? 'J.-R. de Dreuzy, S. Leray, J. Marçais (2026), PyAges: an extensible toolkit for lumped-parameter modeling of tracer-derived groundwater ages. <span class="smallcaps">Geoscientific Model Development</span>, submitted.'
            : 'J.-R. de Dreuzy, S. Leray, J. Marçais (2026), PyAges: an extensible toolkit for lumped-parameter modeling of tracer-derived groundwater ages. <span class="smallcaps">Geoscientific Model Development</span>, soumis.';
          submittedList.prepend(li);
        }
        if (!hostText().includes('sentinel water fingerprint: capturing hydrosystem dynamics for adaptive water management')) {
          const li = document.createElement('li');
          li.innerHTML = lang === 'en'
            ? 'M. Ricau, R. Abhervé, H. Budzinski, C. Casenave, A. Chaumot, F. Courant, V. Dupraz, G. Fernandes, H. Fenet, E. Gomez, P. Gonzalez, G. Imfeld, J. Jaunat, G. Junqua, C. Kane, S. Lardy-Fontan, T. Le Borgne, B. Lopez, J. M.F. Martins, J. Molénat, S. Payraudeau, A. Togola, J. Tournebize, J.-R. de Dreuzy (2026), Sentinel water fingerprint: capturing hydrosystem dynamics for adaptive water management. <span class="smallcaps">WIREs Water</span>, submitted.'
            : 'M. Ricau, R. Abhervé, H. Budzinski, C. Casenave, A. Chaumot, F. Courant, V. Dupraz, G. Fernandes, H. Fenet, E. Gomez, P. Gonzalez, G. Imfeld, J. Jaunat, G. Junqua, C. Kane, S. Lardy-Fontan, T. Le Borgne, B. Lopez, J. M.F. Martins, J. Molénat, S. Payraudeau, A. Togola, J. Tournebize, J.-R. de Dreuzy (2026), Sentinel water fingerprint: capturing hydrosystem dynamics for adaptive water management. <span class="smallcaps">WIREs Water</span>, soumis.';
          submittedList.prepend(li);
        }
      }

      if (lang === 'en') {
        const walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT);
        const nodes = [];
        while (walker.nextNode()) nodes.push(walker.currentNode);
        nodes.forEach(node => {
          node.nodeValue = node.nodeValue
            .replace(/article en révision pour/gi, 'in revision for')
            .replace(/article en révision/gi, 'in revision')
            .replace(/en révision/gi, 'in revision')
            .replace(/under review at/gi, 'in revision for')
            .replace(/under review for/gi, 'in revision for')
            .replace(/under review/gi, 'in revision')
            .replace(/in review/gi, 'in revision')
            .replace(/soumis à/gi, 'submitted to')
            .replace(/soumis/gi, 'submitted')
            .replace(/en préparation pour/gi, 'in preparation for')
            .replace(/en préparation/gi, 'in preparation');
        });
      } else {
        const walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT);
        const nodes = [];
        while (walker.nextNode()) nodes.push(walker.currentNode);
        nodes.forEach(node => {
          node.nodeValue = node.nodeValue
            .replace(/under review at/gi, 'en révision pour')
            .replace(/under review for/gi, 'en révision pour')
            .replace(/under review/gi, 'en révision')
            .replace(/in revision at/gi, 'en révision pour')
            .replace(/in revision for/gi, 'en révision pour')
            .replace(/in revision/gi, 'en révision')
            .replace(/in review/gi, 'en révision')
            .replace(/submitted to/gi, 'soumis à')
            .replace(/submitted/gi, 'soumis')
            .replace(/in preparation for/gi, 'en préparation pour')
            .replace(/in preparation/gi, 'en préparation');
        });
      }

      headings = [...host.querySelectorAll('h2,h3,h4,h5,h6')];
      headings.forEach(heading => {
        const title = normalize(heading.textContent);
        if (lang === 'en') {
          if (title.includes('in preparation')) heading.textContent = 'In preparation';
          else if (title.includes('soumis') || title.includes('submitted')) heading.textContent = 'Submitted';
          else if (title === 'in review' || title.includes('en revision') || title.includes('under review') || title.includes('in revision')) heading.textContent = 'In revision';
          else if (title.includes('articles publies') || title === 'publies' || title === 'published') heading.textContent = 'Published';
        } else {
          if (title.includes('en preparation')) heading.textContent = 'En préparation';
          else if (title.includes('soumis')) heading.textContent = 'Soumis';
          else if (title === 'in review' || title.includes('en revision') || title.includes('article en revision') || title.includes('under review') || title.includes('in revision')) heading.textContent = 'En révision';
          else if (title.includes('articles publies') || title === 'publies') heading.textContent = 'Publiés';
        }
      });

      const finalizeStatusAtEnd = (heading, kind) => {
        if (!heading) return;
        const finalWord = kind === 'submitted'
          ? (lang === 'en' ? 'submitted' : 'soumis')
          : kind === 'revision'
            ? (lang === 'en' ? 'in revision' : 'en révision')
            : (lang === 'en' ? 'in preparation' : 'en préparation');
        const withTargetPatterns = kind === 'submitted'
          ? [
              /\s*(?:submitted\s+to|soumis\s+à|prepared\s+for|préparé\s+pour)\s+([\s\S]+?)\.?\s*$/i
            ]
          : kind === 'revision'
            ? [
                /\s*(?:in\s+revision\s+(?:at|for)|under\s+review\s+(?:at|for)|en\s+révision\s+pour|article\s+en\s+révision\s+pour|submitted\s+to|soumis\s+à)\s+([\s\S]+?)\.?\s*$/i
              ]
            : [
                /\s*(?:in\s+preparation\s+for|en\s+préparation\s+pour)\s+([\s\S]+?)\.?\s*$/i
              ];
        const barePatterns = kind === 'submitted'
          ? [/\s*,?\s*(?:submitted|soumis)\.?\s*$/i]
          : kind === 'revision'
            ? [/\s*,?\s*(?:in\s+revision|under\s+review|in\s+review|en\s+révision|article\s+en\s+révision)\.?\s*$/i]
            : [/\s*,?\s*(?:in\s+preparation|en\s+préparation)\.?\s*$/i];

        const entries = [];
        sectionNodes(heading).forEach(node => {
          if (node.matches?.('li,p')) entries.push(node);
          node.querySelectorAll?.('li,p').forEach(entry => entries.push(entry));
        });
        [...new Set(entries)].forEach(entry => {
          let html = entry.innerHTML.trim();
          let changed = false;
          for (const pattern of withTargetPatterns) {
            if (pattern.test(html)) {
              html = html.replace(pattern, (_, target) =>
                ` ${target.trim().replace(/[.,;:]\s*$/, '')}, ${finalWord}.`);
              changed = true;
              break;
            }
          }
          if (!changed) {
            for (const pattern of barePatterns) {
              if (pattern.test(html)) {
                html = html.replace(pattern, `, ${finalWord}.`);
                changed = true;
                break;
              }
            }
          }
          entry.innerHTML = html;
        });
      };

      headings = [...host.querySelectorAll('h2,h3,h4,h5,h6')];
      const finalPrepHeading = headings.find(h => normalize(h.textContent) === (lang === 'en' ? 'in preparation' : 'en preparation'));
      const finalSubmittedHeading = headings.find(h => normalize(h.textContent) === (lang === 'en' ? 'submitted' : 'soumis'));
      const finalRevisionHeading = headings.find(h => normalize(h.textContent) === (lang === 'en' ? 'in revision' : 'en revision'));
      finalizeStatusAtEnd(finalPrepHeading, 'preparation');
      finalizeStatusAtEnd(finalSubmittedHeading, 'submitted');
      finalizeStatusAtEnd(finalRevisionHeading, 'revision');

      headings = [...host.querySelectorAll('h2,h3,h4,h5,h6')];
      const publishedLabel = lang === 'en' ? 'published' : 'publies';
      const publishedHeading = headings.find(h => normalize(h.textContent) === publishedLabel);
      if (publishedHeading) {
        let list = publishedHeading.nextElementSibling;
        while (list && !['OL', 'UL'].includes(list.tagName) && !isHeading(list)) list = list.nextElementSibling;
        if (!list || isHeading(list)) {
          list = document.createElement('ol');
          publishedHeading.insertAdjacentElement('afterend', list);
        }
        const li = document.createElement('li');
        li.innerHTML = 'A. Gauvain, R. Abhervé, B. Boivin, C. Roques, M. Le Mesnil, A. Coche, T. Babey, J. Marçais, C. Bouchez, S. Leray, E. Marti, E. Bresciani, R. Figueroa, M. Pélissier, L. Guillaumot, T. Touzeau, I. Issolah, E. Maugan, R. S. Bagagnan, C. Vautier, J. Sallou, J. Bourcier, B. Combemale, P. Brunner, L. Longuevergne, L. Aquilina, J.-R. de Dreuzy (2026), <a href="https://hess.copernicus.org/articles/30/5571/2026/" target="_blank" rel="noopener">Technical note: HydroModPy (v1.0) – a Python toolbox for deploying catchment-scale shallow groundwater models</a>. <span class="smallcaps">Hydrology and Earth System Sciences</span>, 30, 5571.';
        list.prepend(li);
      }

      headings.filter(h => {
        const t = normalize(h.textContent);
        return ['en preparation', 'soumis', 'en revision', 'in preparation', 'submitted', 'in revision', 'under review'].includes(t);
      }).forEach(makeSectionUnnumbered);

      host.querySelectorAll('li strong, li b, p strong, p b').forEach(el => {
        const fragment = document.createDocumentFragment();
        while (el.firstChild) fragment.appendChild(el.firstChild);
        el.replaceWith(fragment);
      });

      host.setAttribute('aria-busy', 'false');
      if (location.hash) setTimeout(() => document.getElementById(location.hash.slice(1))?.scrollIntoView(), 0);
    } catch (error) {
      host.setAttribute('aria-busy', 'false');
      host.innerHTML = lang === 'en'
        ? '<p>The bibliography could not be loaded. Please reload this page in a recent browser.</p>'
        : '<p>La bibliographie n’a pas pu être chargée. Merci de recharger la page dans un navigateur récent.</p>';
      console.error(error);
    }
  })();
})();
