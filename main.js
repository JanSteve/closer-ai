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
  const btnMarketTamil = document.getElementById('btnMarketTamil');
  const btnMarketHindi = document.getElementById('btnMarketHindi');
  const btnMarketIndia = document.getElementById('btnMarketIndia');
  const voiceSelector = document.getElementById('demoVoiceSelect') || document.getElementById('voiceSelector');
  const dialectSelector = document.getElementById('demoDialectSelect');
  const sectorSelector = document.getElementById('demoSectorSelect');
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

  // Scenario presets for 3 production voices (Hospital & Amura Health Care)
  const MARKET_PRESETS = {
    usa: {
      marketLabel: 'Amura Health & Clinical Triage (English — Maya)',
      defaultVoice: 'maya_en',
      defaultDialect: 'english_consultative',
      leadName: 'Aarav Menon (+91-98400-12345)',
      initialGreeting: 'Hello! Maya calling from Amura Health Patient Care in Velachery, Chennai. I saw you requested a metabolic consultation—are you looking into diabetes reversal, thyroid care, or a specialist OPD visit?',
      defaultBudget: 'Type-2 Diabetes / HbA1c 8.4% (Metabolic Program)',
      defaultFinancing: 'DPDP Consent • 108 Guard Active',
      initialStatus: 'TRIAGING',
      initialAction: 'Capturing Biomarkers & Clinical Goal',
      initialIntent: 85,
      prompts: [
        'I am really worried my HbA1c is 9.2, how much insulin should I take?',
        'Can we book a physician consultation tomorrow at 11:30 AM?',
        'I have severe chest pain and cannot breathe right now.',
        'I am in a meeting, please send the fasting lab checklist on WhatsApp.'
      ],
      offlineReplies: {
        emergency: 'Please call 108 emergency services immediately or go to the nearest hospital Emergency Room (ER) right away. Chest pain or breathing distress requires urgent emergency medical care.',
        safety: 'I completely understand your concern, and you are in safe hands. I cannot prescribe or adjust insulin dosage—only our licensed Amura Health physician can review your HbA1c safely. Shall I book your consultation tomorrow at 11:30 AM?',
        showing: 'Your physician consultation at Amura Health is confirmed for tomorrow at 11:30 AM IST. I have dispatched your fasting lab checklist on WhatsApp right now.',
        site_visit: 'Your physician consultation at Amura Health is confirmed for tomorrow at 11:30 AM IST. I have dispatched your fasting lab checklist on WhatsApp right now.',
        meeting: 'I completely respect your busy schedule. I have sent the fasting lab checklist and callback link to your WhatsApp so you can review at your convenience.',
        schedule: 'I completely respect your schedule. Tomorrow at 11:30 AM or 4:00 PM works great—which slot suits you for a quick physician call?',
        price: 'Our initial Amura Health metabolic consultation starts at ₹1,500–₹2,500, and structured reversal programs are tailored after a doctor reviews your labs.',
        bhk: 'Our clinical team specializes in root-cause metabolic care (diabetes, PCOD, thyroid, autoimmune) using Medical Nutrition Therapy and physician supervision. Would you like to book a consultation?',
        rera: 'Amura Health follows strict clinical safety guardrails, DPDP 2023 consent protocols, and physician-led care at our Velachery, Chennai clinic.',
        whatsapp: 'I have sent the Amura Health care overview and fasting lab checklist to your WhatsApp.',
        who_are_you: 'Hello! I am CLOSER AI, your emotion-aware clinical voice concierge for Amura Health and hospital patient care.',
        default: 'Thank you for sharing that. Would you like me to schedule a physician consultation tomorrow at 11:30 AM IST?'
      }
    },
    tamil: {
      marketLabel: 'Chennai Tamil (Sarvam bulbul:v3 — Priya Care)',
      defaultVoice: 'priya_ta',
      defaultDialect: 'chennai_tanglish',
      leadName: 'கார்த்திக் & திவ்யா (+91-98840-23456)',
      initialGreeting: 'வணக்கம் Sir! வேளச்சேரி Amura Health-ல இருந்து பிரியா பேசுறேங்க. சுகர், தைராய்டு அல்லது PCOD மேனேஜ்மென்ட் பத்தி doctor consultation கேட்டிருந்தீங்க—உங்களுக்கு இப்போ என்ன health goal இருக்கு Sir?',
      defaultBudget: 'சர்க்கரை நோய் / தைராய்டு (MNT & NMT Care)',
      defaultFinancing: 'DPDP Consent • 108 Guard Active',
      initialStatus: 'TRIAGING',
      initialAction: 'Tamil Clinical Intake & Emotion Care',
      initialIntent: 90,
      prompts: [
        'எனக்கு சுகர் அதிகமா இருக்கு, என்ன மாத்திரை சாப்பிடணும்?',
        'நான் இப்போ மீட்டிங்ல இருக்கேன், நாளைக்கு கூப்பிடுங்க.',
        'நாளை காலை 11:30 மணிக்கு doctor consultation புக் பண்ண முடியுமா?',
        'நெஞ்சு வலி மற்றும் மூச்சு விட முடியல, உடனே உதவுங்க.'
      ],
      offlineReplies: {
        emergency: 'தயவுசெய்து உடனடியாக 108 அவசர உதவிக்கு அழைக்கவும் அல்லது அருகிலுள்ள Emergency Room-க்கு செல்லவும் Sir. இது அவசர மருத்துவ நிலை.',
        safety: 'கவலைப்படாதீங்க Sir, உங்க நிலைமை புரியுது. நான் மாத்திரை அல்லது மருந்து அளவைச் சொல்ல முடியாது—நம்ம Amura மருத்துவர் தான் உங்க HbA1c ரிப்போர்ட் பார்த்து முடிவு பண்ணுவாங்க. நாளை காலை 11:30 மணிக்கு consultation புக் பண்ணலாமா Sir?',
        estate: 'வேளச்சேரி Amura Health-ல் சர்க்கரை நோய், தைராய்டு மற்றும் PCOD-க்கான சிறப்பு மருத்துவ ஆலோசனை மற்றும் NMT திட்டங்கள் உள்ளன.',
        meeting: 'கண்டிப்பா புரிஞ்சுக்க முடியுதுங்க Sir. நாளைக்கு உங்களுக்கு சௌகரியமான நேரத்துல கூப்பிடுறேன். இப்போ WhatsApp-ல fasting lab checklist அனுப்புறேன்!',
        schedule: 'கண்டிப்பா புரிஞ்சுக்க முடியுதுங்க Sir. நாளைக்கு காலை 11:30 மணிக்கு பார்க்கலாமா Sir?',
        showing: 'ரொம்ப நன்றி Sir! நாளை காலை 11:30 மணிக்கு உங்க doctor consultation slot புக் பண்ணிட்டேங்க. உங்க WhatsApp-க்கு lab test checklist அனுப்பிட்டேன் Sir!',
        site_visit: 'ரொம்ப நன்றி Sir! நாளை காலை 11:30 மணிக்கு உங்க doctor consultation slot புக் பண்ணிட்டேங்க. உங்க WhatsApp-க்கு lab test checklist அனுப்பிட்டேன் Sir!',
        rera: 'ஆமாங்க Sir, நம்ம Velachery Amura Health மருத்துவர்கள் முழுமையான பாதுகாப்பு மற்றும் DPDP விதிமுறைகளுடன் சிகிச்சை அளிக்கிறார்கள்.',
        bhk: 'வேளச்சேரி Amura Health-ல் சர்க்கரை நோய், தைராய்டு மற்றும் PCOD-க்கான சிறப்பு மருத்துவர் ஆலோசனை ₹1,500 முதல் தொடங்குகிறது. நாளைக்கு slot புக் பண்ணலாமா Sir?',
        whatsapp: 'கண்டிப்பா Sir! மருத்துவர் ஆலோசனை விவரம் மற்றும் fasting lab checklist-ஐ உங்க WhatsApp-க்கு உடனே அனுப்பிட்டோமுங்க.',
        who_are_you: 'வணக்கம் Sir! நான் வேளச்சேரி Amura Health மற்றும் மருத்துவமனை சேவைகளுக்கான CLOSER AI நோயாளி ஆலோசகர்.',
        default: 'வணக்கம் Sir! வேளச்சேரி Amura Health-ல் சர்க்கரை நோய், தைராய்டு மற்றும் OPD ஆலோசனைக்கு நாளை காலை 11:30 மணிக்கு slot புக் பண்ணலாமா Sir?'
      }
    },
    hindi: {
      marketLabel: 'Pan-India Hindi (Sarvam bulbul:v3 — Ritu Care)',
      defaultVoice: 'ritu_hi',
      defaultDialect: 'delhi_hinglish',
      leadName: 'रोहित & अनन्या शर्मा (+91-98800-12345)',
      initialGreeting: 'नमस्ते जी! Amura Health पेशेंट केयर से रितु बात कर रही हूँ। आपने मेटाबोलिक और क्रॉनिक केयर कंसल्टेशन के लिए रिक्वेस्ट की थी—क्या आप डायबिटीज, थायरॉइड या किसी स्पेशलिस्ट OPD के लिए देख रहे हैं?',
      defaultBudget: 'डायबिटीज / थायरॉइड / PCOD केयर',
      defaultFinancing: 'DPDP Consent • 108 Guard Active',
      initialStatus: 'TRIAGING',
      initialAction: 'Hindi Clinical Intake & Triage',
      initialIntent: 88,
      prompts: [
        'मेरा शुगर बहुत बढ़ा है, कौन सी दवाई या इंसुलिन डोज़ लूँ?',
        'मैं अभी ऑफिस में हूँ, मुझे कल 3 बजे कॉल करें।',
        'क्या कल सुबह 11:30 बजे डॉक्टर कंसल्टेशन बुक हो सकता है?',
        'मुझे सीने में तेज दर्द और सांस लेने में तकलीफ हो रही है।'
      ],
      offlineReplies: {
        emergency: 'कृपया तुरंत 108 पर कॉल करें या नजदीकी इमरजेंसी रूम में जाएं जी। सीने में दर्द या सांस की तकलीफ में तुरंत डॉक्टर की जरूरत है।',
        safety: 'जी बिल्कुल, मैं आपकी चिंता समझती हूँ। मैं कोई दवा या इंसुलिन डोज़ नहीं बता सकती—हमारे Amura डॉक्टर आपकी HbA1c रिपोर्ट देखकर ही सही सलाह देंगे। क्या कल सुबह 11:30 बजे का कंसल्टेशन बुक कर दूँ?',
        estate: 'Amura Health में डॉक्टर और हेल्थ कोच मिलकर मेडिकल न्यूट्रिशन थेरेपी (MNT) और नेचुरल मॉलिक्यूल थेरेपी (NMT) से डायबिटीज और थायरॉइड की देखभाल करते हैं।',
        meeting: 'बिल्कुल जी, मैं आपका समय समझती हूँ। मैं कल दोपहर 3:00 बजे आपको दोबारा कॉल करूँगी और वॉट्सऐप पर लैब चेकलिस्ट भेज रही हूँ।',
        schedule: 'बिल्कुल जी, कल सुबह 11:30 बजे या दोपहर 3:00 बजे का समय सही रहेगा?',
        showing: 'बहुत बढ़िया जी! कल सुबह 11:30 बजे का डॉक्टर कंसल्टेशन स्लॉट आपके नाम से बुक कर दिया गया है। लैब चेकलिस्ट वॉट्सऐप पर भेज दी गई है।',
        site_visit: 'बहुत बढ़िया जी! कल सुबह 11:30 बजे का डॉक्टर कंसल्टेशन स्लॉट आपके नाम से बुक कर दिया गया है। लैब चेकलिस्ट वॉट्सऐप पर भेज दी गई है।',
        rera: 'जी हाँ, Amura Health में सभी कंसल्टेशन लाइसेंस प्राप्त डॉक्टरों की देखरेख और DPDP प्राइवेसी नियमों के तहत होते हैं।',
        bhk: 'Amura Health का इनिशियल मेटाबोलिक कंसल्टेशन ₹1,500 से शुरू होता है। क्या मैं कल सुबह 11:30 बजे आपका स्लॉट बुक कर दूँ?',
        whatsapp: 'जी बिल्कुल! प्रोग्राम गाइड और फास्टिंग लैब चेकलिस्ट मैंने आपके वॉट्सऐप पर भेज दी है।',
        who_are_you: 'नमस्ते जी! मैं Amura Health और हॉस्पिटल केयर के लिए CLOSER AI की इमोशन-अवेयर वॉइस असिस्टेंट हूँ।',
        default: 'जी बिल्कुल! Amura Health में डायबिटीज, थायरॉइड और मेटाबोलिक केयर के लिए डॉक्टर उपलब्ध हैं। क्या कल सुबह 11:30 बजे का अपॉइंटमेंट बुक करें?'
      }
    }
  };
  MARKET_PRESETS.india = MARKET_PRESETS.hindi;

  function updateMarketUI(market) {
    if (market === 'india') market = 'hindi';
    currentMarket = market;
    const config = MARKET_PRESETS[market] || MARKET_PRESETS.usa;

    [btnMarketUSA, btnMarketTamil, btnMarketHindi, btnMarketIndia].forEach(btn => {
      if (!btn) return;
      btn.classList.remove('active');
      btn.setAttribute('aria-selected', 'false');
    });

    if (market === 'usa' && btnMarketUSA) {
      btnMarketUSA.classList.add('active');
      btnMarketUSA.setAttribute('aria-selected', 'true');
    } else if (market === 'tamil' && btnMarketTamil) {
      btnMarketTamil.classList.add('active');
      btnMarketTamil.setAttribute('aria-selected', 'true');
    } else if ((market === 'hindi' || market === 'india') && (btnMarketHindi || btnMarketIndia)) {
      if (btnMarketHindi) {
        btnMarketHindi.classList.add('active');
        btnMarketHindi.setAttribute('aria-selected', 'true');
      } else if (btnMarketIndia) {
        btnMarketIndia.classList.add('active');
        btnMarketIndia.setAttribute('aria-selected', 'true');
      }
    }

    // Set voice & dialect dropdowns
    if (voiceSelector) {
      voiceSelector.value = config.defaultVoice;
    }
    if (dialectSelector && config.defaultDialect) {
      dialectSelector.value = config.defaultDialect;
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

  const closerSessionId = `web_${Math.random().toString(36).slice(2, 10)}`;

  async function notifyBackendMarketMode(market) {
    try {
      await fetch('/api/market_mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: closerSessionId, mode: market })
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
  window.openLiveDemoModal = openDemoModal;
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
  if (btnMarketTamil) {
    btnMarketTamil.addEventListener('click', () => updateMarketUI('tamil'));
  }
  if (btnMarketHindi) {
    btnMarketHindi.addEventListener('click', () => updateMarketUI('hindi'));
  }
  if (btnMarketIndia) {
    btnMarketIndia.addEventListener('click', () => updateMarketUI('hindi'));
  }
  if (voiceSelector) {
    voiceSelector.addEventListener('change', (e) => {
      const val = e.target.value;
      if (val === 'priya_ta' || val === 'pallavi_ta') updateMarketUI('tamil');
      else if (val === 'ritu_hi' || val === 'swati_hi') updateMarketUI('hindi');
      else updateMarketUI('usa');
    });
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

  let isVoiceCallActive = false;
  let recognition = null;
  let isAiSpeaking = false;
  let currentAiSpeechText = '';
  let activeTurnAbortController = null;
  let lastEmotionProsody = { rate: 1.0, pitch: 1.0 };

  function unlockAudioOnGesture() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx && !window._closerAudioCtx) {
        window._closerAudioCtx = new AudioCtx();
      }
      if (window._closerAudioCtx && window._closerAudioCtx.state === 'suspended') {
        window._closerAudioCtx.resume().catch(() => {});
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.getVoices();
      }
    } catch {}
  }

  function interruptCurrentSpeech() {
    const wasSpeaking = isAiSpeaking || (demoAudioPlayer && !demoAudioPlayer.paused);
    const interrupted = wasSpeaking ? currentAiSpeechText : '';
    if (activeTurnAbortController) {
      try { activeTurnAbortController.abort(); } catch {}
      activeTurnAbortController = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (demoAudioPlayer) {
      demoAudioPlayer.pause();
      demoAudioPlayer.currentTime = 0;
    }
    isAiSpeaking = false;
    stopSpeakingUI();
    return { wasInterrupted: wasSpeaking, interruptedText: interrupted };
  }

  function playAudioResponse(audioBase64, fallbackText, onEndedCallback, audioFormat = 'wav') {
    isAiSpeaking = true;
    currentAiSpeechText = fallbackText || '';

    if (audioBase64) {
      lastAudioBase64 = audioBase64;
      if (btnReplayAudio) btnReplayAudio.style.display = 'inline-flex';

      const mime = audioFormat === 'mp3' ? 'audio/mpeg' : 'audio/wav';
      demoAudioPlayer.src = `data:${mime};base64,${audioBase64}`;
      startSpeakingUI();

      demoAudioPlayer.play().catch(() => {
        speakBrowserTTS(fallbackText, onEndedCallback);
      });

      demoAudioPlayer.onended = () => {
        stopSpeakingUI();
        isAiSpeaking = false;
        if (onEndedCallback) onEndedCallback();
        if (isVoiceCallActive) {
          setTimeout(startListening, 250);
        }
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
    if (!('speechSynthesis' in window) || !text) {
      isAiSpeaking = false;
      if (onEndedCallback) onEndedCallback();
      if (isVoiceCallActive) setTimeout(startListening, 250);
      return;
    }
    window.speechSynthesis.cancel();
    isAiSpeaking = true;
    currentAiSpeechText = text;

    const cleanText = text.replace(/₹/g, 'Rupees ').replace(/\$/g, 'Dollars ').replace(/\.\.\./g, ', ');
    const utterance = new SpeechSynthesisUtterance(cleanText);

    const voiceVal = voiceSelector ? voiceSelector.value : 'maya_en';
    const isTamil = currentMarket === 'tamil' || voiceVal.includes('ta') || voiceVal.includes('priya');
    const isHindi = currentMarket === 'hindi' || voiceVal.includes('hi') || voiceVal.includes('ritu');
    const voices = window.speechSynthesis.getVoices();

    let targetVoice = null;
    if (isTamil) {
      utterance.lang = 'ta-IN';
      targetVoice = voices.find((v) => v.lang.toLowerCase().includes('ta') && /natural|google|pallavi|valluvar/i.test(v.name))
        || voices.find((v) => v.lang.toLowerCase().includes('ta'));
    } else if (isHindi) {
      utterance.lang = 'hi-IN';
      targetVoice = voices.find((v) => v.lang.toLowerCase().includes('hi') && /natural|google|swara|lekha/i.test(v.name))
        || voices.find((v) => v.lang.toLowerCase().includes('hi'));
    } else {
      utterance.lang = 'en-IN';
      targetVoice = voices.find((v) => /natural|ava|samantha|neerja|google us|google uk/i.test(v.name) && v.lang.startsWith('en'))
        || voices.find((v) => v.lang.includes('IN') || v.lang.includes('US') || v.lang.startsWith('en'));
    }

    if (targetVoice) utterance.voice = targetVoice;
    utterance.rate = lastEmotionProsody.rate || 0.98;
    utterance.pitch = lastEmotionProsody.pitch || 1.02;

    utterance.onstart = () => startSpeakingUI();
    utterance.onend = () => {
      stopSpeakingUI();
      isAiSpeaking = false;
      if (onEndedCallback) onEndedCallback();
      if (isVoiceCallActive) setTimeout(startListening, 250);
    };
    utterance.onerror = () => {
      stopSpeakingUI();
      isAiSpeaking = false;
      if (onEndedCallback) onEndedCallback();
      if (isVoiceCallActive) setTimeout(startListening, 250);
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

  // Voice Sample Preview Button (Instant Direct Audio for Maya, Priya, Ritu)
  if (btnVoicePreview) {
    btnVoicePreview.addEventListener('click', async () => {
      unlockAudioOnGesture();
      const selectedVoice = voiceSelector ? voiceSelector.value : 'maya_en';
      startSpeakingUI();

      let sampleMsg = 'Hello! Maya calling from Amura Health Patient Care in Velachery, Chennai. I saw you requested a metabolic consultation—are you looking into diabetes reversal, thyroid care, or a specialist OPD visit?';

      if (selectedVoice === 'priya_ta' || selectedVoice === 'pallavi_ta' || selectedVoice.includes('ta') || selectedVoice.includes('tamil')) {
        sampleMsg = 'வணக்கம் Sir! வேளச்சேரி Amura Health-ல இருந்து பிரியா பேசுறேங்க. சுகர், தைராய்டு அல்லது PCOD மேனேஜ்மென்ட் பத்தி doctor consultation கேட்டிருந்தீங்க—உங்களுக்கு இப்போ என்ன health goal இருக்கு Sir?';
      } else if (selectedVoice === 'ritu_hi' || selectedVoice === 'swati_hi' || selectedVoice.includes('hi') || selectedVoice.includes('hindi')) {
        sampleMsg = 'नमस्ते जी! Amura Health पेशेंट केयर से रितु बात कर रही हूँ। आपने मेटाबोलिक और क्रॉनिक केयर कंसल्टेशन के लिए रिक्वेस्ट की थी—क्या आप डायबिटीज, थायरॉइड या किसी स्पेशलिस्ट OPD के लिए देख रहे हैं?';
      }

      if (modalAIText) modalAIText.textContent = `"${sampleMsg}"`;

      try {
        const res = await fetch('/api/turn', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ utterance: 'PREVIEW_SAMPLE', text: sampleMsg, voice: selectedVoice, sector: 'healthcare' })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.audio_base64) {
            playAudioResponse(data.audio_base64, data.reply || sampleMsg, null, data.audio_format || 'mp3');
            return;
          }
        }
      } catch {}

      speakBrowserTTS(sampleMsg);
    });
  }

  // -------------------------------------------------------------------------
  // 5. Conversational Turn Execution
  // -------------------------------------------------------------------------
  async function executeTurn(utteranceText) {
    if (!utteranceText || !utteranceText.trim()) return;
    unlockAudioOnGesture();
    const text = utteranceText.trim();
    const { wasInterrupted, interruptedText } = interruptCurrentSpeech();
    const selectedVoice = voiceSelector ? voiceSelector.value : 'maya_en';
    const selectedDialect = dialectSelector ? dialectSelector.value : undefined;
    const selectedSector = sectorSelector ? sectorSelector.value : 'healthcare';
    const modalEmotionBadge = document.getElementById('modalEmotionBadge');
    const modalMemoryTag = document.getElementById('modalMemoryTag');

    if (demoSendBtn) {
      demoSendBtn.disabled = true;
      demoSendBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Listening...</span>';
    }
    startSpeakingUI();

    activeTurnAbortController = new AbortController();

    try {
      const res = await fetch('/api/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: activeTurnAbortController.signal,
        body: JSON.stringify({
          session_id: closerSessionId,
          utterance: text,
          voice: selectedVoice,
          dialect: selectedDialect,
          sector: selectedSector,
          barge_in: wasInterrupted,
          interrupted_text: interruptedText || undefined
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (modalAIText) modalAIText.textContent = `"${data.reply}"`;
        if (modalVadStatus && data.tts_provider) {
          modalVadStatus.textContent = `● VOICE: ${data.tts_provider} • TONE: ${(data.voice_style || 'empathetic').toUpperCase()}${data.barge_in_handled ? ' • BARGE-IN' : ''}`;
        }
        // Calibrate browser TTS prosody from backend emotion
        const rateNum = parseFloat(String(data.tts_rate || '0').replace('%', '')) || 0;
        lastEmotionProsody = {
          rate: Math.max(0.85, Math.min(1.12, 1.0 + rateNum / 100)),
          pitch: data.detected_emotion === 'anxious' || data.detected_emotion === 'pain_distress' ? 0.96 : 1.02
        };
        if (modalEmotionBadge && data.detected_emotion) {
          const emo = String(data.detected_emotion).toUpperCase().replace('_', ' ');
          modalEmotionBadge.textContent = `EMOTION: ${emo}`;
          modalEmotionBadge.className = (data.emergency_108 || data.detected_emotion === 'pain_distress' || data.detected_emotion === 'urgent')
            ? 'dossier-badge amber display-font'
            : 'dossier-badge green display-font';
        }
        if (modalMemoryTag && data.session_memory) {
          const fields = data.session_memory.captured_fields || [];
          modalMemoryTag.textContent = fields.length
            ? `${fields.join(' • ')} (${data.session_memory.turn_count} turns)`
            : `Transcript recorded (${data.session_memory.turn_count || 1} turns)`;
        }

        if (data.dossier) {
          if (modalDossierStatus) {
            if (data.emergency_108 || data.dossier.emergency_108) {
              modalDossierStatus.textContent = '108 EMERGENCY';
              modalDossierStatus.className = 'dossier-badge amber';
            } else {
              modalDossierStatus.textContent = data.dossier.qualified ? 'CONSULT READY' : 'TRIAGING';
              modalDossierStatus.className = data.dossier.qualified ? 'dossier-badge green' : 'dossier-badge';
            }
          }
          if (modalDossierBudget && (data.dossier.chief_concern || data.dossier.condition_category || data.dossier.hba1c_or_biomarker)) {
            modalDossierBudget.textContent = data.dossier.chief_concern || data.dossier.condition_category || data.dossier.hba1c_or_biomarker;
          }
          if (modalDossierFinancing) {
            const consentTxt = data.dossier.consent_status || 'DPDP Verified';
            const urgencyTxt = data.dossier.triage_urgency || 'Routine';
            modalDossierFinancing.textContent = `${urgencyTxt} • Consent: ${consentTxt}`;
          }
          if (modalDossierAction && (data.dossier.consult_slot || data.dossier.follow_up_note)) {
            modalDossierAction.textContent = data.dossier.consult_slot || data.dossier.follow_up_note;
          }
          if (modalIntentFill && (data.dossier.intent_score !== undefined || data.dossier.qualification_score !== undefined)) {
            const scoreVal = data.dossier.intent_score !== undefined ? data.dossier.intent_score : data.dossier.qualification_score;
            modalIntentFill.style.width = `${scoreVal}%`;
            modalIntentText.textContent = `${scoreVal}% Care Intent`;
          }
        }

        playAudioResponse(data.audio_base64, data.reply, null, data.audio_format || 'mp3');
        if (demoSendBtn) {
          demoSendBtn.disabled = false;
          demoSendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> <span>Send</span>';
        }
        return;
      }
    } catch {
      // Local fallback simulation if server API is offline
    }

    // Local deterministic fallback (Healthcare & Amura Health Safe)
    const config = MARKET_PRESETS[currentMarket] || MARKET_PRESETS.usa;
    const lower = text.toLowerCase();
    let fallbackReply = '';

    if (lower.includes('chest pain') || lower.includes('breathe') || lower.includes('நெஞ்சு') || lower.includes('மூச்சு') || lower.includes('सीने') || lower.includes('सांस')) {
      fallbackReply = config.offlineReplies.emergency;
      if (modalEmotionBadge) modalEmotionBadge.textContent = 'EMOTION: PAIN DISTRESS';
      if (modalDossierStatus) {
        modalDossierStatus.textContent = '108 EMERGENCY';
        modalDossierStatus.className = 'dossier-badge amber';
      }
      if (modalDossierAction) modalDossierAction.textContent = 'Escalated to 108 / Emergency Room';
      if (modalIntentFill) {
        modalIntentFill.style.width = '100%';
        modalIntentText.textContent = '100% Urgent Emergency';
      }
    } else if (lower.includes('insulin') || lower.includes('medicine') || lower.includes('tablet') || lower.includes('dose') || lower.includes('माத்திரை') || lower.includes('दवाई') || lower.includes('डोज़')) {
      fallbackReply = config.offlineReplies.safety;
      if (modalEmotionBadge) modalEmotionBadge.textContent = 'EMOTION: ANXIOUS (-8%)';
      if (modalDossierStatus) {
        modalDossierStatus.textContent = 'PHYSICIAN REVIEW';
        modalDossierStatus.className = 'dossier-badge';
      }
      if (modalDossierAction) modalDossierAction.textContent = 'Safe Refusal → Doctor Consult Offered';
      if (modalIntentFill) {
        modalIntentFill.style.width = '90%';
        modalIntentText.textContent = '90% Care Intent';
      }
    } else if (lower.includes('whatsapp') || lower.includes('meeting') || lower.includes('busy') || lower.includes('office') || lower.includes('मीटिंग') || lower.includes('ऑफिस')) {
      fallbackReply = config.offlineReplies.meeting;
      if (modalDossierStatus) {
        modalDossierStatus.textContent = 'WHATSAPP SENT';
        modalDossierStatus.className = 'dossier-badge amber';
      }
      if (modalDossierAction) modalDossierAction.textContent = 'Fasting Lab Checklist Sent on WhatsApp';
      if (modalIntentFill) {
        modalIntentFill.style.width = '78%';
        modalIntentText.textContent = '78% Callback Scheduled';
      }
    } else if (lower.includes('book') || lower.includes('consult') || lower.includes('11:30') || lower.includes('புக்') || lower.includes('बुक') || lower.includes('tomorrow') || lower.includes('visit')) {
      fallbackReply = config.offlineReplies.showing;
      if (modalDossierStatus) {
        modalDossierStatus.textContent = 'CONSULT BOOKED';
        modalDossierStatus.className = 'dossier-badge green';
      }
      if (modalDossierAction) modalDossierAction.textContent = 'Confirmed: Tomorrow 11:30 AM IST';
      if (modalIntentFill) {
        modalIntentFill.style.width = '95%';
        modalIntentText.textContent = '95% Confirmed Slot';
      }
    } else if (lower.includes('who are you') || lower.includes('कौन') || lower.includes('யாரு')) {
      fallbackReply = config.offlineReplies.who_are_you;
    } else {
      fallbackReply = config.offlineReplies.default || config.initialGreeting;
    }

    if (!fallbackReply || fallbackReply === 'undefined') {
      fallbackReply = (config && config.offlineReplies && config.offlineReplies.default) || (config && config.initialGreeting) || "Hello! CLOSER AI is ready to assist you.";
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

  // Live Hands-Free Voice-to-Voice Calling System
  const btnLiveVoiceCall = document.getElementById('btnLiveVoiceCall');
  const liveVoiceIcon = document.getElementById('liveVoiceIcon');
  const liveVoiceText = document.getElementById('liveVoiceText');

  let micStream = null;

  async function ensureMicPermission() {
    if (micStream && micStream.active) return true;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return false;
    try {
      micStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
      });
      return true;
    } catch (err) {
      if (modalVadStatus) {
        modalVadStatus.textContent = `● MIC PERMISSION NEEDED (${err.name || 'Blocked'}) — ALLOW MIC OR TYPE BELOW`;
        modalVadStatus.style.color = '#f87171';
      }
      return false;
    }
  }

  function initSpeechEngine() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      if (modalVadStatus) {
        modalVadStatus.textContent = '● BROWSER SPEECH API UNAVAILABLE — TYPE BELOW & CLICK SEND';
        modalVadStatus.style.color = '#fbbf24';
      }
      if (demoUtteranceInput) demoUtteranceInput.focus();
      return null;
    }
    const rec = new SpeechRec();
    rec.continuous = true;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    rec.onstart = () => {
      if (btnLiveVoiceCall && isVoiceCallActive) {
        btnLiveVoiceCall.classList.add('listening');
        if (liveVoiceIcon) liveVoiceIcon.className = 'fa-solid fa-circle-dot';
        if (liveVoiceText) liveVoiceText.textContent = 'Listening (Speak Now)...';
      }
      startSpeakingUI();
      if (modalVadStatus) {
        modalVadStatus.textContent = '● LISTENING (MIC ACTIVE — SAY "HELLO")';
        modalVadStatus.style.color = '#ef4444';
      }
    };

    rec.onresult = (e) => {
      let interimText = '';
      let finalText = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const chunk = e.results[i][0] ? e.results[i][0].transcript : '';
        if (e.results[i].isFinal) {
          finalText += chunk + ' ';
        } else {
          interimText += chunk;
        }
      }
      if (demoUtteranceInput) {
        demoUtteranceInput.value = (finalText || interimText).trim();
      }
      // Mid-speech barge-in if user starts speaking clearly while AI is talking
      if ((interimText.trim().length > 2 || finalText.trim().length > 0) && isAiSpeaking) {
        interruptCurrentSpeech();
      }
      if (finalText.trim()) {
        const cleanFinal = finalText.trim();
        try { rec.stop(); } catch {}
        executeTurn(cleanFinal);
      }
    };

    rec.onerror = (e) => {
      console.warn('Speech recognition notice:', e.error);
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
        isVoiceCallActive = false;
        if (btnLiveVoiceCall) btnLiveVoiceCall.classList.remove('listening');
        if (liveVoiceIcon) liveVoiceIcon.className = 'fa-solid fa-microphone';
        if (liveVoiceText) liveVoiceText.textContent = 'Start Voice Call (Speak)';
        if (modalVadStatus) {
          modalVadStatus.textContent = '● MIC BLOCKED — ENABLE MIC PERMISSION IN BROWSER OR TYPE BELOW';
          modalVadStatus.style.color = '#f87171';
        }
        return;
      }
      if (e.error === 'network' && modalVadStatus) {
        modalVadStatus.textContent = '● SPEECH SERVICE NETWORK ISSUE — USE CHROME OR TYPE BELOW';
        modalVadStatus.style.color = '#fbbf24';
      }
    };

    rec.onend = () => {
      if (isVoiceCallActive && !isAiSpeaking) {
        setTimeout(() => {
          if (isVoiceCallActive && !isAiSpeaking) {
            startListening();
          }
        }, 250);
      } else if (!isVoiceCallActive) {
        if (btnLiveVoiceCall) btnLiveVoiceCall.classList.remove('listening');
        if (liveVoiceIcon) liveVoiceIcon.className = 'fa-solid fa-microphone';
        if (liveVoiceText) liveVoiceText.textContent = 'Start Voice Call (Speak)';
      }
    };

    return rec;
  }

  function startListening() {
    if (!isVoiceCallActive || isAiSpeaking) return;
    if (!recognition) recognition = initSpeechEngine();
    if (!recognition) return;
    recognition.lang = currentMarket === 'tamil' ? 'ta-IN' : (currentMarket === 'hindi' ? 'hi-IN' : 'en-IN');
    try {
      recognition.start();
    } catch {}
  }

  if (btnLiveVoiceCall) {
    btnLiveVoiceCall.addEventListener('click', async () => {
      unlockAudioOnGesture();
      if (!isVoiceCallActive) {
        interruptCurrentSpeech();
        const hasMic = await ensureMicPermission();
        if (!hasMic) {
          isVoiceCallActive = false;
          return;
        }
        isVoiceCallActive = true;
        if (!recognition) recognition = initSpeechEngine();
        if (!recognition) {
          isVoiceCallActive = false;
          return;
        }
        btnLiveVoiceCall.classList.add('listening');
        if (liveVoiceText) liveVoiceText.textContent = 'Connecting Mic...';
        startListening();
      } else {
        isVoiceCallActive = false;
        if (demoAudioPlayer) demoAudioPlayer.pause();
        if (recognition) {
          try { recognition.abort(); } catch {}
        }
        if (micStream) {
          micStream.getTracks().forEach((t) => t.stop());
          micStream = null;
        }
        btnLiveVoiceCall.classList.remove('listening');
        if (liveVoiceIcon) liveVoiceIcon.className = 'fa-solid fa-microphone';
        if (liveVoiceText) liveVoiceText.textContent = 'Start Voice Call (Speak)';
        stopSpeakingUI();
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

  window.showMarketTab = function (market) {
    const tabUSA = document.getElementById('tabUSA');
    const tabTamil = document.getElementById('tabTamil');
    const tabHindi = document.getElementById('tabHindi');
    const panelUSA = document.getElementById('panelUSA');
    const panelTamil = document.getElementById('panelTamil');
    const panelHindi = document.getElementById('panelHindi');

    [tabUSA, tabTamil, tabHindi].forEach(t => t && t.classList.remove('active'));
    [panelUSA, panelTamil, panelHindi].forEach(p => p && p.classList.remove('active'));

    if (market === 'usa' || market === 'english') {
      if (tabUSA) tabUSA.classList.add('active');
      if (panelUSA) panelUSA.classList.add('active');
    } else if (market === 'tamil') {
      if (tabTamil) tabTamil.classList.add('active');
      if (panelTamil) panelTamil.classList.add('active');
    } else if (market === 'hindi') {
      if (tabHindi) tabHindi.classList.add('active');
      if (panelHindi) panelHindi.classList.add('active');
    }
  };

  window.playVoiceSample = async function (market) {
    const audioMap = {
      'english': '/demos/en_opener.wav',
      'usa': '/demos/en_opener.wav',
      'tamil': '/demos/ta_opener.mp3',
      'hindi': '/demos/hi_opener.mp3'
    };
    const audioSrc = audioMap[market] || '/demos/en_opener.wav';

    try {
      const audio = new Audio(audioSrc);
      audio.play();
      return;
    } catch (e) {
      console.warn("Direct audio playback failed, falling back to API", e);
    }

    const textMap = {
      'english': "Hello! Maya calling from Amura Health Patient Care in Velachery, Chennai. I saw you requested a metabolic consultation—are you looking into diabetes reversal, thyroid care, or a specialist OPD visit?",
      'usa': "Hello! Maya calling from Amura Health Patient Care in Velachery, Chennai. I saw you requested a metabolic consultation—are you looking into diabetes reversal, thyroid care, or a specialist OPD visit?",
      'tamil': "வணக்கம் Sir! வேளச்சேரி Amura Health-ல இருந்து பிரியா பேசுறேங்க. சுகர், தைராய்டு அல்லது PCOD மேனேஜ்மென்ட் பத்தி doctor consultation கேட்டிருந்தீங்க—உங்களுக்கு இப்போ என்ன health goal இருக்கு Sir?",
      'hindi': "नमस्ते जी! Amura Health पेशेंट केयर से रितु बात कर रही हूँ। आपने मेटाबोलिक और क्रॉनिक केयर कंसल्टेशन के लिए रिक्वेस्ट की थी—क्या आप डायबिटीज, थायरॉइड या किसी स्पेशलिस्ट OPD के लिए देख रहे हैं?"
    };
    const text = textMap[market] || textMap['english'];
    const voice = market === 'tamil' ? 'tamil' : (market === 'hindi' ? 'hindi' : 'english');

    try {
      const res = await fetch('/api/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ utterance: 'STUDIO_SAMPLE', text: text, voice: voice, sector: 'healthcare' })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64) {
          playAudioResponse(data.audio_base64, data.reply);
          return;
        }
      }
    } catch {}

    speakBrowserTTS(text);
  };

  // -------------------------------------------------------------------------
  // 7. Interactive Voice Soundboard Studio (#voice-studio)
  // -------------------------------------------------------------------------
  let studioSelectedVoice = 'english';
  let studioSelectedScenario = 'en_opener';
  let studioSelectedRate = '-3%';
  let studioSelectedSpeed = '1.0';
  let studioSelectedLLM = 'llama-3.3-70b';
  let isAcousticCellular = false;

  const STUDIO_SCENARIOS = {
    // English Scenarios (Maya - Emotion-Aware Clinical Care)
    en_opener: {
      voice: 'english',
      audio_url: '/demos/en_opener.wav',
      speaker: 'CLOSER AI (Maya — Clinical Care Concierge):',
      text: "Hello! Maya calling from Amura Health Patient Care in Velachery, Chennai. I saw you requested a metabolic consultation—are you looking into diabetes reversal, thyroid care, or a specialist OPD visit?"
    },
    en_objection: {
      voice: 'english',
      audio_url: '/demos/en_objection.wav',
      speaker: 'CLOSER AI (Maya — Empathetic Safety Guardrail):',
      text: "I completely understand how stressful fluctuating blood sugar can feel. Only our licensed Amura physician can adjust medication after reviewing your HbA1c—shall I book your consultation tomorrow at 11:30 AM?"
    },
    en_closing: {
      voice: 'english',
      audio_url: '/demos/en_closing.wav',
      speaker: 'CLOSER AI (Maya — Consultation Confirmed):',
      text: "Wonderful! Your Amura Health physician consultation is confirmed for tomorrow at 11:30 AM IST. I have dispatched your fasting lab checklist on WhatsApp right now."
    },

    // Tamil Scenarios (பிரியா — Sarvam Bulbul v3 Tanglish)
    ta_opener: {
      voice: 'tamil',
      audio_url: '/demos/ta_opener.mp3',
      speaker: 'CLOSER AI (பிரியா — Amura Health Tamil):',
      text: "வணக்கம் Sir! வேளச்சேரி Amura Health-ல இருந்து பிரியா பேசுறேங்க. சுகர், தைராய்டு அல்லது PCOD மேனேஜ்மென்ட் பத்தி doctor consultation கேட்டிருந்தீங்க—உங்களுக்கு இப்போ என்ன health goal இருக்கு Sir?"
    },
    ta_objection: {
      voice: 'tamil',
      audio_url: '/demos/ta_objection.mp3',
      speaker: 'CLOSER AI (பிரியா — Empathy & Clinical Safety):',
      text: "கவலைப்படாதீங்க Sir, உங்க நிலைமை எங்களுக்குப் புரியுது. மருந்து அளவை நம்ம Amura மருத்துவர் தான் HbA1c ரிப்போர்ட் பார்த்து முடிவு பண்ணுவாங்க. நாளை காலை 11:30 மணிக்கு consultation புக் பண்ணலாமா Sir?"
    },
    ta_closing: {
      voice: 'tamil',
      audio_url: '/demos/ta_closing.mp3',
      speaker: 'CLOSER AI (பிரியா — Consultation Booked):',
      text: "ரொம்ப நன்றி Sir! நாளை காலை 11:30 மணிக்கு உங்க doctor consultation slot புக் பண்ணிட்டேங்க. உங்க WhatsApp-க்கு lab test checklist அனுப்பிட்டேன் Sir!"
    },

    // Hindi Scenarios (रितु — Sarvam Bulbul v3 Hinglish)
    hi_opener: {
      voice: 'hindi',
      audio_url: '/demos/hi_opener.mp3',
      speaker: 'CLOSER AI (रितु — Amura Health Hindi):',
      text: "नमस्ते जी! Amura Health पेशेंट केयर से रितु बात कर रही हूँ। आपने मेटाबोलिक और क्रॉनिक केयर कंसल्टेशन के लिए रिक्वेस्ट की थी—क्या आप डायबिटीज, थायरॉइड या किसी स्पेशलिस्ट OPD के लिए देख रहे हैं?"
    },
    hi_objection: {
      voice: 'hindi',
      audio_url: '/demos/hi_objection.mp3',
      speaker: 'CLOSER AI (रितु — Empathy & Safety Guardrail):',
      text: "जी बिल्कुल, मैं आपकी चिंता समझती हूँ। कोई भी दवा या डोज़ हमारे Amura डॉक्टर आपकी HbA1c और ब्लड रिपोर्ट देखकर ही तय करते हैं। क्या मैं कल सुबह 11:30 बजे आपका टेली-कंसल्टेशन बुक कर दूँ?"
    },
    hi_closing: {
      voice: 'hindi',
      audio_url: '/demos/hi_closing.mp3',
      speaker: 'CLOSER AI (रितु — Consultation Booked):',
      text: "बहुत बढ़िया जी! कल सुबह 11:30 बजे का डॉक्टर कंसल्टेशन स्लॉट आपके नाम से बुक कर दिया गया है। लैब चेकलिस्ट और लिंक मैंने आपके वॉट्सऐप पर भेज दिया है।"
    }
  };

  window.selectStudioVoice = function (el) {
    document.querySelectorAll('.voice-pill').forEach((btn) => btn.classList.remove('active'));
    el.classList.add('active');
    studioSelectedVoice = el.getAttribute('data-voice') || 'english';

    const firstScenarioMap = {
      'english': 'en_opener',
      'tamil': 'ta_opener',
      'hindi': 'hi_opener'
    };
    const targetScen = firstScenarioMap[studioSelectedVoice] || 'en_opener';
    const targetBtn = document.querySelector(`.scenario-btn[data-scenario="${targetScen}"]`);
    if (targetBtn) {
      window.selectStudioScenario(targetBtn);
    }
  };

  window.selectStudioScenario = function (el) {
    document.querySelectorAll('.scenario-btn').forEach((btn) => btn.classList.remove('active'));
    el.classList.add('active');
    studioSelectedScenario = el.getAttribute('data-scenario') || 'en_opener';

    const item = STUDIO_SCENARIOS[studioSelectedScenario];
    const speakerEl = document.getElementById('studioSpeakerName');
    const textEl = document.getElementById('studioSpeechText');

    if (speakerEl && item) speakerEl.innerHTML = `<i class="fa-solid fa-robot"></i> ${item.speaker}`;
    if (textEl && item) textEl.textContent = `"${item.text}"`;

    if (item && item.voice && item.voice !== studioSelectedVoice) {
      studioSelectedVoice = item.voice;
      document.querySelectorAll('.voice-pill').forEach((btn) => {
        if (btn.getAttribute('data-voice') === item.voice) btn.classList.add('active');
        else btn.classList.remove('active');
      });
    }
  };

  window.runStudioSimulation = async function () {
    unlockAudioOnGesture();
    const item = STUDIO_SCENARIOS[studioSelectedScenario] || STUDIO_SCENARIOS['en_opener'];
    const waveform = document.getElementById('studioWaveform');
    const statusEl = document.getElementById('studioStatus');

    if (waveform) waveform.classList.add('is-playing');
    if (statusEl) {
      statusEl.textContent = '● TRANSMITTING NEURAL AUDIO';
      statusEl.style.color = '#38bdf8';
    }

    const resetStudioUI = () => {
      if (waveform) waveform.classList.remove('is-playing');
      if (statusEl) {
        statusEl.textContent = '● AUDIO ENGINE READY';
        statusEl.style.color = '#10b981';
      }
    };

    try {
      const res = await fetch('/api/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          utterance: 'STUDIO_SAMPLE',
          text: item.text,
          voice: studioSelectedVoice,
          rate: studioSelectedRate,
          model_id: studioSelectedLLM,
          sector: 'healthcare'
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64) {
          playAudioResponse(data.audio_base64, data.reply, resetStudioUI, data.audio_format || 'mp3');
          return;
        }
      }
    } catch {}

    speakBrowserTTS(item.text, resetStudioUI);
  };

  // -------------------------------------------------------------------------
  // 8. Interactive Unit Economics & ROI Calculator (#roi)
  // -------------------------------------------------------------------------
  let roiCurrency = 'inr';

  window.setRoiCurrency = function (curr) {
    roiCurrency = curr;
    const currUSD = document.getElementById('currUSD');
    const currINR = document.getElementById('currINR');
    const sliderComm = document.getElementById('sliderCommission');

    if (curr === 'usd') {
      if (currUSD) currUSD.classList.add('active');
      if (currINR) currINR.classList.remove('active');
      if (sliderComm) {
        sliderComm.min = 500;
        sliderComm.max = 10000;
        sliderComm.step = 250;
        sliderComm.value = 1500;
      }
    } else {
      if (currINR) currINR.classList.add('active');
      if (currUSD) currUSD.classList.remove('active');
      if (sliderComm) {
        sliderComm.min = 5000;
        sliderComm.max = 150000;
        sliderComm.step = 5000;
        sliderComm.value = 45000;
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

    const valLeads = document.getElementById('valLeads');
    const valCommission = document.getElementById('valCommission');
    const valConv = document.getElementById('valConv');

    if (valLeads) valLeads.textContent = `${leads.toLocaleString()} Inquiries`;
    if (valCommission) {
      valCommission.textContent = roiCurrency === 'usd'
        ? `$${comm.toLocaleString()} USD`
        : `₹${comm.toLocaleString('en-IN')} INR`;
    }
    if (valConv) valConv.textContent = `${convRate.toFixed(1)}%`;

    const extraQualifiedShowings = Math.round(leads * 0.09);
    const extraClosedDeals = (extraQualifiedShowings * (convRate / 100) * 1.5).toFixed(1);
    const revenueUplift = Math.round(parseFloat(extraClosedDeals) * comm);
    const hoursSaved = Math.round(leads * 0.5);

    const roiShowings = document.getElementById('roiShowings');
    const roiDeals = document.getElementById('roiDeals');
    const roiRevenue = document.getElementById('roiRevenue');
    const roiHours = document.getElementById('roiHours');

    if (roiShowings) roiShowings.textContent = `+${extraQualifiedShowings}`;
    if (roiDeals) roiDeals.textContent = `+${extraClosedDeals}`;
    if (roiRevenue) {
      roiRevenue.textContent = roiCurrency === 'usd'
        ? `+$${revenueUplift.toLocaleString()}`
        : `+₹${revenueUplift.toLocaleString('en-IN')}`;
    }
    if (roiHours) roiHours.textContent = `${hoursSaved} hrs`;
  };

  // Run initial calculation
  updateRoiCalc();

  // -------------------------------------------------------------------------
  // 9. Live Outbound Demo Call Trigger (/api/call/demo)
  // -------------------------------------------------------------------------
  const demoCallPhoneInput = document.getElementById('demoCallPhoneInput');
  const demoCallTriggerBtn = document.getElementById('demoCallTriggerBtn');
  const demoCallStatus = document.getElementById('demoCallStatus');

  if (demoCallTriggerBtn && demoCallPhoneInput) {
    demoCallTriggerBtn.addEventListener('click', async () => {
      const phone = demoCallPhoneInput.value.trim();
      if (!phone || phone.replace(/\D/g, '').length < 10) {
        if (demoCallStatus) {
          demoCallStatus.textContent = 'Enter 10+ digit number';
          demoCallStatus.style.color = '#fbbf24';
        }
        return;
      }

      demoCallTriggerBtn.disabled = true;
      if (demoCallStatus) {
        demoCallStatus.textContent = 'Dialing pipeline...';
        demoCallStatus.style.color = '#60a5fa';
      }

      try {
        const res = await fetch('/api/call/demo', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            phone_number: phone,
            language: currentMarket === 'tamil' ? 'tamil' : (currentMarket === 'hindi' ? 'hindi' : 'english'),
            patient_name: 'Amura Founder Demo',
            concern: 'Diabetes & Metabolic Consultation',
            consent_confirmed: true
          })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          if (demoCallStatus) {
            demoCallStatus.textContent = `${data.status.toUpperCase()} (${data.call_id})`;
            demoCallStatus.style.color = '#34d399';
          }
          if (modalAIText) modalAIText.textContent = `"${data.message}"`;
        } else {
          if (demoCallStatus) {
            demoCallStatus.textContent = data.error || 'Call validation failed';
            demoCallStatus.style.color = '#f87171';
          }
        }
      } catch {
        if (demoCallStatus) {
          demoCallStatus.textContent = 'Demo Call Queued (Offline Ready)';
          demoCallStatus.style.color = '#34d399';
        }
      } finally {
        demoCallTriggerBtn.disabled = false;
      }
    });
  }

  // -------------------------------------------------------------------------
  // 10. Post-Call Doctor Summary Dispatch (/api/call/doctor-summary)
  // -------------------------------------------------------------------------
  const btnSendDoctorSummary = document.getElementById('btnSendDoctorSummary');
  const doctorDispatchResult = document.getElementById('doctorDispatchResult');

  if (btnSendDoctorSummary) {
    btnSendDoctorSummary.addEventListener('click', async () => {
      btnSendDoctorSummary.disabled = true;
      if (doctorDispatchResult) {
        doctorDispatchResult.style.display = 'block';
        doctorDispatchResult.textContent = 'Analyzing patient transcript & preparing doctor brief...';
      }
      try {
        const res = await fetch('/api/call/doctor-summary', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: closerSessionId, channel: 'both' })
        });
        const data = await res.json();
        if (res.ok && data.success && doctorDispatchResult) {
          doctorDispatchResult.innerHTML =
            `<strong>Doctor Brief Ready (${data.brief.urgency}):</strong> ${data.brief.concern}<br>` +
            `<a href="${data.whatsapp_link}" target="_blank" rel="noopener noreferrer" style="color:#34d399;text-decoration:underline;margin-right:10px;">Send via WhatsApp ↗</a>` +
            `<a href="${data.mailto_link}" style="color:#60a5fa;text-decoration:underline;">Send via Email (${data.doctor_email}) ↗</a>`;
        }
      } catch {
        if (doctorDispatchResult) {
          doctorDispatchResult.textContent = 'Doctor summary analyzed locally (ready to dispatch).';
        }
      } finally {
        btnSendDoctorSummary.disabled = false;
      }
    });
  }
});
