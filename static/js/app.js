/* app.js – Interview Trainer Agent frontend */

const API = '';  // Same origin

// ── State ──────────────────────────────────────────────────────────────────
let currentSession = null;
let currentRole    = '';
let currentLevel   = '';
let currentSkills  = [];

// ── DOM helpers ────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const show = el => el.classList.remove('hidden');
const hide = el => el.classList.add('hidden');

// ── Tab switching ──────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const targetTab = btn.dataset.tab;
    const parent    = btn.closest('section') || btn.closest('main') || document;

    // Deactivate sibling buttons
    btn.parentElement.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Find all sibling tab-content panels — deactivate, then activate target
    const allContents = parent.querySelectorAll('.tab-content');
    allContents.forEach(tc => {
      tc.classList.remove('active');
      tc.style.display = 'none';
    });
    const target = $(`tab-${targetTab}`);
    if (target) { target.classList.add('active'); target.style.display = 'block'; }
  });
});

// Initialise tab visibility
document.querySelectorAll('.tab-content').forEach(tc => {
  if (!tc.classList.contains('active')) tc.style.display = 'none';
});

// ── File Upload ────────────────────────────────────────────────────────────
const uploadZone = $('upload-zone');
const fileInput  = $('file-input');
const fileNameEl = $('file-name');

uploadZone.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragover'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('dragover');
  if (e.dataTransfer.files[0]) { fileInput.files = e.dataTransfer.files; updateFileName(); }
});
fileInput.addEventListener('change', updateFileName);

function updateFileName() {
  if (fileInput.files[0]) {
    fileNameEl.textContent = '✅ ' + fileInput.files[0].name;
    show(fileNameEl);
  }
}

