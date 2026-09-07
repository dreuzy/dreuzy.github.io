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
      const binary = atob(data);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i += 1) {
        bytes[i] = binary.charCodeAt(i);
      }

      const blobUrl = URL.createObjectURL(new Blob([bytes], { type: mime }));
      img.src = blobUrl;
      img.classList.add('generated-figure-loaded');

      const link = img.closest('a.generated-figure-link');
      if (link) {
        link.href = blobUrl;
        link.target = '_blank';
        link.rel = 'noopener';
      }
    } catch (error) {
      console.error('Unable to load generated figure', name, error);
      img.classList.add('generated-figure-error');
    }
  });
});
