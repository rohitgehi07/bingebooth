document.addEventListener('DOMContentLoaded', function() {
  const toggleBtn = document.getElementById('chatbot-toggle-btn');
  const chatWindow = document.getElementById('chatbot-window');
  const closeBtn = document.getElementById('chatbot-close-btn');
  const chatForm = document.getElementById('chatbot-form');
  const chatInput = document.getElementById('chatbot-input');
  const messagesContainer = document.getElementById('chatbot-messages');
  const quickChips = document.querySelectorAll('.chat-chip');

  if (!toggleBtn || !chatWindow) return;

  function openChat() {
    chatWindow.classList.remove('closed', 'hidden');
    chatWindow.classList.add('open');
    if (chatInput) chatInput.focus();
    scrollToBottom();
  }

  function closeChat() {
    chatWindow.classList.remove('open');
    chatWindow.classList.add('closed', 'hidden');
  }

  function toggleChat() {
    if (chatWindow.classList.contains('open')) {
      closeChat();
    } else {
      openChat();
    }
  }

  toggleBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    toggleChat();
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', (e) => {
      e.preventDefault();
      closeChat();
    });
  }

  // Load persisted history from localStorage
  loadChatHistory();

  // Quick reply chip click listener
  quickChips.forEach(chip => {
    chip.addEventListener('click', (e) => {
      e.preventDefault();
      const text = chip.getAttribute('data-msg');
      if (text) sendMessage(text);
    });
  });

  // Form submit listener (Send button & Enter key press)
  if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = chatInput.value ? chatInput.value.trim() : '';
      if (text) {
        sendMessage(text);
        chatInput.value = '';
      }
    });
  }

  function sendMessage(text) {
    appendMessage(text, 'user');
    showTypingIndicator();

    // ~600ms realistic typing indicator delay
    setTimeout(() => {
      fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      })
      .then(res => res.json())
      .then(data => {
        hideTypingIndicator();
        const replyText = data.reply || data.response || "I didn't receive a response.";
        appendMessage(replyText, 'bot');
      })
      .catch(() => {
        hideTypingIndicator();
        appendMessage("Sorry, I'm having trouble connecting right now. Please try again or call 7888081697.", 'bot');
      });
    }, 600);
  }

  function appendMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} mb-3`;

    if (sender === 'user') {
      msgDiv.innerHTML = `
        <div class="bg-gradient-binge text-white px-3.5 py-2.5 rounded-2xl rounded-tr-none text-xs max-w-[80%] shadow">
          ${escapeHtml(text)}
        </div>
      `;
    } else {
      msgDiv.innerHTML = `
        <div class="flex items-start gap-2 max-w-[85%]">
          <div class="w-7 h-7 rounded-full bg-gradient-binge text-white flex items-center justify-center flex-shrink-0 text-xs shadow">
            🍿
          </div>
          <div class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-purple-100 dark:border-gray-700 px-3.5 py-2.5 rounded-2xl rounded-tl-none text-xs shadow-sm leading-relaxed">
            ${escapeHtml(text)}
          </div>
        </div>
      `;
    }

    if (messagesContainer) {
      messagesContainer.appendChild(msgDiv);
      scrollToBottom();
      saveChatHistory();
    }
  }

  function showTypingIndicator() {
    hideTypingIndicator();
    if (!messagesContainer) return;
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'flex justify-start mb-3';
    indicator.innerHTML = `
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-full bg-gradient-binge text-white flex items-center justify-center text-xs shadow">🍿</div>
        <div class="bg-white dark:bg-gray-800 border border-purple-100 dark:border-gray-700 px-3.5 py-2 rounded-2xl text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5 shadow-sm">
          <span class="font-semibold text-[11px] text-purple-600 dark:text-purple-400">Bingyy is typing</span>
          <span class="animate-bounce">●</span>
          <span class="animate-bounce [animation-delay:0.2s]">●</span>
          <span class="animate-bounce [animation-delay:0.4s]">●</span>
        </div>
      </div>
    `;
    messagesContainer.appendChild(indicator);
    scrollToBottom();
  }

  function hideTypingIndicator() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
  }

  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function saveChatHistory() {
    try {
      if (messagesContainer) {
        localStorage.setItem('bingebooth_chat_html', messagesContainer.innerHTML);
      }
    } catch (e) {}
  }

  function loadChatHistory() {
    try {
      const saved = localStorage.getItem('bingebooth_chat_html');
      if (saved && saved.trim() !== '' && messagesContainer) {
        messagesContainer.innerHTML = saved;
      }
    } catch (e) {}
  }
});
