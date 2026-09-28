document.addEventListener('DOMContentLoaded', function() {
  const langToggleBtn = document.getElementById('lang-toggle-btn');
  if (!langToggleBtn) return;

  langToggleBtn.addEventListener('click', () => {
    const currentLang = langToggleBtn.getAttribute('data-current-lang') || 'en';
    const newLang = currentLang === 'en' ? 'hi' : 'en';

    fetch('/api/set-lang', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lang: newLang })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        localStorage.setItem('bingebooth_lang', newLang);
        window.location.reload();
      }
    });
  });
});
