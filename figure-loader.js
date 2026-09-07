document.addEventListener('DOMContentLoaded', () => {
  const figures = document.querySelectorAll('img[data-b64-name][data-b64-parts]');
  figures.forEach(async (img) => {
    const requestedName = img.dataset.b64Name;
    const restoreApprovedHydroModPy = requestedName === 'hydromodpy-v2';
    const name = restoreApprovedHydroModPy ? 'hydromodpy-approvedq100' : requestedName;
    const count = restoreApprovedHydroModPy ? 8 : Number(img.dataset.b64Parts || 0);
    const mime = img.dataset.b64Mime || 'image/webp';
    if (!name || !count) return;
    try {
      const requests = Array.from({ length: count }, (_, i) => {
        const n = String(i).padStart(2, '0');
        return fetch(`assets/figure-data/${name}.part-${n}.txt`).then(r => {
          if (!r.ok) throw new Error(`${name} part ${n}`);
          return r.text();
        });
      });
      const data = (await Promise.all(requests)).join('').replace(/\s+/g, '');
      const src = `data:${mime};base64,${data}`;
      img.src = src;
      img.classList.add('generated-figure-loaded');
      const link = img.closest('a.generated-figure-link');
      if (link) link.href = src;
    } catch (error) {
      console.error('Unable to load generated figure', name, error);
      img.classList.add('generated-figure-error');
    }
  });

  const figureImages = document.querySelectorAll('.figure-panel img');
  if (!figureImages.length) return;

  const lightbox = document.createElement('div');
  lightbox.className = 'image-lightbox';
  lightbox.setAttribute('aria-hidden', 'true');
  lightbox.innerHTML = `
    <button class="lightbox-close" type="button" aria-label="Fermer l’image agrandie">×</button>
    <img class="lightbox-image" src="" alt="">
  `;
  document.body.appendChild(lightbox);

  const lightboxImage = lightbox.querySelector('.lightbox-image');
  const closeButton = lightbox.querySelector('.lightbox-close');

  const openLightbox = (img) => {
    lightboxImage.src = img.currentSrc || img.src;
    lightboxImage.alt = img.alt || '';
    lightbox.classList.add('is-open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.classList.add('lightbox-open');
    closeButton.focus();
  };

  const closeLightbox = () => {
    lightbox.classList.remove('is-open');
    lightbox.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('lightbox-open');
    lightboxImage.src = '';
  };

  figureImages.forEach((img) => {
    img.classList.add('zoomable-image');
    img.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      openLightbox(img);
    });
  });

  closeButton.addEventListener('click', closeLightbox);

  lightbox.addEventListener('click', (event) => {
    if (event.target === lightbox) closeLightbox();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && lightbox.classList.contains('is-open')) {
      closeLightbox();
    }
  });
});
