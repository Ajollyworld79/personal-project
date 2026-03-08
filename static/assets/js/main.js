/*
	Phantom by HTML5 UP — Vanilla JS rewrite
	Original: html5up.net | @ajlkn (CC BY 3.0)
	jQuery removed — saves ~100KB page weight.
*/

(function() {
	'use strict';

	// Breakpoints (standalone, no jQuery needed).
	breakpoints({
		xlarge:   [ '1281px',  '1680px' ],
		large:    [ '981px',   '1280px' ],
		medium:   [ '737px',   '980px'  ],
		small:    [ '481px',   '736px'  ],
		xsmall:   [ '361px',   '480px'  ],
		xxsmall:  [ null,      '360px'  ]
	});

	// Remove preload class after page load (enables CSS transitions).
	window.addEventListener('load', function() {
		setTimeout(function() {
			document.body.classList.remove('is-preload');
		}, 100);
	});

	// Touch detection.
	if (browser.mobile)
		document.body.classList.add('is-touch');

	// Menu (kept for completeness — #menu is hidden via CSS).
	var menu = document.getElementById('menu');
	if (menu) {
		var inner = menu.querySelector('.inner');
		if (inner && !inner.querySelector('a.close')) {
			var closeLink = document.createElement('a');
			closeLink.className = 'close';
			closeLink.href = '#menu';
			closeLink.textContent = 'Close';
			inner.appendChild(closeLink);
		}

		var locked = false;
		function menuLock() {
			if (locked) return false;
			locked = true;
			setTimeout(function() { locked = false; }, 350);
			return true;
		}

		function menuShow()   { if (menuLock()) document.body.classList.add('is-menu-visible'); }
		function menuHide()   { if (menuLock()) document.body.classList.remove('is-menu-visible'); }
		function menuToggle() { if (menuLock()) document.body.classList.toggle('is-menu-visible'); }

		menu.addEventListener('click', function(e) { e.stopPropagation(); });
		menu.addEventListener('click', function(e) {
			var link = e.target.closest('a');
			if (!link) return;
			e.preventDefault();
			e.stopPropagation();
			menuHide();
			var href = link.getAttribute('href');
			if (href === '#menu') return;
			setTimeout(function() { window.location.href = href; }, 350);
		});

		document.querySelectorAll('a[href="#menu"]').forEach(function(a) {
			a.addEventListener('click', function(e) {
				e.stopPropagation();
				e.preventDefault();
				menuToggle();
			});
		});

		document.body.addEventListener('click', function() { menuHide(); });
		document.addEventListener('keydown', function(e) { if (e.key === 'Escape') menuHide(); });
	}

})();