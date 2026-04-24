/**
 * VotePath AI – Frontend Script
 * Vanilla JS, no dependencies.
 */

'use strict';

// ── Config ────────────────────────────────────────────────────
const API_BASE = '';          // same origin — empty string works for both local and Cloud Run
const ASK_ENDPOINT = `${API_BASE}/ask`;

// ── DOM refs ──────────────────────────────────────────────────
const form          = document.getElementById('questionForm');
const input         = document.getElementById('questionInput');
const submitBtn     = document.getElementById('submitBtn');
const loadingState  = document.getElementById('loadingState');
const errorState    = document.getElementById('errorState');
const errorMessage  = document.getElementById('errorMessage');
const responseCard  = document.getElementById('responseCard');
const askAnother    = document.getElementById('askAnother');
const askAnotherBtn = document.getElementById('askAnotherBtn');
const quickBtns     = document.querySelectorAll('.quick-btn');

// Response card elements
const categoryBadge  = document.getElementById('categoryBadge');
const cardTitle      = document.getElementById('cardTitle');
const overviewText   = document.getElementById('overviewText');
const stepsList      = document.getElementById('stepsList');
const stepsSection   = document.getElementById('stepsSection');
const documentsList  = document.getElementById('documentsList');
const documentsSection = document.getElementById('documentsSection');
const tipsList       = document.getElementById('tipsList');
const tipsSection    = document.getElementById('tipsSection');
const nextActionText = document.getElementById('nextActionText');
const nextActionSection = document.getElementById('nextActionSection');
const metaConfidence = document.getElementById('metaConfidence');
const metaSource     = document.getElementById('metaSource');
const metaCache      = document.getElementById('metaCache');
const metaReason     = document.getElementById('metaReason');

// ── Helpers ───────────────────────────────────────────────────

/** Show/hide utility */
function show(el) { el.classList.remove('hidden'); }
function hide(el) { el.classList.add('hidden'); }

/** Escape HTML to prevent XSS */
function esc(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

/** Format category slug → readable label */
function formatCategory(cat) {
  const map = {
    first_time_voter: '🌟 First-Time Voter',
    registration:     '📋 Registration',
    documents:        '🪪 Documents',
    correction:       '✏️ Correction',
    status_check:     '🔍 Status Check',
    polling_day:      '📍 Polling Day',
    timeline:         '📅 Timeline',
    faq:              '💬 FAQ',
  };
  return map[cat] || cat.replace(/_/g, ' ');
}

/** Confidence → colour class */
function confidenceClass(level) {
  return { high: '🟢', medium: '🟡', low: '🔴' }[level] || '⚪';
}

// ── State ─────────────────────────────────────────────────────
function setLoading(on) {
  if (on) {
    hide(responseCard);
    hide(errorState);
    hide(askAnother);
    show(loadingState);
    submitBtn.disabled = true;
    input.disabled = true;
  } else {
    hide(loadingState);
    submitBtn.disabled = false;
    input.disabled = false;
  }
}

function showError(msg) {
  errorMessage.textContent = msg || 'Something went wrong. Please try again.';
  document.title = 'VotePath AI – Election Process Assistant';
  show(errorState);
  hide(responseCard);
  hide(askAnother);
}

// ── Render response ───────────────────────────────────────────
function renderResponse(data) {
  // Badge + title
  categoryBadge.textContent = formatCategory(data.category);
  cardTitle.textContent = data.title || 'Election Guidance';

  // Overview
  overviewText.textContent = data.overview || '';

  // Steps
  if (data.steps && data.steps.length > 0) {
    stepsList.innerHTML = data.steps
      .map((s, i) => `<li><span class="step-num">${i + 1}</span><span>${esc(s)}</span></li>`)
      .join('');
    show(stepsSection);
  } else {
    hide(stepsSection);
  }

  // Documents
  if (data.documents && data.documents.length > 0) {
    documentsList.innerHTML = data.documents
      .map(d => `<li>${esc(d)}</li>`)
      .join('');
    show(documentsSection);
  } else {
    hide(documentsSection);
  }

  // Tips
  if (data.tips && data.tips.length > 0) {
    tipsList.innerHTML = data.tips
      .map(t => `<li>${esc(t)}</li>`)
      .join('');
    show(tipsSection);
  } else {
    hide(tipsSection);
  }

  // Next action
  if (data.next_action) {
    nextActionText.textContent = data.next_action;
    show(nextActionSection);
  } else {
    hide(nextActionSection);
  }

  // Metadata strip
  const conf = data.confidence || 'low';
  metaConfidence.textContent = `${confidenceClass(conf)} ${conf} confidence`;
  metaSource.textContent     = `📡 ${data.system_mode === 'sheets' ? 'Google Sheets' : 'Fallback data'}`;
  metaCache.textContent      = data.served_from_cache ? '⚡ cached' : '🔄 live';
  metaReason.textContent     = data.confidence_reason || '';

  // Show card
  show(responseCard);
  show(askAnother);

  // Update page title for accessibility and UX
  document.title = `VotePath AI — ${formatCategory(data.category)}`;

  // Smooth scroll to card
  responseCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── API call ──────────────────────────────────────────────────
async function askQuestion(question) {
  const q = question.trim();
  if (!q) {
    input.focus();
    return;
  }

  setLoading(true);

  try {
    const res = await fetch(ASK_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error (${res.status})`);
    }

    const data = await res.json();
    renderResponse(data);

  } catch (err) {
    console.error('VotePath API error:', err);
    if (err.name === 'TypeError') {
      // Network failure
      showError('Unable to reach the server. Please check your connection and try again.');
    } else {
      showError(err.message || 'Something went wrong. Please try again.');
    }
  } finally {
    setLoading(false);
  }
}

// ── Event listeners ───────────────────────────────────────────

// Form submit
form.addEventListener('submit', (e) => {
  e.preventDefault();
  askQuestion(input.value);
});

// Quick action buttons
quickBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const query = btn.dataset.query;
    input.value = query;
    askQuestion(query);
  });
});

// Ask another
askAnotherBtn.addEventListener('click', () => {
  hide(responseCard);
  hide(askAnother);
  hide(errorState);
  input.value = '';
  document.title = 'VotePath AI – Election Process Assistant';
  input.focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Allow Enter key in input (already handled by form submit, but guard anyway)
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    form.dispatchEvent(new Event('submit'));
  }
});

// ── Init ──────────────────────────────────────────────────────
input.focus();
