(() => {
  const init = () => {
    const isProjectsPage = window.location.pathname.startsWith('/projects');

    // Project expand/collapse
    for (const btn of document.querySelectorAll('.posts article .toggle-details')) {
      btn.setAttribute('aria-expanded', 'false');
      btn.addEventListener('click', (e) => {
        const article = e.currentTarget.closest('article');
        if (!article) return;
        const open = article.classList.toggle('project-open');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    }

    const filterButtons = document.querySelectorAll('.filter-btn');
    const clearButtons = document.querySelectorAll('#clear-filters');
    const articles = document.querySelectorAll('.posts article, .projects-grid article');

    // On /projects we show everything and hide the filter UI
    if (isProjectsPage) {
      for (const a of articles) a.classList.add('project-visible');
      const fb = document.querySelector('.filter-bar');
      if (fb) fb.hidden = true;
    }

    const getActiveFilters = () =>
      [...document.querySelectorAll('.filter-btn.active')]
        .map((b) => b.dataset.tech?.toLowerCase())
        .filter(Boolean);

    const applyFilters = () => {
      if (isProjectsPage) return;
      const active = getActiveFilters();
      if (active.length === 0) {
        for (const a of articles) a.classList.add('project-visible');
        return;
      }
      for (const a of articles) {
        const badges = [...a.querySelectorAll('.tech-badge')].map((t) =>
          t.textContent.trim().toLowerCase()
        );
        const matches = active.some((f) => badges.includes(f));
        a.classList.toggle('project-visible', matches);
      }
    };

    for (const btn of filterButtons) {
      btn.setAttribute('aria-pressed', 'false');
      btn.classList.remove('active');
      btn.addEventListener('click', (e) => {
        const tech = e.currentTarget.dataset.tech;
        if (!tech) return;
        const active = e.currentTarget.classList.toggle('active');
        e.currentTarget.setAttribute('aria-pressed', active ? 'true' : 'false');
        applyFilters();
      });
    }

    for (const cb of clearButtons) {
      cb.addEventListener('click', () => {
        for (const b of document.querySelectorAll('.filter-btn.active')) {
          if (b.id === 'clear-filters') continue;
          b.classList.remove('active');
          b.setAttribute('aria-pressed', 'false');
        }
        applyFilters();
      });
    }

    applyFilters();

    // Smooth scroll for in-page anchors (respect reduced-motion)
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    for (const a of document.querySelectorAll('a[href^="#"]')) {
      a.addEventListener('click', (e) => {
        const href = a.getAttribute('href');
        if (!href || href === '#') return;
        const target = document.querySelector(href);
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth' });
      });
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
