/* ==========================================================================
   Harness Kit — Central JavaScript Module (js/main.js)
   ========================================================================== */

(function () {
  'use strict';

  let currentLang = 'vi';

  /**
   * Switch Language (VI / EN)
   * @param {string} lang - 'vi' or 'en'
   */
  window.switchLang = function (lang) {
    if (!lang) return;
    currentLang = lang;
    document.body.className = `lang-${lang}`;

    // Update Language Buttons
    const viBtn = document.getElementById('lang-vi-btn');
    const enBtn = document.getElementById('lang-en-btn');
    if (viBtn) viBtn.classList.toggle('active', lang === 'vi');
    if (enBtn) enBtn.classList.toggle('active', lang === 'en');

    // Update buttons in lang-toggle container if present (e.g. use-case.html)
    const toggleBtns = document.querySelectorAll('.lang-toggle button, [data-lang]');
    toggleBtns.forEach(btn => {
      const btnLang = btn.getAttribute('data-lang') || (btn.id && btn.id.includes('vi') ? 'vi' : 'en');
      btn.classList.toggle('active', btnLang === lang);
    });

    // Save Preference
    try {
      localStorage.setItem('harness-kit-lang', lang);
    } catch (e) {
      console.warn('LocalStorage unavailable for language preference.');
    }

    // Trigger page-specific translation updates if defined (e.g. index.html)
    if (typeof window.onLanguageChange === 'function') {
      window.onLanguageChange(lang);
    }
  };

  /**
   * Copy code block content to clipboard
   * @param {HTMLElement} btn - Clicked copy button
   */
  window.copyBlock = function (btn) {
    if (!btn) return;
    const wrap = btn.closest('.code-wrap, .code-block-wrap, .code-block, .clone-box');
    const target = wrap ? wrap.querySelector('pre, code') : null;
    const textToCopy = target ? target.textContent.trim() : '';

    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        const origText = btn.innerHTML;
        const isVi = currentLang === 'vi';
        btn.classList.add('copied');
        btn.innerHTML = isVi ? '✓ Đã chép' : '✓ Copied!';

        setTimeout(() => {
          btn.classList.remove('copied');
          btn.innerHTML = origText;
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy text: ', err);
      });
    }
  };

  /**
   * Copy specific text to clipboard directly
   * @param {string} text 
   * @param {HTMLElement} btn 
   */
  window.copyText = function (text, btn) {
    navigator.clipboard.writeText(text).then(() => {
      if (btn) {
        const origText = btn.innerHTML;
        const isVi = currentLang === 'vi';
        btn.classList.add('copied');
        btn.innerHTML = isVi ? '✓ Đã chép' : '✓ Copied!';
        setTimeout(() => {
          btn.classList.remove('copied');
          btn.innerHTML = origText;
        }, 2000);
      }
    });
  };

  /**
   * Initialize Language and DOM Event Listeners on Load
   */
  document.addEventListener('DOMContentLoaded', function () {
    // Restore Saved Language
    let savedLang = 'vi';
    try {
      savedLang = localStorage.getItem('harness-kit-lang') || 'vi';
    } catch (e) {}

    window.switchLang(savedLang === 'en' ? 'en' : 'vi');

    // Attach listener for data-lang buttons
    document.querySelectorAll('[data-lang]').forEach(btn => {
      btn.addEventListener('click', function () {
        const lang = this.getAttribute('data-lang');
        if (lang) window.switchLang(lang);
      });
    });
  });

})();
