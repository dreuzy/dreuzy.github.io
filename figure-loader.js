document.addEventListener('DOMContentLoaded', () => {
  const figures = document.querySelectorAll('img[data-b64-name][data-b64-parts]');
  figures.forEach(async (img) => {
    const requestedName = img.dataset.b64Name;
    const restoreApprovedHydroModPy = requestedName === 'hydromodpy-v2';
    const name = restoreApprovedHydroModPy ? 'hydromodpy-approvedq100' : requestedName;
    const count = restoreApprovedHydroModPy ? 8 : Number(img.dataset.b64Parts || 0);
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
      const src = `data:image/webp;base64,${data}`;
      img.src = src;
      img.classList.add('generated-figure-loaded');
      const link = img.closest('a.generated-figure-link');
      if (link) link.href = src;
    } catch (error) {
      console.error('Unable to load generated figure', name, error);
      img.classList.add('generated-figure-error');
    }
  });
});
