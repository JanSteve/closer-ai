/**
 * Intelligence Designed To Evolve — Production Landing Page Script
 * CLOSER AI Single-Viewport Engine, Extended Presentation & Dual-Market Voice Studio
 */

document.addEventListener('DOMContentLoaded', () => {
  // -------------------------------------------------------------------------
  // 1. Stats Counter with easeOutCubic & IntersectionObserver
  // -------------------------------------------------------------------------
  const statCards = document.querySelectorAll('.stat-card');
  let hasCounted = false;

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function startCountUp(card, index) {
    const target = parseFloat(card.getAttribute('data-target'));
    const decimals = parseInt(card.getAttribute('data-decimals') || '0', 10);
    const countEl = card.querySelector('.count');
    if (!countEl || isNaN(target)) return;

    const duration = 1500 + index * 80;
    const startOffset = 480 + index * 90;

    setTimeout(() => {
      const startTime = performance.now();

      function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = easeOutCubic(progress) * target;

        countEl.textContent = current.toFixed(decimals);

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          countEl.textContent = target.toFixed(decimals);
        }
      }

      requestAnimationFrame(step);
    }, startOffset);
  }

  const statsFooter = document.querySelector('.stats-footer');
  if (statsFooter && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !hasCounted) {
          hasCounted = true;
          statCards.forEach((card, i) => startCountUp(card, i));
          observer.disconnect();
        }
      });
    }, { threshold: 0.25 });

    observer.observe(statsFooter);
  } else {
    // Fallback if IntersectionObserver is unsupported
    statCards.forEach((card, i) => startCountUp(card, i));
  }

  // Background Video Touch-to-Play Fallback (for mobile power-save policies)
  const bgVideo = document.querySelector('.bg-video');
  if (bgVideo) {
    const playPromise = bgVideo.play();
    if (playPromise !== undefined) {
      playPromise.catch(() => {
        const unlock = () => {
          bgVideo.play();
          document.removeEventListener('click', unlock);
          document.removeEventListener('touchstart', unlock);
        };
        document.addEventListener('click', unlock, { once: true, passive: true });
        document.addEventListener('touchstart', unlock, { once: true, passive: true });
      });
    }
  }

  // -------------------------------------------------------------------------
  // 1b. Scroll-Driven Reveal Observer (.reveal -> .is-revealed)
  // -------------------------------------------------------------------------
  const revealElements = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          obs.unobserve(entry.target);
        }
      });
    }, {
      root: null,
      rootMargin: '0px 0px -40px 0px',
      threshold: 0.08
    });

    revealElements.forEach((el) => revealObserver.observe(el));
  } else {
    revealElements.forEach((el) => el.classList.add('is-revealed'));
  }

  // -------------------------------------------------------------------------
  // 1c. Floating Frosted Header on Scroll
  // -------------------------------------------------------------------------
  const mainHeader = document.getElementById('mainHeader');
  if (mainHeader) {
    const handleHeaderScroll = () => {
      if (window.scrollY > 80) {
        mainHeader.classList.add('is-scrolled');
      } else {
        mainHeader.classList.remove('is-scrolled');
      }
    };
    window.addEventListener('scroll', handleHeaderScroll, { passive: true });
    handleHeaderScroll();
  }

  // -------------------------------------------------------------------------
  // 2. Mobile Burger Navigation (<=720px)
  // -------------------------------------------------------------------------
  const burgerBtn = document.getElementById('burgerBtn');
  const mobileOverlay = document.getElementById('mobileOverlay');
  const mobileSheet = document.getElementById('mobileSheet');
  const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
  const mobileSignInBtn = document.getElementById('mobileSignInBtn');
  let isMenuClosing = false;

  function openMobileMenu() {
    if (!burgerBtn || !mobileSheet || !mobileOverlay) return;
    isMenuClosing = false;
    mobileOverlay.classList.remove('is-closing');
    mobileSheet.classList.remove('is-closing');
    burgerBtn.setAttribute('aria-expanded', 'true');
    mobileOverlay.removeAttribute('hidden');
    mobileSheet.removeAttribute('hidden');
    document.body.classList.add('menu-open');
  }

  function closeMobileMenu(immediate = false) {
    if (!burgerBtn || !mobileSheet || !mobileOverlay) return;
    burgerBtn.setAttribute('aria-expanded', 'false');

    if (immediate) {
      mobileOverlay.setAttribute('hidden', '');
      mobileSheet.setAttribute('hidden', '');
      mobileOverlay.classList.remove('is-closing');
      mobileSheet.classList.remove('is-closing');
      document.body.classList.remove('menu-open');
      isMenuClosing = false;
      return;
    }

    if (isMenuClosing) return;
    isMenuClosing = true;
    mobileOverlay.classList.add('is-closing');
    mobileSheet.classList.add('is-closing');

    setTimeout(() => {
      mobileOverlay.setAttribute('hidden', '');
      mobileSheet.setAttribute('hidden', '');
      mobileOverlay.classList.remove('is-closing');
      mobileSheet.classList.remove('is-closing');
      document.body.classList.remove('menu-open');
      isMenuClosing = false;
    }, 250);
  }

  function toggleMobileMenu() {
    const isOpen = burgerBtn && burgerBtn.getAttribute('aria-expanded') === 'true';
    if (isOpen) {
      closeMobileMenu(false);
    } else {
      openMobileMenu();
    }
  }

  if (burgerBtn) {
    burgerBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMobileMenu();
    });
  }

  if (mobileOverlay) {
    mobileOverlay.addEventListener('click', () => closeMobileMenu(false));
  }

  mobileNavLinks.forEach((link) => {
    link.addEventListener('click', () => {
      mobileNavLinks.forEach((l) => l.classList.remove('active'));
      link.classList.add('active');
      closeMobileMenu(false);
    });
  });

  // Desktop Nav Links Active Indicator Switcher
  const desktopNavLinks = document.querySelectorAll('.nav-link');
  desktopNavLinks.forEach((link) => {
    link.addEventListener('click', () => {
      desktopNavLinks.forEach((l) => l.classList.remove('active'));
      link.classList.add('active');
    });
  });

  // ScrollSpy to update active navigation links based on scroll position
  const sections = document.querySelectorAll('section[id], body#home');
  window.addEventListener('scroll', () => {
    let currentId = 'home';
    const scrollPos = window.scrollY + 180;

    sections.forEach((sec) => {
      const top = sec.offsetTop;
      const height = sec.offsetHeight;
      if (scrollPos >= top && scrollPos < top + height) {
        currentId = sec.getAttribute('id') || 'home';
      }
    });

    desktopNavLinks.forEach((link) => {
      const href = link.getAttribute('href');
      if (href === `#${currentId}`) {
        desktopNavLinks.forEach((l) => l.classList.remove('active'));
        link.classList.add('active');
      }
    });

    mobileNavLinks.forEach((link) => {
      const href = link.getAttribute('href');
      if (href === `#${currentId}`) {
        mobileNavLinks.forEach((l) => l.classList.remove('active'));
        link.classList.add('active');
      }
    });
  }, { passive: true });

  // Global Keydown (Escape to close mobile menu & modals)
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeMobileMenu(false);
      closeDemoModal(false);
    }
  });

  // Auto-close mobile menu on desktop resize
  window.addEventListener('resize', () => {
    if (window.innerWidth > 720) {
      closeMobileMenu(true);
    }
  });

  // -------------------------------------------------------------------------
  // 3. Dual-Market Voice Engine Live Demo Modal
  // -------------------------------------------------------------------------
  const demoModal = document.getElementById('demoModal') || document.getElementById('demoModalBackdrop');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const modalMobileDoneBtn = document.getElementById('modalMobileDoneBtn');
  const ctaBtn = document.getElementById('ctaBtn');

  const btnMarketUSA = document.getElementById('btnMarketUSA');
  const btnMarketIndia = document.getElementById('btnMarketIndia');
  const voiceSelector = document.getElementById('demoVoiceSelect') || document.getElementById('voiceSelector');
  const btnVoicePreview = document.getElementById('btnVoicePreview');
  const promptChipsContainer = document.getElementById('promptChips');
  const demoUtteranceInput = document.getElementById('demoUtteranceInput');
  const demoSendBtn = document.getElementById('demoSendBtn');
  const modalVadContainer = document.getElementById('modalVadContainer');
  const modalVadStatus = document.getElementById('modalVadStatus');
  const modalAIText = document.getElementById('modalAIText');
  const btnReplayAudio = document.getElementById('btnReplayAudio');
  const demoAudioPlayer = document.getElementById('demoAudioPlayer');

  // Dossier elements
  const modalDossierStatus = document.getElementById('modalDossierStatus');
  const modalDossierMarket = document.getElementById('modalDossierMarket');
  const modalDossierLead = document.getElementById('modalDossierLead');
  const modalDossierBudget = document.getElementById('modalDossierBudget');
  const modalDossierFinancing = document.getElementById('modalDossierFinancing');
  const modalIntentFill = document.getElementById('modalIntentFill');
  const modalIntentText = document.getElementById('modalIntentText');
  const modalDossierAction = document.getElementById('modalDossierAction');

  let currentMarket = 'usa';
  let lastAudioBase64 = null;
  let isModalClosing = false;

  // Scenario presets for both markets
  const MARKET_PRESETS = {
    usa: {
      marketLabel: 'USA (Luxury Real Estate)',
      defaultVoice: 'en-US-AriaNeural',
      leadName: 'Harrison & Claire Sterling (+1-310-555-0144)',
      initialGreeting: 'Hello, this is CLOSER AI luxury real estate concierge. How can I assist you with your estate search today?',
      defaultBudget: '$6,500,000 USD (Bel Air / Beverly Hills)',
      defaultFinancing: 'Cash / Jumbo Pre-Approved',
      initialStatus: 'QUALIFYING',
      initialAction: 'Evaluating Luxury Portfolio',
      initialIntent: 80,
      prompts: [
        'Looking for a $6.5M estate in Bel Air, all cash.',
        'I am in a meeting right now, please call me tomorrow.',
        'Can we book a private showing Thursday at 2:00 PM PST?',
        'Today is not good, what about next Monday?'
      ],
      offlineReplies: {
        estate: 'Splendid. We have an architectural estate on Bellagio Road in Bel Air listed at $6.85M with panoramic ocean and city views. Would you like to schedule a private walkthrough?',
        meeting: 'I completely respect your busy schedule. I will follow up with you tomorrow afternoon at your convenience. Have a productive day.',
        showing: 'Your private VIP tour has been confirmed for Thursday at 2:00 PM PST. A confirmation packet has been dispatched to your mobile.',
        schedule: 'Understood. I have logged your preference for Monday at 2:00 PM. An acquisition specialist will reach out to confirm arrangements.'
      }
    },
    india: {
      marketLabel: 'India (Customer Care & Lead Support)',
      defaultVoice: 'en-IN-NeerjaNeural',
      leadName: 'Rohit & Ananya Sharma (+91-98800-12345)',
      initialGreeting: 'Namaste! Welcome to CLOSER AI client relationship concierge. How may I assist you with your premium residential inquiry today?',
      defaultBudget: '₹2.5 Crore (Whitefield, Bangalore)',
      defaultFinancing: 'HDFC / SBI Pre-Sanctioned Home Loan',
      initialStatus: 'QUALIFYING',
      initialAction: 'Checking RERA & Unit Inventories',
      initialIntent: 85,
      prompts: [
        'Looking for 3 BHK in Whitefield around 2.5 Crore.',
        'Is this project 100% RERA approved with bank tie-ups?',
        'I am in office right now, please WhatsApp all details.',
        'Can I book a weekend site visit for this Sunday at 11 AM?'
      ],
      offlineReplies: {
        bhk: 'Namaste! We have luxury 3 BHK residences in prime Whitefield starting at ₹2.45 Crores with club amenities and possession in 2026. Shall I arrange a site visit this Saturday?',
        rera: 'Yes, absolutely. The project is 100% RERA registered with pre-approved loans from HDFC, SBI, and ICICI Bank. All legal clearances are verified.',
        whatsapp: 'Understood. I have dispatched the complete brochure, floor plans, and pricing matrix directly to your WhatsApp. Please review at your convenience.',
        site_visit: 'Confirmed. Your site visit has been scheduled for this Sunday at 11:00 AM. Our relationship manager will welcome you at the project sales lounge.'
      }
    }
  };

  function updateMarketUI(market) {
    currentMarket = market;
    const config = MARKET_PRESETS[market];

    if (!btnMarketUSA || !btnMarketIndia) return;

    // Toggle active class and accessibility on market buttons
    if (market === 'usa') {
      btnMarketUSA.classList.add('active');
      btnMarketUSA.setAttribute('aria-selected', 'true');
      btnMarketIndia.classList.remove('active');
      btnMarketIndia.setAttribute('aria-selected', 'false');
    } else {
      btnMarketIndia.classList.add('active');
      btnMarketIndia.setAttribute('aria-selected', 'true');
      btnMarketUSA.classList.remove('active');
      btnMarketUSA.setAttribute('aria-selected', 'false');
    }

    // Set voice dropdown
    if (voiceSelector) {
      voiceSelector.value = config.defaultVoice;
    }

    // Set greeting & initial response
    if (modalAIText) {
      modalAIText.textContent = `"${config.initialGreeting}"`;
    }
    if (btnReplayAudio) {
      btnReplayAudio.style.display = 'none';
    }

    // Populate scenario chips
    if (promptChipsContainer) {
      promptChipsContainer.innerHTML = '';
      config.prompts.forEach((promptText) => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'prompt-chip';
        chip.textContent = promptText;
        chip.addEventListener('click', () => {
          if (demoUtteranceInput) {
            demoUtteranceInput.value = promptText;
          }
          executeTurn(promptText);
        });
        promptChipsContainer.appendChild(chip);
      });
    }

    // Update Dossier View
    if (modalDossierMarket) modalDossierMarket.textContent = config.marketLabel;
    if (modalDossierLead) modalDossierLead.textContent = config.leadName;
    if (modalDossierBudget) modalDossierBudget.textContent = config.defaultBudget;
    if (modalDossierFinancing) modalDossierFinancing.textContent = config.defaultFinancing;
    if (modalDossierStatus) {
      modalDossierStatus.textContent = config.initialStatus;
      modalDossierStatus.className = 'dossier-badge';
    }
    if (modalDossierAction) modalDossierAction.textContent = config.initialAction;
    if (modalIntentFill) modalIntentFill.style.width = `${config.initialIntent}%`;
    if (modalIntentText) modalIntentText.textContent = `${config.initialIntent}% High Intent`;

    // Attempt to notify local dashboard backend if running
    notifyBackendMarketMode(market);
  }

  async function notifyBackendMarketMode(market) {
    try {
      await fetch('/api/market_mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: market })
      });
    } catch {
      // Backend not running on same origin; ignore silently
    }
  }

  function openDemoModal() {
    if (!demoModal) return;
    isModalClosing = false;
    demoModal.classList.remove('is-closing');
    demoModal.classList.add('is-open');
    demoModal.removeAttribute('hidden');
    demoModal.style.display = 'flex';
    document.body.classList.add('modal-open');
    updateMarketUI(currentMarket);
  }

  function closeDemoModal(immediate = false) {
    if (!demoModal) return;

    // Immediately halt voice output and speech synthesis
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (demoAudioPlayer) {
      demoAudioPlayer.pause();
      demoAudioPlayer.currentTime = 0;
    }
    stopSpeakingUI();

    if (immediate) {
      demoModal.classList.remove('is-open', 'is-closing');
      demoModal.setAttribute('hidden', '');
      demoModal.style.display = 'none';
      document.body.classList.remove('modal-open');
      isModalClosing = false;
      return;
    }

    if (isModalClosing) return;
    isModalClosing = true;
    demoModal.classList.add('is-closing');

    setTimeout(() => {
      demoModal.classList.remove('is-open', 'is-closing');
      demoModal.setAttribute('hidden', '');
      demoModal.style.display = 'none';
      document.body.classList.remove('modal-open');
      isModalClosing = false;
    }, 220);
  }

  window.openModalHandler = openDemoModal;
  window.closeModalHandler = closeDemoModal;

  // CTA Button scrolls down to #product without opening intrusive popup modal
  if (ctaBtn) {
    ctaBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const productEl = document.getElementById('product');
      if (productEl) {
        productEl.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }
  if (modalCloseBtn) modalCloseBtn.addEventListener('click', () => closeDemoModal(false));
  if (modalMobileDoneBtn) modalMobileDoneBtn.addEventListener('click', () => closeDemoModal(false));

  if (demoModal) {
    demoModal.addEventListener('click', (e) => {
      if (e.target === demoModal) {
        closeDemoModal(false);
      }
    });
  }

  if (btnMarketUSA) {
    btnMarketUSA.addEventListener('click', () => updateMarketUI('usa'));
  }
  if (btnMarketIndia) {
    btnMarketIndia.addEventListener('click', () => updateMarketUI('india'));
  }

  // -------------------------------------------------------------------------
  // 4. Voice Synthesis & Audio Playback Pipeline
  // -------------------------------------------------------------------------
  function startSpeakingUI() {
    if (modalVadContainer) {
      const waveform = modalVadContainer.querySelector('.vad-waveform') || document.getElementById('modalVadWaveform');
      if (waveform) waveform.classList.add('active');
    }
    if (modalVadStatus) {
      modalVadStatus.textContent = '● SYNTHESIZING & SPEAKING (VAD ACTIVE)';
      modalVadStatus.style.color = '#38bdf8';
    }
  }

  function stopSpeakingUI() {
    if (modalVadContainer) {
      const waveform = modalVadContainer.querySelector('.vad-waveform') || document.getElementById('modalVadWaveform');
      if (waveform) waveform.classList.remove('active');
    }
    if (modalVadStatus) {
      modalVadStatus.textContent = '● READY (VAD & TELEPHONY ACTIVE)';
      modalVadStatus.style.color = '#10b981';
    }
  }

  function playAudioResponse(audioBase64, fallbackText, onEndedCallback) {
    if (audioBase64) {
      lastAudioBase64 = audioBase64;
      if (btnReplayAudio) btnReplayAudio.style.display = 'inline-flex';

      demoAudioPlayer.src = `data:audio/wav;base64,${audioBase64}`;
      startSpeakingUI();

      demoAudioPlayer.play().catch(() => {
        speakBrowserTTS(fallbackText, onEndedCallback);
      });

      demoAudioPlayer.onended = () => {
        stopSpeakingUI();
        if (onEndedCallback) onEndedCallback();
      };
      demoAudioPlayer.onerror = () => {
        stopSpeakingUI();
        speakBrowserTTS(fallbackText, onEndedCallback);
      };
      return;
    }

    speakBrowserTTS(fallbackText, onEndedCallback);
  }

  function speakBrowserTTS(text, onEndedCallback) {
    if (!('speechSynthesis' in window)) {
      if (onEndedCallback) onEndedCallback();
      return;
    }
    window.speechSynthesis.cancel();

    const cleanText = text.replace(/₹/g, 'Rupees ').replace(/\$/g, 'Dollars ');
    const utterance = new SpeechSynthesisUtterance(cleanText);

    const voiceVal = voiceSelector ? voiceSelector.value : 'en-US-AriaNeural';
    const isIndia = voiceVal.includes('en-IN') || currentMarket === 'india';
    const voices = window.speechSynthesis.getVoices();

    const targetVoice = voices.find((v) => {
      if (isIndia) return v.lang.includes('IN') || v.lang.includes('en-GB');
      return v.lang.includes('US') || v.lang.includes('en');
    });

    if (targetVoice) utterance.voice = targetVoice;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => startSpeakingUI();
    utterance.onend = () => {
      stopSpeakingUI();
      if (onEndedCallback) onEndedCallback();
    };
    utterance.onerror = () => {
      stopSpeakingUI();
      if (onEndedCallback) onEndedCallback();
    };

    window.speechSynthesis.speak(utterance);
  }

  if (btnReplayAudio) {
    btnReplayAudio.addEventListener('click', () => {
      if (lastAudioBase64) {
        demoAudioPlayer.currentTime = 0;
        startSpeakingUI();
        demoAudioPlayer.play().catch(() => stopSpeakingUI());
      } else if (modalAIText) {
        speakBrowserTTS(modalAIText.textContent.replace(/^"|"$/g, ''));
      }
    });
  }

  // Voice Sample Preview Button
  if (btnVoicePreview) {
    btnVoicePreview.addEventListener('click', async () => {
      const selectedVoice = voiceSelector ? voiceSelector.value : 'en-US-AriaNeural';
      startSpeakingUI();

      try {
        const res = await fetch('/api/turn', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ utterance: 'PREVIEW_SAMPLE', voice: selectedVoice })
        });
        if (res.ok) {
          const data = await res.json();
          if (modalAIText) modalAIText.textContent = `"${data.reply}"`;
          playAudioResponse(data.audio_base64, data.reply);
          return;
        }
      } catch {
        // Fallback to local speech
      }

      const sampleMsg = selectedVoice.includes('IN')
        ? 'Namaste. CLOSER AI Indian customer care engine is active and ready to assist you.'
        : 'Hello. CLOSER AI luxury real estate concierge is active and ready to assist you.';

      if (modalAIText) modalAIText.textContent = `"${sampleMsg}"`;
      speakBrowserTTS(sampleMsg);
    });
  }

  // -------------------------------------------------------------------------
  // 5. Conversational Turn Execution
  // -------------------------------------------------------------------------
  async function executeTurn(utteranceText) {
    if (!utteranceText || !utteranceText.trim()) return;
    const text = utteranceText.trim();
    const selectedVoice = voiceSelector ? voiceSelector.value : 'en-US-AriaNeural';

    if (demoSendBtn) {
      demoSendBtn.disabled = true;
      demoSendBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Processing...</span>';
    }
    startSpeakingUI();

    try {
      const res = await fetch('/api/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ utterance: text, voice: selectedVoice })
      });

      if (res.ok) {
        const data = await res.json();
        if (modalAIText) modalAIText.textContent = `"${data.reply}"`;

        if (data.dossier) {
          if (modalDossierStatus) {
            modalDossierStatus.textContent = data.dossier.qualified ? 'QUALIFIED' : 'QUALIFYING';
            modalDossierStatus.className = data.dossier.qualified ? 'dossier-badge green' : 'dossier-badge';
          }
          if (modalDossierBudget && data.dossier.budget_bracket) {
            modalDossierBudget.textContent = data.dossier.budget_bracket;
          }
          if (modalDossierFinancing && data.dossier.financing_status) {
            modalDossierFinancing.textContent = data.dossier.financing_status;
          }
          if (modalDossierAction && data.dossier.follow_up_note) {
            modalDossierAction.textContent = data.dossier.follow_up_note;
          }
          if (modalIntentFill && data.dossier.qualification_score !== undefined) {
            modalIntentFill.style.width = `${data.dossier.qualification_score}%`;
            modalIntentText.textContent = `${data.dossier.qualification_score}% Intent Score`;
          }
        }

        playAudioResponse(data.audio_base64, data.reply);
        if (demoSendBtn) {
          demoSendBtn.disabled = false;
          demoSendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> <span>Simulate Turn</span>';
        }
        return;
      }
    } catch {
      // Local fallback simulation if server API is offline
    }

    // Local deterministic fallback
    const config = MARKET_PRESETS[currentMarket];
    const lower = text.toLowerCase();
    let fallbackReply = '';

    if (currentMarket === 'usa') {
      if (lower.includes('meeting') || lower.includes('busy') || lower.includes('later')) {
        fallbackReply = config.offlineReplies.meeting;
        if (modalDossierStatus) {
          modalDossierStatus.textContent = 'SCHEDULE FRICTION';
          modalDossierStatus.className = 'dossier-badge amber';
        }
        if (modalDossierAction) modalDossierAction.textContent = 'Follow up scheduled for tomorrow';
        if (modalIntentFill) {
          modalIntentFill.style.width = '70%';
          modalIntentText.textContent = '70% Intent (Polite Friction)';
        }
      } else if (lower.includes('thursday') || lower.includes('showing') || lower.includes('tour') || lower.includes('book')) {
        fallbackReply = config.offlineReplies.showing;
        if (modalDossierStatus) {
          modalDossierStatus.textContent = 'TOUR BOOKED';
          modalDossierStatus.className = 'dossier-badge green';
        }
        if (modalDossierAction) modalDossierAction.textContent = 'Thursday at 2:00 PM PST VIP Tour';
        if (modalIntentFill) {
          modalIntentFill.style.width = '95%';
          modalIntentText.textContent = '95% Verified Intent';
        }
      } else if (lower.includes('monday') || lower.includes('not good')) {
        fallbackReply = config.offlineReplies.schedule;
        if (modalDossierStatus) {
          modalDossierStatus.textContent = 'CALLBACK SET';
          modalDossierStatus.className = 'dossier-badge amber';
        }
        if (modalDossierAction) modalDossierAction.textContent = 'Follow up scheduled for Monday';
        if (modalIntentFill) {
          modalIntentFill.style.width = '80%';
          modalIntentText.textContent = '80% Intent (Scheduled)';
        }
      } else {
        fallbackReply = config.offlineReplies.estate;
        if (modalDossierStatus) {
          modalDossierStatus.textContent = 'QUALIFIED';
          modalDossierStatus.className = 'dossier-badge';
        }
        if (modalDossierAction) modalDossierAction.textContent = 'Matched: Bel Air 10484 Bellagio ($6.85M)';
        if (modalIntentFill) {
          modalIntentFill.style.width = '85%';
          modalIntentText.textContent = '85% Active Search';
        }
      }
    } else {
      if (lower.includes('rera') || lower.includes('legal') || lower.includes('bank')) {
        fallbackReply = config.offlineReplies.rera;
        if (modalDossierStatus) {
          modalDossierStatus.textContent = 'VERIFIED';
          modalDossierStatus.className = 'dossier-badge green';
        }
        if (modalDossierAction) modalDossierAction.textContent = 'RERA Validated • SBI/HDFC Tie-up';
        if (modalIntentFill) {
          modalIntentFill.style.width = '90%';
          modalIntentText.textContent = '90% High Intent';
        }
      } else if (lower.includes('whatsapp') || lower.includes('office') || lower.includes('busy')) {
        fallbackReply = config.offlineReplies.whatsapp;
        if (modalDossierStatus) {
          modalDossierStatus.textContent = 'WHATSAPP SENT';
          modalDossierStatus.className = 'dossier-badge amber';
        }
        if (modalDossierAction) modalDossierAction.textContent = 'Brochure Dispatched to +91-98800-12345';
        if (modalIntentFill) {
          modalIntentFill.style.width = '75%';
          modalIntentText.textContent = '75% Active Lead';
        }
      } else if (lower.includes('sunday') || lower.includes('weekend') || lower.includes('visit')) {
        fallbackReply = config.offlineReplies.site_visit;
        if (modalDossierStatus) {
          modalDossierStatus.textContent = 'VISIT BOOKED';
          modalDossierStatus.className = 'dossier-badge green';
        }
        if (modalDossierAction) modalDossierAction.textContent = 'Sunday 11:00 AM Site Visit Confirmed';
        if (modalIntentFill) {
          modalIntentFill.style.width = '95%';
          modalIntentText.textContent = '95% High Intent (Site Visit)';
        }
      } else {
        fallbackReply = config.offlineReplies.bhk;
        if (modalDossierStatus) {
          modalDossierStatus.textContent = 'INVENTORY MATCH';
          modalDossierStatus.className = 'dossier-badge';
        }
        if (modalDossierAction) modalDossierAction.textContent = 'Matched: Whitefield 3 BHK (₹2.45 Cr)';
        if (modalIntentFill) {
          modalIntentFill.style.width = '85%';
          modalIntentText.textContent = '85% In Conversation';
        }
      }
    }

    if (modalAIText) modalAIText.textContent = `"${fallbackReply}"`;
    playAudioResponse(null, fallbackReply);

    if (demoSendBtn) {
      demoSendBtn.disabled = false;
      demoSendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> <span>Simulate Turn</span>';
    }
  }

  if (demoSendBtn) {
    demoSendBtn.addEventListener('click', () => {
      if (demoUtteranceInput) executeTurn(demoUtteranceInput.value);
    });
  }

  if (demoUtteranceInput) {
    demoUtteranceInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        executeTurn(demoUtteranceInput.value);
      }
    });
  }

  // -------------------------------------------------------------------------
  // 6. Dual-Market Showcase Tab Switching (#markets)
  // -------------------------------------------------------------------------
  window.showMarketTab = function (market) {
    const tabUSA = document.getElementById('tabUSA');
    const tabIndia = document.getElementById('tabIndia');
    const panelUSA = document.getElementById('panelUSA');
    const panelIndia = document.getElementById('panelIndia');

    if (market === 'usa') {
      if (tabUSA) {
        tabUSA.classList.add('active');
        tabUSA.setAttribute('aria-selected', 'true');
      }
      if (tabIndia) {
        tabIndia.classList.remove('active');
        tabIndia.setAttribute('aria-selected', 'false');
      }
      if (panelIndia) {
        panelIndia.classList.remove('active');
      }
      if (panelUSA) {
        panelUSA.classList.add('active');
      }
    } else {
      if (tabIndia) {
        tabIndia.classList.add('active');
        tabIndia.setAttribute('aria-selected', 'true');
      }
      if (tabUSA) {
        tabUSA.classList.remove('active');
        tabUSA.setAttribute('aria-selected', 'false');
      }
      if (panelUSA) {
        panelUSA.classList.remove('active');
      }
      if (panelIndia) {
        panelIndia.classList.add('active');
      }
    }
  };

  window.playVoiceSample = async function (market) {
    const isIndia = market === 'india';
    const text = isIndia
      ? "Namaste! This is Priya from Customer Care. I would be delighted to assist you with your 3 BHK enquiry in Whitefield. The project is 100% RERA approved. May I send the brochure directly to your WhatsApp?"
      : "Good morning! This is Sophia with CLOSER Luxury Concierge. I have the private dossier ready for the 10484 Bellagio Road estate in Bel Air. Are you currently looking to tour this Thursday?";
    const voice = isIndia ? 'en-IN-NeerjaNeural' : 'en-US-AriaNeural';

    try {
      const res = await fetch('/api/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ utterance: 'STUDIO_SAMPLE', text: text, voice: voice })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64) {
          playAudioResponse(data.audio_base64, data.reply);
          return;
        }
      }
    } catch {
      // Fallback to local speech
    }

    speakBrowserTTS(text);
  };

  // -------------------------------------------------------------------------
  // 7. Interactive Voice Soundboard Studio (#voice-studio)
  // -------------------------------------------------------------------------
  let studioSelectedVoice = 'en-US-AriaNeural';
  let studioSelectedScenario = 'friction_busy';
  let studioSelectedRate = '-3%';
  let studioSelectedSpeed = '1.0';
  let studioSelectedLLM = 'llama-3.3-70b';
  let isAcousticCellular = false;

  const STUDIO_SCENARIOS = {
    friction_busy: {
      speaker: 'CLOSER AI (Sophia / Guy):',
      text: "I completely understand and respect your schedule. I will make a priority note to ring you back tomorrow afternoon. Would 2:00 PM work best for you?"
    },
    just_browsing: {
      speaker: 'CLOSER AI (Sophia):',
      text: "Gotcha, totally understand... Browsing is the most exciting part! Many of our private clients start looking a few months out. If a quiet off-market property with skyline views opened up at the right number, what would be your ideal timeline?"
    },
    luxury_cash: {
      speaker: 'CLOSER AI (Sophia):',
      text: "Excellent. For an all-cash acquisition in Bel Air at $8.5M, we coordinate direct proof-of-funds with private escrow. Would you prefer a Thursday private walkthrough?"
    },
    us_1031_exchange: {
      speaker: 'CLOSER AI (Sophia • DeepSeek 671B MoE):',
      text: "Understood! We coordinate 1031 tax-deferred exchanges with qualified intermediaries for our private clients. We currently have three off-market replacement properties in Bel Air and Beverly Hills that satisfy strict 45-day identification rules. Are you currently in your exchange period?"
    },
    exclusive_listing: {
      speaker: 'CLOSER AI (Guy):',
      text: "That's wonderful — having great representation is crucial! Are you officially committed with an exclusive agreement, or are you open to seeing private pocket listings before they hit the MLS?"
    },
    india_greeting: {
      speaker: 'CLOSER AI (Priya):',
      text: "Namaste sir... This is Priya from Customer Care and Client Relations. Thank you for reaching out to us regarding your residential inquiry in Bangalore. How may I assist you today?"
    },
    india_bhk_rera: {
      speaker: 'CLOSER AI (Priya):',
      text: "Namaste! The 3 BHK residences in Whitefield priced at ₹2.45 Crores are 100% RERA approved with Karnataka registration PRM/KA/RERA/1251. I have dispatched the floor plan to your WhatsApp."
    },
    india_rera_carpet: {
      speaker: 'CLOSER AI (Priya • BLOOMZ 176B Multilingual):',
      text: "Namaste! All our listed configurations offer 100% RERA carpet area transparency without misleading super built-up inflation. For the Whitefield 3 BHK, the net carpet area is 1,640 square feet with full occupancy certification. Shall I send the official RERA sanction layout to your WhatsApp?"
    },
    india_ticket: {
      speaker: 'CLOSER AI (Prabhat):',
      text: "I completely understand your concern regarding possession timelines. I have logged official priority grievance ticket #CC-84291 with our project engineering directorate. You will receive an SMS and WhatsApp update within 2 hours."
    },
    india_office_hours: {
      speaker: 'CLOSER AI (Priya / Prabhat):',
      text: "I completely understand and respect your busy office hours, sir! I won't disturb you right now. I will ring you back after 6:00 PM today, and I have already forwarded all property photos and cost sheets to your WhatsApp."
    }
  };

  window.setStudioLLM = async function (el, modelId) {
    document.querySelectorAll('.llm-pill').forEach((btn) => btn.classList.remove('active'));
    el.classList.add('active');
    studioSelectedLLM = modelId || 'llama-3.3-70b';

    const llmTag = document.getElementById('studioLLMTag');
    const latencyTag = document.getElementById('studioLatency');

    try {
      const res = await fetch('/api/llm_select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: studioSelectedLLM })
      });
      if (res.ok) {
        const data = await res.json();
        const m = data.model;
        if (llmTag && m) {
          llmTag.innerHTML = `ENGINE: <strong>${m.parameter_scale || '175B+'}</strong>`;
        }
        if (latencyTag && m) {
          latencyTag.textContent = `${m.target_latency_ms || 88} ms`;
        }
      }
    } catch {
      // Offline fallback indicator
      if (latencyTag) {
        const latMap = { 'llama-3.3-70b': '88 ms', 'bloomz-176b': '280 ms', 'deepseek-v3': '195 ms', 'command-r-plus': '175 ms', 'qwen-2.5-72b': '115 ms' };
        latencyTag.textContent = latMap[studioSelectedLLM] || '120 ms';
      }
    }
  };

  window.selectStudioVoice = function (el) {
    document.querySelectorAll('.voice-pill').forEach((btn) => btn.classList.remove('active'));
    el.classList.add('active');
    studioSelectedVoice = el.getAttribute('data-voice') || 'en-US-AriaNeural';
  };

  window.setStudioCadence = function (el, rate, speed) {
    document.querySelectorAll('.cadence-pill').forEach((btn) => btn.classList.remove('active'));
    el.classList.add('active');
    studioSelectedRate = rate || '-3%';
    studioSelectedSpeed = speed || '1.0';
  };

  window.setAcousticMode = function (isCellular) {
    isAcousticCellular = !!isCellular;
    const btnStudio = document.getElementById('btnAcousticStudio');
    const btnCell = document.getElementById('btnAcousticCellular');
    if (btnStudio && btnCell) {
      if (isCellular) {
        btnStudio.classList.remove('active');
        btnCell.classList.add('active');
      } else {
        btnStudio.classList.add('active');
        btnCell.classList.remove('active');
      }
    }
  };

  window.selectStudioScenario = function (el) {
    document.querySelectorAll('.scenario-btn').forEach((btn) => btn.classList.remove('active'));
    el.classList.add('active');
    studioSelectedScenario = el.getAttribute('data-scenario') || 'friction_busy';

    const item = STUDIO_SCENARIOS[studioSelectedScenario];
    const speakerEl = document.getElementById('studioSpeakerName');
    const textEl = document.getElementById('studioSpeechText');

    if (speakerEl && item) speakerEl.innerHTML = `<i class="fa-solid fa-robot"></i> ${item.speaker}`;
    if (textEl && item) textEl.textContent = `"${item.text}"`;
  };

  window.runStudioSimulation = async function () {
    const item = STUDIO_SCENARIOS[studioSelectedScenario] || STUDIO_SCENARIOS['friction_busy'];
    const waveform = document.getElementById('studioWaveform');
    const statusEl = document.getElementById('studioStatus');

    if (waveform) waveform.classList.add('is-playing');
    if (statusEl) {
      statusEl.textContent = isAcousticCellular ? '● CELLULAR IVR STREAMING (8kHz)' : '● TRANSMITTING NEURAL AUDIO';
      statusEl.style.color = '#38bdf8';
    }

    const resetStudioUI = () => {
      if (waveform) waveform.classList.remove('is-playing');
      if (statusEl) {
        statusEl.textContent = '● AUDIO ENGINE READY';
        statusEl.style.color = '#10b981';
      }
    };

    // 1. Try backend high-fidelity synthesis first
    try {
      const res = await fetch('/api/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          utterance: 'STUDIO_SAMPLE',
          text: item.text,
          voice: studioSelectedVoice,
          rate: studioSelectedRate,
          model_id: studioSelectedLLM
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64) {
          playAudioResponse(data.audio_base64, data.reply, resetStudioUI);
          return;
        }
      }
    } catch {
      // Backend unavailable; fallback to browser speech
    }

    // 2. Browser speech synthesis fallback
    if (!('speechSynthesis' in window)) {
      setTimeout(resetStudioUI, 2500);
      return;
    }

    window.speechSynthesis.cancel();
    const cleanText = item.text.replace(/₹/g, 'Rupees ').replace(/\$/g, 'Dollars ');
    const utter = new SpeechSynthesisUtterance(cleanText);

    const isIndia = studioSelectedVoice.includes('IN');
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find((v) => {
      if (isIndia) return v.lang.includes('IN') || v.lang.includes('en-GB');
      return v.lang.includes('US') || v.lang.includes('en');
    });

    if (voice) utter.voice = voice;
    utter.rate = parseFloat(studioSelectedSpeed) || 1.0;

    utter.onend = resetStudioUI;
    utter.onerror = resetStudioUI;

    window.speechSynthesis.speak(utter);
  };

  // -------------------------------------------------------------------------
  // 8. Interactive Unit Economics & ROI Calculator (#roi)
  // -------------------------------------------------------------------------
  let roiCurrency = 'usd';

  window.setRoiCurrency = function (curr) {
    roiCurrency = curr;
    const currUSD = document.getElementById('currUSD');
    const currINR = document.getElementById('currINR');
    const sliderComm = document.getElementById('sliderCommission');

    if (curr === 'usd') {
      if (currUSD) currUSD.classList.add('active');
      if (currINR) currINR.classList.remove('active');
      if (sliderComm) {
        sliderComm.min = 5000;
        sliderComm.max = 150000;
        sliderComm.step = 5000;
        sliderComm.value = 25000;
      }
    } else {
      if (currINR) currINR.classList.add('active');
      if (currUSD) currUSD.classList.remove('active');
      if (sliderComm) {
        sliderComm.min = 100000; // ₹1 Lakh
        sliderComm.max = 5000000; // ₹50 Lakhs
        sliderComm.step = 50000;
        sliderComm.value = 500000; // ₹5 Lakhs
      }
    }
    updateRoiCalc();
  };

  window.updateRoiCalc = function () {
    const sliderLeads = document.getElementById('sliderLeads');
    const sliderComm = document.getElementById('sliderCommission');
    const sliderConv = document.getElementById('sliderConv');

    if (!sliderLeads || !sliderComm || !sliderConv) return;

    const leads = parseInt(sliderLeads.value, 10);
    const comm = parseInt(sliderComm.value, 10);
    const convRate = parseFloat(sliderConv.value);

    // Label updates
    const valLeads = document.getElementById('valLeads');
    const valCommission = document.getElementById('valCommission');
    const valConv = document.getElementById('valConv');

    if (valLeads) valLeads.textContent = `${leads.toLocaleString()} Leads`;
    if (valCommission) {
      valCommission.textContent = roiCurrency === 'usd'
        ? `$${comm.toLocaleString()} USD`
        : `₹${(comm / 100000).toFixed(1)} Lakhs`;
    }
    if (valConv) valConv.textContent = `${convRate.toFixed(1)}%`;

    // Calculations:
    // CLOSER AI boosts lead capture by responding instantly to 100% of calls (typically +40% more qualified bookings)
    const extraQualifiedShowings = Math.round(leads * 0.09);
    const extraClosedDeals = (extraQualifiedShowings * (convRate / 100) * 1.5).toFixed(1);
    const revenueUplift = Math.round(parseFloat(extraClosedDeals) * comm);
    const hoursSaved = Math.round(leads * 0.5); // 30 minutes saved per lead in manual follow up

    const roiShowings = document.getElementById('roiShowings');
    const roiDeals = document.getElementById('roiDeals');
    const roiRevenue = document.getElementById('roiRevenue');
    const roiHours = document.getElementById('roiHours');

    if (roiShowings) roiShowings.textContent = `+${extraQualifiedShowings}`;
    if (roiDeals) roiDeals.textContent = `+${extraClosedDeals}`;
    if (roiRevenue) {
      roiRevenue.textContent = roiCurrency === 'usd'
        ? `+$${revenueUplift.toLocaleString()}`
        : `+₹${(revenueUplift / 100000).toFixed(1)} Lakhs`;
    }
    if (roiHours) roiHours.textContent = `${hoursSaved} hrs`;
  };

  // Run initial calculation
  updateRoiCalc();
});
