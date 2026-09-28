document.addEventListener('DOMContentLoaded', function() {
  const showId = window.currentShowId;
  if (!showId) return;

  const seatElements = document.querySelectorAll('.seat:not(.seat-sold):not(.seat-held):not(.seat-aisle)');
  const allSeatsMap = document.querySelectorAll('.seat');
  const maxSeatModal = document.getElementById('seat-count-modal');
  const confirmSeatCountBtn = document.getElementById('confirm-seat-count-btn');
  const countPills = document.querySelectorAll('.seat-count-pill');
  
  const summaryBar = document.getElementById('seat-summary-bar');
  const selectedSeatsLabel = document.getElementById('selected-seats-label');
  const selectedTotalLabel = document.getElementById('selected-total-label');
  const selectedSeatsCountLabel = document.getElementById('selected-seats-count');
  const submitHoldForm = document.getElementById('hold-seats-form');
  const hiddenSeatIdsInput = document.getElementById('hidden-seat-ids');
  const hiddenSeatLabelsInput = document.getElementById('hidden-seat-labels');

  // Find Seats Together Elements
  const groupSizeSelect = document.getElementById('group-size-select');
  const findBestSeatsBtn = document.getElementById('find-best-seats-btn');

  let maxSeatsAllowed = 2;
  let selectedSeats = [];

  // Seat count selection modal handler
  countPills.forEach(pill => {
    pill.addEventListener('click', () => {
      countPills.forEach(p => p.classList.remove('bg-purple-600', 'text-white'));
      pill.classList.add('bg-purple-600', 'text-white');
      maxSeatsAllowed = parseInt(pill.getAttribute('data-count'), 10);
      if (groupSizeSelect) groupSizeSelect.value = Math.min(maxSeatsAllowed, 6);
    });
  });

  if (confirmSeatCountBtn && maxSeatModal) {
    confirmSeatCountBtn.addEventListener('click', () => {
      maxSeatModal.classList.add('hidden');
    });
  }

  // Group Seat Scanner Algorithm Click Handler
  if (findBestSeatsBtn && groupSizeSelect) {
    findBestSeatsBtn.addEventListener('click', () => {
      const groupSize = parseInt(groupSizeSelect.value, 10);
      findBestSeatsBtn.disabled = true;
      findBestSeatsBtn.innerHTML = `<span class="animate-spin inline-block mr-1">🌀</span> Scanning...`;

      fetch('/api/find-best-seats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ show_id: showId, group_size: groupSize })
      })
      .then(res => res.json())
      .then(data => {
        findBestSeatsBtn.disabled = false;
        findBestSeatsBtn.innerHTML = `✨ Find Best Seats`;

        if (data.success) {
          // Clear current manual selections
          selectedSeats.forEach(s => {
            const el = document.querySelector(`.seat[data-seat-id="${s.id}"]`);
            if (el) el.className = 'seat seat-available';
          });
          selectedSeats = [];

          // Highlight recommended seats with glowing class
          maxSeatsAllowed = groupSize;
          data.seat_ids.forEach(seatId => {
            const el = document.querySelector(`.seat[data-seat-id="${seatId}"]`);
            if (el) {
              el.className = 'seat seat-recommended';
              const seatLabel = el.getAttribute('data-seat-label');
              const price = floatVal(el.getAttribute('data-price'));
              selectedSeats.push({ id: seatId, label: seatLabel, price: price });
            }
          });

          updateSummaryBar();
          showNotification(data.message, 'success');
        } else {
          showNotification(data.message, 'warning');
        }
      })
      .catch(err => {
        findBestSeatsBtn.disabled = false;
        findBestSeatsBtn.innerHTML = `✨ Find Best Seats`;
        showNotification('Failed to find group seats.', 'error');
      });
    });
  }

  // Seat toggle click listener
  seatElements.forEach(seat => {
    seat.addEventListener('click', () => {
      const seatId = parseInt(seat.getAttribute('data-seat-id'), 10);
      const seatLabel = seat.getAttribute('data-seat-label');
      const price = floatVal(seat.getAttribute('data-price'));

      const existingIndex = selectedSeats.findIndex(s => s.id === seatId);

      if (existingIndex > -1) {
        // Deselect
        selectedSeats.splice(existingIndex, 1);
        seat.className = 'seat seat-available';
      } else {
        // Select
        if (selectedSeats.length >= maxSeatsAllowed) {
          const removed = selectedSeats.shift();
          const removedEl = document.querySelector(`.seat[data-seat-id="${removed.id}"]`);
          if (removedEl) {
            removedEl.className = 'seat seat-available';
          }
        }
        selectedSeats.push({ id: seatId, label: seatLabel, price: price });
        seat.className = 'seat seat-selected';
      }

      updateSummaryBar();
    });
  });

  function floatVal(val) {
    return parseFloat(val) || 0.0;
  }

  function updateSummaryBar() {
    if (selectedSeats.length > 0) {
      summaryBar.classList.remove('translate-y-full', 'opacity-0');
      summaryBar.classList.add('translate-y-0', 'opacity-100');

      const labels = selectedSeats.map(s => s.label).join(', ');
      const total = selectedSeats.reduce((sum, s) => sum + s.price, 0);

      selectedSeatsLabel.textContent = labels;
      selectedSeatsCountLabel.textContent = `${selectedSeats.length} Ticket${selectedSeats.length > 1 ? 's' : ''}`;
      selectedTotalLabel.textContent = `₹${total.toFixed(2)}`;

      hiddenSeatIdsInput.value = selectedSeats.map(s => s.id).join(',');
      hiddenSeatLabelsInput.value = labels;
    } else {
      summaryBar.classList.add('translate-y-full', 'opacity-0');
      summaryBar.classList.remove('translate-y-0', 'opacity-100');
    }
  }

  function showNotification(msg, type) {
    const toast = document.createElement('div');
    toast.className = `fixed top-20 right-6 z-50 p-4 rounded-2xl shadow-2xl border text-xs font-bold text-white transition-all animate-bounce
                      ${type === 'success' ? 'bg-emerald-600 border-emerald-400' : 'bg-amber-600 border-amber-400'}`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  // Real-time polling every 5 seconds
  function pollSeatStatus() {
    fetch(`/api/show/${showId}/seat-status`)
      .then(res => res.json())
      .then(data => {
        if (!data.success) return;

        const heldSeats = new Set(data.held_seats);
        const soldSeats = new Set(data.sold_seats);

        allSeatsMap.forEach(s => {
          const seatId = parseInt(s.getAttribute('data-seat-id'), 10);
          if (!seatId) return;

          // Don't override currently selected seats by active user
          if (selectedSeats.some(sel => sel.id === seatId)) return;

          if (soldSeats.has(seatId)) {
            s.className = 'seat seat-sold';
          } else if (heldSeats.has(seatId)) {
            s.className = 'seat seat-held';
          } else if (!s.classList.contains('seat-aisle')) {
            s.className = 'seat seat-available';
          }
        });
      })
      .catch(err => console.log('Seat status polling error:', err));
  }

  setInterval(pollSeatStatus, 5000);


  // FEATURE C: Best Seat Score Viewing Quality Indicator Tooltip
  const tooltip = document.createElement('div');
  tooltip.id = 'best-seat-tooltip';
  tooltip.className = 'fixed hidden z-50 bg-gray-950 text-white border border-purple-500/60 p-2.5 rounded-2xl shadow-2xl text-[11px] max-w-xs pointer-events-none transition-opacity duration-200';
  document.body.appendChild(tooltip);

  function getSeatQualityScore(seatLabel) {
    if (!seatLabel) return { stars: '★★★☆☆', label: 'Standard View', score: 3 };
    const rowChar = seatLabel.charAt(0).toUpperCase();
    const seatNum = parseInt(seatLabel.slice(1), 10) || 6;

    const rowCharCode = rowChar.charCodeAt(0);
    const minRowCode = 'A'.charCodeAt(0);
    const rowIdx = rowCharCode - minRowCode;

    let rowScore = 3;
    if (rowIdx >= 3 && rowIdx <= 6) rowScore = 5;
    else if (rowIdx === 2 || rowIdx === 7) rowScore = 4;
    else if (rowIdx === 1) rowScore = 2;
    else if (rowIdx === 0) rowScore = 1;

    const centerDist = Math.abs(seatNum - 6.5);
    let centerScore = 5;
    if (centerDist <= 1.5) centerScore = 5;
    else if (centerDist <= 3.5) centerScore = 4;
    else if (centerDist <= 4.5) centerScore = 3;
    else centerScore = 2;

    const avgScore = Math.round((rowScore * 0.6) + (centerScore * 0.4));

    if (avgScore >= 5) return { stars: '★★★★★', label: 'Prime Center — Perfect View & Angle', score: 5 };
    if (avgScore === 4) return { stars: '★★★★☆', label: 'Great View — Optimal viewing angle', score: 4 };
    if (avgScore === 3) return { stars: '★★★☆☆', label: 'Good View — Slightly off-center', score: 3 };
    if (avgScore === 2) return { stars: '★★☆☆☆', label: 'Side Angle — Wider viewing angle', score: 2 };
    return { stars: '★☆☆☆☆', label: 'Front Row — Close screen proximity', score: 1 };
  }

  document.querySelectorAll('.seat').forEach(seat => {
    function showTooltip(e) {
      if (seat.classList.contains('seat-sold') || seat.classList.contains('seat-held')) return;
      const label = seat.getAttribute('data-seat-label') || seat.textContent.trim();
      const quality = getSeatQualityScore(label);

      tooltip.innerHTML = `
        <div class="flex items-center gap-1.5 font-bold text-amber-400">
          <span>${quality.stars}</span>
          <span class="text-white">${label}</span>
        </div>
        <div class="text-[10px] text-purple-300 font-medium mt-0.5">${quality.label}</div>
      `;
      tooltip.classList.remove('hidden');

      const rect = seat.getBoundingClientRect();
      tooltip.style.left = `${Math.min(window.innerWidth - 200, Math.max(10, rect.left - 40))}px`;
      tooltip.style.top = `${rect.top - 55}px`;
    }

    function hideTooltip() {
      tooltip.classList.add('hidden');
    }

    seat.addEventListener('mouseenter', showTooltip);
    seat.addEventListener('mouseleave', hideTooltip);
    seat.addEventListener('touchstart', (e) => { showTooltip(e); }, { passive: true });
    seat.addEventListener('touchend', hideTooltip);
  });


  // FEATURE A: Watch Party Host Integration Script
  const inviteFriendsBtn = document.getElementById('invite-friends-btn');
  const watchPartyModal = document.getElementById('watch-party-modal');
  const closePartyModalBtn = document.getElementById('close-watch-party-modal-btn');
  const shareUrlInput = document.getElementById('party-share-url-input');
  const copyPartyLinkBtn = document.getElementById('copy-party-link-btn');
  const partyQrcodeContainer = document.getElementById('party-qrcode-container');
  const startPollingHostBtn = document.getElementById('start-polling-host-btn');
  const hostBanner = document.getElementById('watch-party-host-banner');
  const topSeatsText = document.getElementById('watch-party-top-seats-text');
  const autoSelectPartySeatsBtn = document.getElementById('auto-select-party-seats-btn');

  let activePartyCode = localStorage.getItem(`bingebooth_party_${showId}`) || null;
  let topVotedSeatIds = [];

  if (inviteFriendsBtn) {
    inviteFriendsBtn.addEventListener('click', () => {
      if (activePartyCode) {
        showPartyModal(activePartyCode);
      } else {
        inviteFriendsBtn.disabled = true;
        inviteFriendsBtn.innerHTML = `<span>🌀</span> Creating...`;

        fetch('/api/party/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ show_id: showId })
        })
        .then(res => res.json())
        .then(data => {
          inviteFriendsBtn.disabled = false;
          inviteFriendsBtn.innerHTML = `<span>🎉</span> Invite Friends to Pick Seats`;
          if (data.success) {
            activePartyCode = data.party_code;
            localStorage.setItem(`bingebooth_party_${showId}`, activePartyCode);
            showPartyModal(activePartyCode);
            startHostPolling(activePartyCode);
          } else {
            showNotification(data.message || 'Failed to create Watch Party.', 'error');
          }
        })
        .catch(err => {
          inviteFriendsBtn.disabled = false;
          inviteFriendsBtn.innerHTML = `<span>🎉</span> Invite Friends to Pick Seats`;
          showNotification('Error creating Watch Party.', 'error');
        });
      }
    });
  }

  function showPartyModal(partyCode) {
    const fullUrl = `${window.location.origin}/party/${partyCode}`;
    if (shareUrlInput) shareUrlInput.value = fullUrl;

    if (partyQrcodeContainer) {
      partyQrcodeContainer.innerHTML = '';
      if (typeof QRCode !== 'undefined') {
        new QRCode(partyQrcodeContainer, {
          text: fullUrl,
          width: 120,
          height: 120,
          colorDark: "#7C3AED",
          colorLight: "#ffffff"
        });
      }
    }

    if (watchPartyModal) watchPartyModal.classList.remove('hidden');
  }

  if (closePartyModalBtn && watchPartyModal) {
    closePartyModalBtn.addEventListener('click', () => {
      watchPartyModal.classList.add('hidden');
    });
  }

  if (startPollingHostBtn && watchPartyModal) {
    startPollingHostBtn.addEventListener('click', () => {
      watchPartyModal.classList.add('hidden');
      if (activePartyCode) startHostPolling(activePartyCode);
    });
  }

  if (copyPartyLinkBtn && shareUrlInput) {
    copyPartyLinkBtn.addEventListener('click', () => {
      shareUrlInput.select();
      navigator.clipboard.writeText(shareUrlInput.value);
      copyPartyLinkBtn.textContent = 'Copied! ✓';
      setTimeout(() => { copyPartyLinkBtn.textContent = 'Copy Link'; }, 2000);
      showNotification('Watch Party link copied to clipboard!', 'success');
    });
  }

  function startHostPolling(partyCode) {
    if (!hostBanner) return;
    hostBanner.classList.remove('hidden');
    pollPartyVotes(partyCode);
    setInterval(() => pollPartyVotes(partyCode), 5000);
  }

  function pollPartyVotes(partyCode) {
    fetch(`/api/party/${partyCode}/votes`)
      .then(res => res.json())
      .then(data => {
        if (data.success && topSeatsText) {
          if (data.is_expired) {
            topSeatsText.textContent = "Watch party expired (10 min session elapsed).";
            return;
          }
          if (data.top_seats && data.top_seats.length > 0) {
            topVotedSeatIds = data.top_seats.map(s => s.seat_id);
            topSeatsText.textContent = `Most voted: ${data.top_labels_summary} (${data.total_voters} guest${data.total_voters > 1 ? 's' : ''} voted)`;
          } else {
            topSeatsText.textContent = "No guests have voted yet — share link with friends!";
          }
        }
      })
      .catch(err => console.error("Party poll error:", err));
  }

  if (autoSelectPartySeatsBtn) {
    autoSelectPartySeatsBtn.addEventListener('click', () => {
      if (topVotedSeatIds.length === 0) {
        showNotification('No guest votes received yet.', 'warning');
        return;
      }
      // Select top voted seats
      selectedSeats.forEach(s => {
        const el = document.querySelector(`.seat[data-seat-id="${s.id}"]`);
        if (el) el.className = 'seat seat-available';
      });
      selectedSeats = [];
      maxSeatsAllowed = topVotedSeatIds.length;

      topVotedSeatIds.forEach(sid => {
        const el = document.querySelector(`.seat[data-seat-id="${sid}"]`);
        if (el && !el.disabled) {
          el.className = 'seat seat-selected';
          const seatLabel = el.getAttribute('data-seat-label');
          const price = floatVal(el.getAttribute('data-price'));
          selectedSeats.push({ id: sid, label: seatLabel, price: price });
        }
      });
      updateSummaryBar();
      showNotification(`Auto-selected ${selectedSeats.length} top-voted seats!`, 'success');
    });
  }

  if (activePartyCode) {
    startHostPolling(activePartyCode);
  }
});
