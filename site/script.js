(() => {
  'use strict';
  const toast = document.querySelector('#toast');
  let toastTimer;
  function notify(message) {
    if (!toast) return;
    clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.add('visible');
    toastTimer = setTimeout(() => toast.classList.remove('visible'), 3500);
  }
  async function copyText(value, successMessage) {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(value);
      notify(successMessage);
      return true;
    } catch {
      // Keep the actual address available even in restricted in-app browsers.
      window.prompt('Copy the text below:', value);
      return false;
    }
  }
  const emailButton = document.querySelector('#copy-email');
  if (emailButton) {
    emailButton.hidden = false;
    emailButton.addEventListener('click', () => copyText('gwl0711@gmail.com', 'Email address copied'));
  }
  const dialog = document.querySelector('#share-dialog');
  if (dialog && typeof dialog.showModal === 'function') {
    document.querySelectorAll('.share-trigger').forEach(button => {
      button.hidden = false;
      button.addEventListener('click', () => dialog.showModal());
    });
    dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      const r = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom)) dialog.close();
    });
    const copyUrl = document.querySelector('#copy-url');
    let copyTimer;
    copyUrl.addEventListener('click', async () => {
      if (await copyText('https://gwl0711.github.io/', 'Website link copied')) {
        clearTimeout(copyTimer);
        copyUrl.textContent = 'Link copied ✓';
        copyTimer = setTimeout(() => { copyUrl.textContent = 'Copy link ⧉'; }, 2500);
      }
    });
  }
  document.querySelector('#print-qr')?.addEventListener('click', () => window.print());
  const year = document.querySelector('#year');
  if (year) year.textContent = new Date().getFullYear();
  if ('IntersectionObserver' in window) {
    const sections = document.querySelectorAll('main > section[id]');
    const navLinks = document.querySelectorAll('.site-header nav a');
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        navLinks.forEach(link => {
          const active = link.hash === `#${entry.target.id}`;
          link.classList.toggle('active', active);
          if (active) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
      }
    }, { rootMargin: '-15% 0px -65% 0px' });
    sections.forEach(section => observer.observe(section));
  }
})();
