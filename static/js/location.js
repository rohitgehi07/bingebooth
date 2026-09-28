document.addEventListener('DOMContentLoaded', function() {
  const cityModal = document.getElementById('city-modal');
  const openCityModalBtn = document.getElementById('open-city-modal-btn');
  const closeCityModalBtn = document.getElementById('close-city-modal-btn');
  const detectLocationBtn = document.getElementById('detect-location-btn');
  const citySearchInput = document.getElementById('city-search-input');
  const cityButtons = document.querySelectorAll('.city-select-btn');

  // Show modal on first visit if no city stored in session
  if (cityModal && window.isFirstVisit) {
    cityModal.classList.remove('hidden');
  }

  if (openCityModalBtn && cityModal) {
    openCityModalBtn.addEventListener('click', () => {
      cityModal.classList.remove('hidden');
    });
  }

  if (closeCityModalBtn && cityModal) {
    closeCityModalBtn.addEventListener('click', () => {
      cityModal.classList.add('hidden');
    });
  }

  // Geolocation detection handler
  if (detectLocationBtn) {
    detectLocationBtn.addEventListener('click', () => {
      detectLocationBtn.disabled = true;
      detectLocationBtn.innerHTML = `<span class="animate-spin inline-block mr-2">🌀</span> Detecting...`;

      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            fetch('/api/detect-city', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ latitude: lat, longitude: lng })
            })
            .then(res => res.json())
            .then(data => {
              if (data.success) {
                window.location.reload();
              } else {
                alert('Could not detect city automatically. Please select from the list.');
              }
            })
            .catch(() => alert('Location service unavailable.'))
            .finally(() => {
              detectLocationBtn.disabled = false;
              detectLocationBtn.innerHTML = `📍 Detect My Location`;
            });
          },
          (error) => {
            detectLocationBtn.disabled = false;
            detectLocationBtn.innerHTML = `📍 Detect My Location`;
            alert('Location access denied or unavailable. Please select your city manually from the list below.');
          },
          { timeout: 10000 }
        );
      } else {
        detectLocationBtn.disabled = false;
        alert('Geolocation is not supported by your browser.');
      }
    });
  }

  // City selection buttons
  cityButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const cityName = btn.getAttribute('data-city');
      fetch('/api/set-city', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city_name: cityName })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          window.location.reload();
        }
      });
    });
  });

  // Search filter for city list in modal
  if (citySearchInput) {
    citySearchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      cityButtons.forEach(btn => {
        const cityName = btn.getAttribute('data-city').toLowerCase();
        if (cityName.includes(query)) {
          btn.style.display = 'inline-flex';
        } else {
          btn.style.display = 'none';
        }
      });
    });
  }
});
