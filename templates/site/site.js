(function () {
  const root = document.documentElement;
  const button = document.querySelector('.theme-toggle');
  const setButton = (theme) => { button.textContent = theme === 'dark' ? '☀' : '☾'; };
  const apply = (theme) => {
    root.dataset.theme = theme;
    localStorage.setItem('mdcss-theme', theme);
    setButton(theme);
  };
  setButton(root.dataset.theme || 'light');
  button.addEventListener('click', () => apply(root.dataset.theme === 'dark' ? 'light' : 'dark'));

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
