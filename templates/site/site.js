(function () {
  const root = document.documentElement;
  const themeButtons = Array.from(document.querySelectorAll('.theme-toggle'));
  const setButtons = (theme) => {
    for (const button of themeButtons) button.textContent = theme === 'dark' ? '☀' : '☾';
  };
  const apply = (theme) => {
    root.dataset.theme = theme;
    localStorage.setItem('mdcss-theme', theme);
    setButtons(theme);
  };
  setButtons(root.dataset.theme || 'light');
  for (const button of themeButtons) {
    button.addEventListener('click', () => apply(root.dataset.theme === 'dark' ? 'light' : 'dark'));
  }

  const closeToc = () => document.body.classList.remove('toc-open');
  document.querySelector('.toc-toggle')?.addEventListener('click', () => {
    document.body.classList.toggle('toc-open');
  });
  document.querySelector('.toc-scrim')?.addEventListener('click', closeToc);
  document.querySelectorAll('.toc a[href^="#"]').forEach((link) => link.addEventListener('click', closeToc));
  window.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeToc();
  });

  const links = Array.from(document.querySelectorAll('.toc a[data-target]'));
  const onScroll = () => {
    let current = '';
    for (const link of links) {
      const target = document.getElementById(link.dataset.target);
      if (target && target.getBoundingClientRect().top <= 96) current = link.dataset.target;
    }
    for (const link of links) link.classList.toggle('active', link.dataset.target === current);
  };
  window.addEventListener('scroll', () => requestAnimationFrame(onScroll), { passive: true });
  onScroll();
})();
