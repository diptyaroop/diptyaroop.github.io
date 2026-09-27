/* Progressive enhancements: content and navigation work without JavaScript. */
(() => {
  document.documentElement.classList.add('js');
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#navigation');
  toggle.hidden = false;
  const closeMenu = () => {
    toggle.setAttribute('aria-expanded', 'false');
    nav.classList.remove('is-open');
  };
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  });
  nav.addEventListener('click', event => {
    if (event.target.closest('a')) closeMenu();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
      closeMenu();
      toggle.focus();
    }
  });
  const controls = document.querySelector('.publication-controls');
  const buttons = [...controls.querySelectorAll('[data-filter]')];
  const papers = [...document.querySelectorAll('.paper')];
  const count = document.querySelector('#paper-count');
  function filterPapers(filter) {
    let visible = 0;
    papers.forEach(paper => {
      const show = filter === 'all' || (filter === 'selected' && paper.dataset.selected === 'true') || (filter === 'recent' && ['2025', '2026'].includes(paper.dataset.year));
      paper.hidden = !show;
      if (show) visible++;
    });
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === filter)));
    count.textContent = `${visible} of ${papers.length} papers`;
  }
  controls.hidden = false;
  buttons.forEach(button => button.addEventListener('click', () => filterPapers(button.dataset.filter)));
  filterPapers('all');
  const links = [...nav.querySelectorAll('a[href^="#"]')];
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        links.forEach(link => {
          if (link.hash === `#${entry.target.id}`) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
      });
    }, { rootMargin: '-12% 0px -65% 0px', threshold: 0 });
    document.querySelectorAll('main > section[id], main > header').forEach(section => observer.observe(section));
  }
})();
