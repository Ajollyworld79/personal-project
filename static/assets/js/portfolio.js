document.addEventListener('DOMContentLoaded', function(){
  // Project expand/collapse
  document.querySelectorAll('.posts article .toggle-details').forEach(btn => {
    // initialize aria-expanded
    btn.setAttribute('aria-expanded', 'false');
    btn.addEventListener('click', function(e){
      const article = e.target.closest('article');
      const open = article.classList.toggle('project-open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });

  // Filter projects by technology (OR semantics). Clear button handling included.
  const filterButtons = Array.from(document.querySelectorAll('.filter-btn'));
  const clearButtons = Array.from(document.querySelectorAll('#clear-filters'));
  const articles = Array.from(document.querySelectorAll('.posts article'));

  filterButtons.forEach(b => {
    b.setAttribute('aria-pressed', 'false');
    b.addEventListener('click', function(e){
      // Use the button element (currentTarget) to handle clicks reliably
      const btn = e.currentTarget;
      const tech = btn.dataset.tech;
      if (!tech) return; // ignore non-filter buttons (e.g. Clear)

      const active = btn.classList.toggle('active');
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      applyFilters();
    });
  });

  function getActiveFilters() {
    // Query the DOM for current active filters so we don't rely on a cached list
    return Array.from(document.querySelectorAll('.filter-btn.active')).map(b => b.dataset.tech && b.dataset.tech.toLowerCase()).filter(Boolean);
  }

  function applyFilters() {
    const activeFilters = getActiveFilters();
    articles.forEach(a => {
      const badges = Array.from(a.querySelectorAll('.tech-badge')).map(t => t.textContent.trim().toLowerCase());
      if (activeFilters.length === 0) {
        a.style.display = '';
      } else {
        // OR semantics: show project if it matches ANY selected filter
        const matches = activeFilters.some(f => badges.includes(f));
        a.style.display = matches ? '' : 'none';
      }
    });
  }

  if (clearButtons.length) {
    clearButtons.forEach(cb => cb.addEventListener('click', function(){
      // Remove active state from any button that is currently active (excluding clear itself)
      document.querySelectorAll('.filter-btn.active').forEach(b => {
        if (b.id === 'clear-filters') return;
        b.classList.remove('active');
        b.setAttribute('aria-pressed', 'false');
      });
      applyFilters();
    }));
  }

  // Smooth scroll for internal links
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', function(e){
      const target = document.querySelector(this.getAttribute('href'));
      if (target) { e.preventDefault(); target.scrollIntoView({behavior:'smooth'}); }
    });
  });
});
