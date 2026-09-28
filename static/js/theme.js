document.addEventListener('DOMContentLoaded', function() {
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const sunIcon = document.getElementById('theme-sun-icon');
  const moonIcon = document.getElementById('theme-moon-icon');

  function getSavedTheme() {
    return localStorage.getItem('bingebooth_theme') || 'light';
  }

  function applyTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.classList.add('dark');
      if (sunIcon && moonIcon) {
        sunIcon.classList.remove('hidden');
        moonIcon.classList.add('hidden');
      }
    } else {
      document.documentElement.removeAttribute('data-theme');
      document.documentElement.classList.remove('dark');
      if (sunIcon && moonIcon) {
        sunIcon.classList.add('hidden');
        moonIcon.classList.remove('hidden');
      }
    }
    localStorage.setItem('bingebooth_theme', theme);
  }

  // Initialize theme on page load (Light mode default)
  const initialTheme = getSavedTheme();
  applyTheme(initialTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      applyTheme(newTheme);
    });
  }
});