// ── Manual Profile Form ────────────────────────────────────────────────────
$('form-profile').addEventListener('submit', async e => {
  e.preventDefault();
  const form = e.target;
  const name        = $('name').value.trim();
  const role        = $('role').value;
  const level       = $('level').value;
  const skillsRaw   = $('skills').value.trim();
  const numTech     = parseInt($('num-tech').value) || 5;

  if (!name || !role) { alert('Please fill in Name and Role.'); return; }

  const skills = skillsRaw ? skillsRaw.split(',').map(s => s.trim()).filter(Boolean) : [];

  currentRole   = role;
  currentLevel  = level;
  currentSkills = skills;

  showLoading('Connecting to IBM Granite and generating your personalised questions...');

  try {
    const res = await fetch(`${API}/api/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name, role, experience_level: level, skills,
        num_technical: numTech, num_behavioral: 3,
      }),
    });
    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Unknown error');
    renderResults(data.data);
  } catch (err) {
    hideLoading();
    alert('Error: ' + err.message);
  }
});

// ── Resume Form ────────────────────────────────────────────────────────────
$('form-resume').addEventListener('submit', async e => {
  e.preventDefault();
  if (!fileInput.files[0]) { alert('Please select a resume file.'); return; }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('role', $('resume-role').value);
  formData.append('experience_level', $('resume-level').value);

  currentRole  = $('resume-role').value;
  currentLevel = $('resume-level').value;

  showLoading('Parsing your resume and generating personalised questions...');

  try {
    const res = await fetch(`${API}/api/session/resume`, {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Unknown error');
    renderResults(data.data);
  } catch (err) {
    hideLoading();
    alert('Error: ' + err.message);
  }
});

// ── Render Results ─────────────────────────────────────────────────────────
function renderResults(session) {
  currentSession = session;
  const profile  = session.profile || {};

  // Update subtitle
  $('results-title').textContent  = `Interview Prep – ${profile.name || 'Candidate'}`;
  $('results-subtitle').textContent =
    `${profile.experience_level || ''} • ${formatRole(profile.role || '')} • Session ${session.session_id || ''}`;

  // Technical questions
  renderQuestionList('tech-questions-list', session.technical_questions || [], 'tech');

  // Behavioral questions
  renderQuestionList('behav-questions-list', session.behavioral_questions || [], 'behav');

  // Strategy & Tips
  $('strategy-content').textContent = session.preparation_strategy || 'No strategy generated.';
  $('tips-content').textContent     = session.improvement_tips || 'No tips generated.';

  // Ensure first results tab is active
  document.querySelectorAll('#step-results .tab-btn').forEach((b, i) => {
    b.classList.toggle('active', i === 0);
  });
  document.querySelectorAll('#step-results .tab-content').forEach((tc, i) => {
    tc.classList.toggle('active', i === 0);
    tc.style.display = i === 0 ? 'block' : 'none';
  });

  hideLoading();
  hide($('step-profile'));
  show($('step-results'));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderQuestionList(containerId, questions, type) {
  const container = $(containerId);
  if (!questions.length) {
    container.innerHTML = '<p style="color:var(--muted);padding:20px 0">No questions generated.</p>';
    return;
  }
  container.innerHTML = questions.map((q, i) => {
    const badge = type === 'tech'
      ? `<span class="q-badge badge-tech">${q.topic || 'Technical'}</span>`
      : `<span class="q-badge badge-behav">${q.category || q.framework || 'Behavioral'}</span>`;
    const tip = q.tip ? `<div class="q-tip">💡 ${q.tip}</div>` : '';
    return `
      <div class="question-card">
        <div class="q-left">
          <div class="q-number">Q${i + 1} ${badge}</div>
          <div class="q-text">${escapeHtml(q.question)}</div>
          ${tip}
        </div>
        <button class="btn-answer" data-question="${escapeAttr(q.question)}">
          Get Answer
        </button>
      </div>`;
  }).join('');

  // Attach answer button listeners
  container.querySelectorAll('.btn-answer').forEach(btn => {
    btn.addEventListener('click', () => openAnswerModal(btn.dataset.question));
  });
}

// ── Model Answer Modal ─────────────────────────────────────────────────────
async function openAnswerModal(question) {
  $('modal-question').textContent = question;
  $('modal-answer').textContent   = '';
  hide($('modal-tips'));
  show($('modal-answer-loading'));
  show($('answer-modal'));

  try {
    const profile = currentSession?.profile || {};
    const res = await fetch(`${API}/api/model-answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        role:             profile.role || currentRole,
        experience_level: profile.experience_level?.split(' ')[0]?.toLowerCase() || currentLevel,
        skills:           profile.skills || currentSkills,
      }),
    });
    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Unknown error');

    hide($('modal-answer-loading'));
    $('modal-answer').textContent = data.data.model_answer || 'No answer generated.';

    if (data.data.tips && data.data.tips.length) {
      const tipsEl = $('modal-tips');
      tipsEl.innerHTML = '<strong>Related Tips:</strong>' +
        data.data.tips.map(t => `<div class="tip-item">${escapeHtml(t)}</div>`).join('');
      show(tipsEl);
    }
  } catch (err) {
    hide($('modal-answer-loading'));
    $('modal-answer').textContent = 'Error generating answer: ' + err.message;
  }
}

$('modal-close').addEventListener('click', closeModal);
$('modal-overlay').addEventListener('click', closeModal);
function closeModal() { hide($('answer-modal')); }

// ── New Session ────────────────────────────────────────────────────────────
$('btn-new-session').addEventListener('click', () => {
  hide($('step-results'));
  show($('step-profile'));
  currentSession = null;
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ── Loading helpers ────────────────────────────────────────────────────────
function showLoading(msg) {
  $('loading-text').textContent = msg || 'Loading...';
  hide($('step-profile'));
  hide($('step-results'));
  show($('loading'));
}
function hideLoading() { hide($('loading')); }

// ── Utility ────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function escapeAttr(str) { return String(str).replace(/"/g, '&quot;'); }
function formatRole(role) {
  return role.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
