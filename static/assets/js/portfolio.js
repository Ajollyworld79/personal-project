(function(){
  function initPortfolio(){
    try {
      console.log('initPortfolio running on page:', window.location.pathname);
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
      // Ensure we target project articles on both homepage (.posts article) and the projects page (.projects-grid article)
      const articles = Array.from(document.querySelectorAll('.posts article, .projects-grid article'));

      // Detect if we're on the Projects page — on /projects we want to show all projects and not use filters
      const isProjectsPage = window.location && window.location.pathname && (window.location.pathname === '/projects' || window.location.pathname.startsWith('/projects'));
      if (isProjectsPage) {
        console.log('Projects page detected - showing all projects and hiding filter UI');
        articles.forEach(a => { a.classList.add('project-visible'); a.style.display = ''; });
        const fb = document.querySelector('.filter-bar'); if (fb) fb.style.display = 'none';
      }

      // CSS handles hiding by default - no need to set display here

      filterButtons.forEach(b => {
        b.setAttribute('aria-pressed', 'false');
        b.classList.remove('active'); // Ensure no filters are active on init
        b.addEventListener('click', function(e){
          // Use the button element (currentTarget) to handle clicks reliably
          const btn = e.currentTarget;
          const tech = btn.dataset.tech;
          if (!tech) return; // ignore non-filter buttons (e.g. Clear)

          const active = btn.classList.toggle('active');
          btn.setAttribute('aria-pressed', active ? 'true' : 'false');
          console.debug('Filter clicked:', tech, 'active=', active);
          applyFilters();
        });
      });

      function getActiveFilters() {
        // Query the DOM for current active filters so we don't rely on a cached list
        return Array.from(document.querySelectorAll('.filter-btn.active')).map(b => b.dataset.tech && b.dataset.tech.toLowerCase()).filter(Boolean);
      }

      function applyFilters() {
        const activeFilters = getActiveFilters();
        console.log('applyFilters called, activeFilters:', activeFilters, 'articles found:', articles.length);
        // If on the projects page, always show everything (no filters there)
        if (typeof isProjectsPage !== 'undefined' && isProjectsPage) {
          articles.forEach(a => { a.classList.add('project-visible'); a.style.display = ''; });
          return;
        }
        // If no filters selected, show all projects
        if (activeFilters.length === 0) {
          articles.forEach(a => { a.classList.add('project-visible'); });
          console.log('No filters - showing all articles');
          return;
        }

        articles.forEach(a => {
          const badges = Array.from(a.querySelectorAll('.tech-badge')).map(t => t.textContent.trim().toLowerCase());
          // OR semantics: show project if it matches ANY selected filter
          const matches = activeFilters.some(f => badges.includes(f));
          if (matches) {
            a.classList.add('project-visible');
          } else {
            a.classList.remove('project-visible');
          }
        });
        console.log('Filters applied');
      }

      if (clearButtons.length) {
        clearButtons.forEach(cb => cb.addEventListener('click', function(){
          // Remove active state from any button that is currently active (excluding clear itself)
          document.querySelectorAll('.filter-btn.active').forEach(b => {
            if (b.id === 'clear-filters') return;
            b.classList.remove('active');
            b.setAttribute('aria-pressed', 'false');
          });
          console.debug('Clear clicked — cleared filters, applying filters to hide all.');
          // Use applyFilters so the 'no filters => hide all' behavior is preserved
          applyFilters();
        }));
      }

      // Ensure hide-on-load truly applies (some scripts may run after init)
      try {
        applyFilters();
        // Run again after a short delay and on full window load as a safety net
        setTimeout(() => { console.debug('Re-applying filters after timeout'); applyFilters(); }, 100);
        window.addEventListener('load', function(){ console.debug('window.load — applying filters'); applyFilters(); });
      } catch (e) { console.error('applyFilters error during init safety calls', e); }

      // Smooth scroll for internal links
      document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', function(e){
          const target = document.querySelector(this.getAttribute('href'));
          if (target) { e.preventDefault(); target.scrollIntoView({behavior:'smooth'}); }
        });
      });
    } catch (err) {
      // Fail gracefully — show or hide based on page semantics
      console.error('Error initializing portfolio filters:', err);
      try {
        if (typeof isProjectsPage !== 'undefined' && isProjectsPage) {
          document.querySelectorAll('.posts article, .projects-grid article').forEach(a => { a.style.display = ''; });
        } else {
          document.querySelectorAll('.posts article, .projects-grid article').forEach(a => { a.style.display = 'none'; });
        }
      } catch(e){}
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPortfolio);
  } else {
    // DOMContentLoaded already fired — run immediately
    initPortfolio();
  }
})();
