document.addEventListener('DOMContentLoaded', function(){
  // Theme toggle
  const themeToggle = document.getElementById('theme-toggle');
  const currentTheme = localStorage.getItem('theme');
  // Default to original theme (no purple). If user previously picked 'purple', restore it.
  if (currentTheme === 'purple') {
    document.documentElement.classList.add('purple-theme');
    document.body.classList.add('purple-theme');
  } else {
    document.documentElement.classList.remove('purple-theme');
    document.body.classList.remove('purple-theme');
    if (!currentTheme) localStorage.setItem('theme', 'default');
  }
  themeToggle?.addEventListener('click', function(){
    const hasPurple = document.documentElement.classList.toggle('purple-theme');
    if (hasPurple) document.body.classList.add('purple-theme'); else document.body.classList.remove('purple-theme');
    localStorage.setItem('theme', hasPurple ? 'purple' : 'default');
  });

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
      const tech = e.target.dataset.tech;
      const active = e.target.classList.toggle('active');
      e.target.setAttribute('aria-pressed', active ? 'true' : 'false');
      // compute active filters
      const activeFilters = Array.from(document.querySelectorAll('.filter-btn.active')).map(n => n.dataset.tech);
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
