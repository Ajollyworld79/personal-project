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

  // Filter projects by technology
  document.querySelectorAll('.filter-btn').forEach(b => {
    b.setAttribute('aria-pressed', 'false');
    b.addEventListener('click', function(e){
      // Use the button element (currentTarget) to handle clicks reliably
      const btn = e.currentTarget;
      const tech = btn.dataset.tech;
      if (!tech) return;

      const active = btn.classList.toggle('active');
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      // compute active filters and ignore any buttons without a data-tech value
      const activeFilters = Array.from(document.querySelectorAll('.filter-btn.active')).map(n => n.dataset.tech).filter(Boolean);
      document.querySelectorAll('.posts article').forEach(a => {
        const tags = Array.from(a.querySelectorAll('.tech-badge')).map(t => t.textContent.trim());
        if (activeFilters.length === 0 || activeFilters.some(f => tags.includes(f))) {
          a.style.display = '';
        } else {
          a.style.display = 'none';
        }
      });
    });
  });

  // Smooth scroll for internal links
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', function(e){
      const target = document.querySelector(this.getAttribute('href'));
      if (target) { e.preventDefault(); target.scrollIntoView({behavior:'smooth'}); }
    });
  });
});
