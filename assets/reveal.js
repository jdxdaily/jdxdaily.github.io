/* JDX — subtle Apple-style scroll reveals.
 * Fades elements up as they enter the viewport. No dependencies.
 * Honours prefers-reduced-motion and skips work if IntersectionObserver
 * isn't available, so the page is always usable without JS.
 */
(function () {
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // Things worth revealing. Keep this list narrow so the page doesn't
  // feel like everything is moving.
  var SELECTOR = [
    '.hero .eyebrow', '.hero h1', '.hero .lede',
    '.news-hero .eyebrow', '.news-hero h1', '.news-hero p',
    '.version-card',
    '.stock-teaser',
    '.news-section-header', '.news-card',
    '.archive-item',
    '.briefing-header > *',
    '.briefing-content > h2',
    '.briefing-content > h3',
    '.briefing-content > table.data',
    '.briefing-content > blockquote'
  ].join(',');

  var targets = document.querySelectorAll(SELECTOR);
  if (!targets.length) return;

  targets.forEach(function (el) { el.classList.add('reveal'); });

  // Light stagger between sibling cards inside common grid containers
  ['.versions', '.news-grid', '.archive-list'].forEach(function (sel) {
    document.querySelectorAll(sel).forEach(function (group) {
      var items = Array.prototype.filter.call(
        group.children,
        function (el) { return el.classList.contains('reveal'); }
      );
      items.forEach(function (el, i) {
        el.style.transitionDelay = (Math.min(i, 6) * 70) + 'ms';
      });
    });
  });

  var io = new IntersectionObserver(function (entries, observer) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  targets.forEach(function (el) { io.observe(el); });
})();
