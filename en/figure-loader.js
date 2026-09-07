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
        return fetch(`../assets/figure-data/${name}.part-${n}.txt`).then(r => {
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

  if (!document.getElementById('figure-lightbox-style')) {
    const style = document.createElement('style');
    style.id = 'figure-lightbox-style';
    style.textContent = `
      .zoomable-image { cursor: zoom-in; }
      .image-lightbox {
        position: fixed;
        inset: 0;
        z-index: 10000;
        display: none;
        align-items: center;
        justify-content: center;
        padding: 4rem 2rem 2rem;
        background: rgba(8, 18, 28, 0.84);
      }
      .image-lightbox.is-open { display: flex; }
      .image-lightbox .lightbox-image {
        display: block;
        width: auto;
        height: auto;
        max-width: calc(100vw - 3rem);
        max-height: calc(100vh - 5rem);
        object-fit: contain;
        background: #fff;
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.35);
      }
      .image-lightbox .lightbox-close {
        position: absolute;
        top: 1rem;
        right: 1.25rem;
        width: 46px;
        height: 46px;
        border: 0;
        border-radius: 50%;
        background: #fff;
        color: #17324a;
        font-size: 2rem;
        line-height: 1;
        cursor: pointer;
      }
      body.lightbox-open { overflow: hidden; }
    `;
    document.head.appendChild(style);
  }

  const lightbox = document.createElement('div');
  lightbox.className = 'image-lightbox';
  lightbox.setAttribute('aria-hidden', 'true');
  lightbox.innerHTML = `
    <button class="lightbox-close" type="button" aria-label="Close enlarged image">×</button>
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
