document.addEventListener('DOMContentLoaded', function() {
  const timerDisplay = document.getElementById('hold-timer-display');
  if (!timerDisplay) return;

  let remainingSeconds = parseInt(timerDisplay.getAttribute('data-seconds'), 10) || 240;

  function updateTimer() {
    if (remainingSeconds <= 0) {
      timerDisplay.textContent = "00:00";
      timerDisplay.classList.add('timer-warning');
      alert("Your 4-minute seat hold has expired. The seats have been released.");
      const redirectUrl = timerDisplay.getAttribute('data-redirect-url') || '/';
      window.location.href = redirectUrl;
      return;
    }

    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = remainingSeconds % 60;
    const formatted = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

    timerDisplay.textContent = formatted;

    if (remainingSeconds <= 60) {
      timerDisplay.classList.add('timer-warning');
    }

    remainingSeconds--;
  }

  updateTimer();
  const interval = setInterval(updateTimer, 1000);
});
