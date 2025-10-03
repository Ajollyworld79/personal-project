/*
	Phantom by HTML5 UP
	html5up.net | @ajlkn
	Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)
*/

(function($) {

	var	$window = $(window),
		$body = $('body');

	// Breakpoints.
		breakpoints({
			xlarge:   [ '1281px',  '1680px' ],
			large:    [ '981px',   '1280px' ],
			medium:   [ '737px',   '980px'  ],
			small:    [ '481px',   '736px'  ],
			xsmall:   [ '361px',   '480px'  ],
			xxsmall:  [ null,      '360px'  ]
		});

	// Play initial animations on page load.
		$window.on('load', function() {
			window.setTimeout(function() {
				$body.removeClass('is-preload');
			}, 100);
		});

	// Touch?
		if (browser.mobile)
			$body.addClass('is-touch');

	// Forms.
		var $form = $('form');

		// Auto-resizing textareas.
			$form.find('textarea').each(function() {

				var $this = $(this),
					$wrapper = $('<div class="textarea-wrapper"></div>'),
					$submits = $this.find('input[type="submit"]');

				$this
					.wrap($wrapper)
					.attr('rows', 1)
					.css('overflow', 'hidden')
					.css('resize', 'none')
					.on('keydown', function(event) {

						if (event.keyCode == 13
						&&	event.ctrlKey) {

							event.preventDefault();
							event.stopPropagation();

							$(this).blur();

						}

					})
					.on('blur focus', function() {
						$this.val($.trim($this.val()));
					})
					.on('input blur focus --init', function() {

						$wrapper
							.css('height', $this.height());

						$this
							.css('height', 'auto')
							.css('height', $this.prop('scrollHeight') + 'px');

					})
					.on('keyup', function(event) {

						if (event.keyCode == 9)
							$this
								.select();

					})
					.triggerHandler('--init');

				// Fix.
					if (browser.name == 'ie'
					||	browser.mobile)
						$this
							.css('max-height', '10em')
							.css('overflow-y', 'auto');

			});

	// Menu.
		var $menu = $('#menu');

		// Only wrap if not already statically present
		if ($menu.children('.inner').length === 0) {
			$menu.wrapInner('<div class="inner"></div>');
		}

		// Close link forventes nu allerede i template; hvis ikke, opret kort.
		if ($menu.find('> .inner > a.close').length === 0) {
			$menu.children('.inner').append('<a class="close" href="#menu">Close</a>');
		}

		$menu._locked = false;

		$menu._lock = function() {

			if ($menu._locked)
				return false;

			$menu._locked = true;

			window.setTimeout(function() {
				$menu._locked = false;
			}, 350);

			return true;

		};

		$menu._show = function() {

			if ($menu._lock())
				$body.addClass('is-menu-visible');

		};

		$menu._hide = function() {

			if ($menu._lock())
				$body.removeClass('is-menu-visible');

		};

		$menu._toggle = function() {

			if ($menu._lock())
				$body.toggleClass('is-menu-visible');

		};

		$menu
			.appendTo($body)
			.on('click', function(event) {
				event.stopPropagation();
			})
			.on('click', 'a', function(event) {

				var href = $(this).attr('href');

				event.preventDefault();
				event.stopPropagation();

				// Hide.
					$menu._hide();

				// Redirect.
					if (href == '#menu')
						return;

					window.setTimeout(function() {
						window.location.href = href;
					}, 350);

			});

		$body
			.on('click', 'a[href="#menu"]', function(event) {

				event.stopPropagation();
				event.preventDefault();

				// Toggle.
					$menu._toggle();

			})
			.on('click', function(event) {

				// Hide.
					$menu._hide();

			})
			.on('keydown', function(event) {
				if (event.keyCode == 27)
					$menu._hide();
			});

		// Synkroniser ARIA med fallback trigger hvis findes
		var $trigger = $('#menuToggle');
		function syncAria(){
			var open = $body.hasClass('is-menu-visible');
			if ($trigger.length){
				$trigger.attr('aria-expanded', open ? 'true' : 'false');
			}
			$menu.attr('aria-hidden', open ? 'false' : 'true');
		}
		// Hook ind i vores _show/_hide/_toggle
		var _show = $menu._show, _hide = $menu._hide, _toggle = $menu._toggle;
		$menu._show = function(){ _show.call(this); syncAria(); };
		$menu._hide = function(){ _hide.call(this); syncAria(); };
		$menu._toggle = function(){ _toggle.call(this); syncAria(); };
		syncAria();

})(jQuery);

// Fallback: hvis jQuery/breakpoints init fejler, sørg for at menu kan toggles
(()=>{
	try {
		if (window.jQuery) return; // original script kørte fint
	} catch(_) {}
	const body=document.body;
	const menu=document.getElementById('menu');
	if(!menu) return;
	// close link allerede i template (eller tilføjet ovenfor)
	const toggle=(e)=>{e&&e.preventDefault();body.classList.toggle('is-menu-visible');};
	document.querySelectorAll('a[href="#menu"]').forEach(a=>a.addEventListener('click',toggle));
	menu.addEventListener('click',e=>{
		if(e.target.matches('a.close')){e.preventDefault();toggle();}
		else if(e.target.tagName==='A'&& e.target.getAttribute('href')!=='#menu'){
			body.classList.remove('is-menu-visible');
			setTimeout(()=>{window.location.href=e.target.href;},200);
		}
	});
	document.addEventListener('keydown',e=>{ if(e.key==='Escape') body.classList.remove('is-menu-visible'); });
})();

	// Always ensure preload class removed (defensive)
	window.addEventListener('load',()=>{document.body.classList.remove('is-preload');});