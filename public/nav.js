// Drop-down menus whose label is not a link (Landscape): open on click or tap, close on outside click or Escape.
// Hover and keyboard focus are handled in CSS.
document.querySelectorAll('.dd .ddbtn').forEach((b) => {
  const dd = b.parentElement;
  b.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = !dd.classList.contains('open');
    document.querySelectorAll('.dd.open').forEach((x) => { x.classList.remove('open'); x.querySelector('.ddbtn')?.setAttribute('aria-expanded', 'false'); });
    dd.classList.toggle('open', open); b.setAttribute('aria-expanded', String(open));
  });
});
document.addEventListener('click', (e) => {
  document.querySelectorAll('.dd.open').forEach((x) => { if (!x.contains(e.target)) { x.classList.remove('open'); x.querySelector('.ddbtn')?.setAttribute('aria-expanded', 'false'); } });
});
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  document.querySelectorAll('.dd.open').forEach((x) => { x.classList.remove('open'); x.querySelector('.ddbtn')?.setAttribute('aria-expanded', 'false'); x.querySelector('.ddbtn')?.focus(); });
});
