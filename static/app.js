'use strict';

// ─── DOG CATALOG ────────────────────────────────────────────────────────────
const DOG_CATALOG = [
  { name: 'Biscuit',   emoji: '🦮', breed: 'Golden Retriever',   age_years: 3.0, size: 'large',  energy_level: 'medium', temperament: 'friendly',  training_level: 'high',   special_needs: false, hypoallergenic: false, kid_compatibility: 'high',   other_pets_compatibility: 'high',   shelter_notes: 'Good with people.' },
  { name: 'Luna',      emoji: '🐕', breed: 'Labrador Retriever', age_years: 2.5, size: 'large',  energy_level: 'high',   temperament: 'energetic', training_level: 'medium', special_needs: false, hypoallergenic: false, kid_compatibility: 'high',   other_pets_compatibility: 'medium', shelter_notes: 'Active and playful.' },
  { name: 'Peanut',    emoji: '🐶', breed: 'Beagle',             age_years: 4.0, size: 'medium', energy_level: 'medium', temperament: 'friendly',  training_level: 'medium', special_needs: false, hypoallergenic: false, kid_compatibility: 'high',   other_pets_compatibility: 'high',   shelter_notes: 'Learning basic commands.' },
  { name: 'Coco',      emoji: '🐩', breed: 'Poodle',             age_years: 5.0, size: 'small',  energy_level: 'low',    temperament: 'calm',      training_level: 'high',   special_needs: false, hypoallergenic: true,  kid_compatibility: 'medium', other_pets_compatibility: 'high',   shelter_notes: 'Good with people.' },
  { name: 'Storm',     emoji: '🐺', breed: 'Husky',              age_years: 2.0, size: 'large',  energy_level: 'high',   temperament: 'energetic', training_level: 'low',    special_needs: false, hypoallergenic: false, kid_compatibility: 'medium', other_pets_compatibility: 'low',    shelter_notes: 'Needs consistent routine.' },
  { name: 'Daisy',     emoji: '🐾', breed: 'Shih Tzu',           age_years: 6.0, size: 'small',  energy_level: 'low',    temperament: 'calm',      training_level: 'medium', special_needs: false, hypoallergenic: true,  kid_compatibility: 'medium', other_pets_compatibility: 'medium', shelter_notes: 'May be shy at first.' },
  { name: 'Rex',       emoji: '🦴', breed: 'German Shepherd',    age_years: 3.5, size: 'large',  energy_level: 'high',   temperament: 'energetic', training_level: 'high',   special_needs: false, hypoallergenic: false, kid_compatibility: 'medium', other_pets_compatibility: 'medium', shelter_notes: 'Needs consistent routine.' },
  { name: 'Mochi',     emoji: '🐕', breed: 'Corgi',              age_years: 2.0, size: 'small',  energy_level: 'medium', temperament: 'friendly',  training_level: 'medium', special_needs: false, hypoallergenic: false, kid_compatibility: 'high',   other_pets_compatibility: 'high',   shelter_notes: 'Active and playful.' },
  { name: 'Buddy',     emoji: '🐶', breed: 'Boxer',              age_years: 4.0, size: 'large',  energy_level: 'medium', temperament: 'friendly',  training_level: 'medium', special_needs: false, hypoallergenic: false, kid_compatibility: 'high',   other_pets_compatibility: 'medium', shelter_notes: 'Good with people.' },
  { name: 'Rosie',     emoji: '🌹', breed: 'Mixed',              age_years: 7.0, size: 'medium', energy_level: 'low',    temperament: 'calm',      training_level: 'high',   special_needs: false, hypoallergenic: false, kid_compatibility: 'high',   other_pets_compatibility: 'high',   shelter_notes: 'Good with people.' },
  { name: 'Zeus',      emoji: '⚡', breed: 'Greyhound',          age_years: 3.0, size: 'large',  energy_level: 'medium', temperament: 'calm',      training_level: 'low',    special_needs: false, hypoallergenic: false, kid_compatibility: 'medium', other_pets_compatibility: 'medium', shelter_notes: 'May be shy at first.' },
  { name: 'Pepper',    emoji: '🐾', breed: 'Mixed',              age_years: 0.8, size: 'small',  energy_level: 'high',   temperament: 'energetic', training_level: 'low',    special_needs: false, hypoallergenic: false, kid_compatibility: 'medium', other_pets_compatibility: 'medium', shelter_notes: 'Active and playful.' },
  { name: 'Oliver',    emoji: '🐕', breed: 'Bulldog',            age_years: 5.0, size: 'medium', energy_level: 'low',    temperament: 'calm',      training_level: 'medium', special_needs: true,  hypoallergenic: false, kid_compatibility: 'high',   other_pets_compatibility: 'high',   shelter_notes: 'Has medical considerations.' },
  { name: 'Cinnamon',  emoji: '🍂', breed: 'Beagle',             age_years: 1.5, size: 'medium', energy_level: 'medium', temperament: 'friendly',  training_level: 'low',    special_needs: false, hypoallergenic: false, kid_compatibility: 'high',   other_pets_compatibility: 'high',   shelter_notes: 'Learning basic commands.' },
  { name: 'Scout',     emoji: '🐩', breed: 'Poodle',             age_years: 8.5, size: 'medium', energy_level: 'low',    temperament: 'shy',       training_level: 'high',   special_needs: false, hypoallergenic: true,  kid_compatibility: 'low',    other_pets_compatibility: 'medium', shelter_notes: 'May be shy at first.' },
  { name: 'Hazel',     emoji: '🌰', breed: 'Golden Retriever',   age_years: 9.0, size: 'large',  energy_level: 'low',    temperament: 'calm',      training_level: 'high',   special_needs: true,  hypoallergenic: false, kid_compatibility: 'high',   other_pets_compatibility: 'high',   shelter_notes: 'Has medical considerations.' },
  { name: 'Archie',    emoji: '🐶', breed: 'Corgi',              age_years: 1.0, size: 'small',  energy_level: 'high',   temperament: 'energetic', training_level: 'low',    special_needs: false, hypoallergenic: false, kid_compatibility: 'medium', other_pets_compatibility: 'medium', shelter_notes: 'Active and playful.' },
  { name: 'Maple',     emoji: '🍁', breed: 'Labrador Retriever', age_years: 6.5, size: 'large',  energy_level: 'medium', temperament: 'friendly',  training_level: 'high',   special_needs: false, hypoallergenic: false, kid_compatibility: 'high',   other_pets_compatibility: 'high',   shelter_notes: 'Good with people.' },
];

// ─── NAVIGATION ─────────────────────────────────────────────────────────────
function goToPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  document.querySelector(`.tab-btn[data-page="${name}"]`).classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => goToPage(btn.dataset.page));
});

// ─── HOME: DOG PREVIEW GRID ─────────────────────────────────────────────────
function renderDogPreviewGrid() {
  const grid = document.getElementById('dog-preview-grid');
  const preview = DOG_CATALOG.slice(0, 12);
  grid.innerHTML = preview.map(dog => `
    <div class="dog-preview-card">
      <div class="dog-emoji">${dog.emoji}</div>
      <div class="dog-preview-name">${dog.name}</div>
      <div class="dog-preview-breed">${dog.breed} &bull; ${dog.age_years}y</div>
      <div class="dog-tags">
        <span class="tag tag-size">${capitalize(dog.size)}</span>
        <span class="tag tag-energy-${dog.energy_level}">${capitalize(dog.energy_level)} energy</span>
        ${dog.hypoallergenic ? '<span class="tag" style="background:#f0fdf4;color:#16a34a">Hypo-allergenic</span>' : ''}
        ${dog.special_needs ? '<span class="tag" style="background:#fdf4ff;color:#9333ea">Special needs</span>' : ''}
      </div>
    </div>
  `).join('');
}

// ─── MATCH FORM ──────────────────────────────────────────────────────────────
document.getElementById('match-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  const btn = document.getElementById('match-btn');
  const panel = document.getElementById('match-results');

  btn.disabled = true;
  btn.textContent = 'Matching…';
  panel.innerHTML = `<div class="loading-spinner"><div class="spinner"></div> Analyzing your lifestyle…</div>`;

  const fd = new FormData(form);
  const user = {
    housing_type: fd.get('housing_type'),
    yard_size_bucket: fd.get('yard_size_bucket'),
    activity_level: fd.get('activity_level'),
    work_hours_away: parseFloat(fd.get('work_hours_away')),
    pet_experience: fd.get('pet_experience'),
    allergies: fd.get('allergies'),
    budget_monthly: parseFloat(fd.get('budget_monthly')),
    kids_in_household: parseInt(fd.get('kids_in_household')),
    other_pets_in_household: parseInt(fd.get('other_pets_in_household')),
    preferred_traits: {
      size: fd.get('preferred_size'),
      age: fd.get('preferred_age'),
      temperament: fd.get('preferred_temperament'),
    },
  };

  const preferredEnergy = fd.get('preferred_energy');
  const candidateDogs = DOG_CATALOG.map(({ name, emoji, ...dog }) => dog);

  try {
    const res = await fetch('/match_dogs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user, candidate_dogs: candidateDogs, top_k: 5 }),
    });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    const data = await res.json();
    renderMatchResults(panel, data, preferredEnergy);
  } catch (err) {
    panel.innerHTML = `<div class="error-msg">⚠️ Something went wrong: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Find My Matches';
  }
});

function renderMatchResults(panel, data, preferredEnergy) {
  const matches = data.matches || [];
  if (!matches.length) {
    panel.innerHTML = `<div class="results-placeholder"><div class="placeholder-icon">😔</div><p>No matches found. Try adjusting your preferences.</p></div>`;
    return;
  }

  const cards = matches.map((m, i) => {
    const dog = m.dog;
    const catalogDog = DOG_CATALOG.find(d => d.breed === dog.breed && d.age_years === dog.age_years) || {};
    const name = catalogDog.name || dog.breed.split(' ')[0];
    const emoji = catalogDog.emoji || '🐕';
    const score = m.compatibility_score;
    const pct = Math.round(score * 100);
    const tier = score >= 0.65 ? 'high' : score >= 0.45 ? 'medium' : 'low';
    const rankLabel = i === 0 ? '🥇' : `#${i + 1}`;
    const why = buildWhyText(m.why, dog, preferredEnergy);

    const ageLabel = dog.age_years < 1 ? 'Puppy' : dog.age_years < 8 ? `${dog.age_years}y` : `${dog.age_years}y (Senior)`;

    return `
      <div class="match-card">
        <div class="match-rank rank-${i + 1}">${rankLabel}</div>
        <div class="match-dog-info">
          <div class="match-dog-name">${emoji} ${name}</div>
          <div class="match-dog-breed">${dog.breed} &bull; ${ageLabel}</div>
          <div class="match-dog-tags">
            <span class="tag tag-size">${capitalize(dog.size)}</span>
            <span class="tag tag-energy-${dog.energy_level}">${capitalize(dog.energy_level)} energy</span>
            <span class="tag">${capitalize(dog.temperament)}</span>
            ${dog.hypoallergenic ? '<span class="tag" style="background:#f0fdf4;color:#16a34a">Hypo-allergenic</span>' : ''}
            ${dog.special_needs ? '<span class="tag" style="background:#fdf4ff;color:#9333ea">Special needs</span>' : ''}
          </div>
          <div class="match-why">${why}</div>
        </div>
        <div class="match-score-block">
          <div class="score-ring ${tier}">
            <span>${pct}%</span>
          </div>
          <div class="score-label">Match</div>
        </div>
      </div>`;
  }).join('');

  panel.innerHTML = `
    <div class="results-header">
      <h2>Your Top ${matches.length} Match${matches.length > 1 ? 'es' : ''}</h2>
      <p>Dogs ranked by compatibility with your lifestyle</p>
    </div>
    <div class="match-cards">${cards}</div>`;
}

function buildWhyText(why, dog, preferredEnergy) {
  const reasons = [];
  const model = (why && why.model) || [];
  const rules = (why && why.rules) || [];

  if (model.length) {
    const top = model.slice(0, 3);
    reasons.push(`<strong>Top factors:</strong> ${top.join(', ')}.`);
  }
  if (rules.length && !model.length) {
    reasons.push(`<strong>Key reasons:</strong> ${rules.slice(0, 3).join(', ')}.`);
  }
  if (!reasons.length) {
    reasons.push(`Good overall match with your lifestyle and preferences.`);
  }
  if (dog.shelter_notes) {
    reasons.push(`<em>Shelter note: "${dog.shelter_notes}"</em>`);
  }
  return reasons.join(' ');
}

// ─── RISK: DOG PICKER ────────────────────────────────────────────────────────
let selectedRiskDog = null;

function renderRiskDogPicker() {
  const picker = document.getElementById('risk-dog-picker');
  picker.innerHTML = DOG_CATALOG.map((dog, i) => `
    <button class="dog-pick-btn" data-idx="${i}" onclick="selectRiskDog(${i})">
      <div class="pick-emoji">${dog.emoji}</div>
      <div class="pick-name">${dog.name}</div>
      <div class="pick-breed">${dog.breed}</div>
    </button>
  `).join('');
}

function selectRiskDog(idx) {
  selectedRiskDog = idx;
  document.querySelectorAll('.dog-pick-btn').forEach((b, i) => {
    b.classList.toggle('selected', i === idx);
  });
}

async function runRiskCheck() {
  if (selectedRiskDog === null) {
    alert('Please select a dog first.');
    return;
  }

  const btn = document.getElementById('risk-btn');
  const resultEl = document.getElementById('risk-result');
  const userForm = document.getElementById('risk-user-form');
  const fd = new FormData(userForm);

  btn.disabled = true;
  btn.textContent = 'Assessing…';
  resultEl.innerHTML = `<div class="loading-spinner"><div class="spinner"></div> Running risk model…</div>`;

  const user = {
    housing_type: fd.get('housing_type'),
    yard_size_bucket: fd.get('yard_size_bucket'),
    activity_level: fd.get('activity_level'),
    work_hours_away: parseFloat(fd.get('work_hours_away')),
    pet_experience: fd.get('pet_experience'),
    allergies: fd.get('allergies'),
    budget_monthly: parseFloat(fd.get('budget_monthly')),
    kids_in_household: parseInt(fd.get('kids_in_household')),
    other_pets_in_household: parseInt(fd.get('other_pets_in_household')),
    preferred_traits: { size: 'medium', age: 'adult', temperament: 'friendly' },
  };

  const catalogDog = DOG_CATALOG[selectedRiskDog];
  const { name, emoji, ...dog } = catalogDog;

  try {
    const res = await fetch('/predict_risk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user, dog }),
    });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    const data = await res.json();
    renderRiskResult(resultEl, data, catalogDog);
  } catch (err) {
    resultEl.innerHTML = `<div class="error-msg">⚠️ ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Check Adoption Risk';
  }
}

function renderRiskResult(el, data, dog) {
  const score = data.risk_score;
  const pct = Math.round(score * 100);
  const label = data.risk_label || '';
  const tier = label.toLowerCase().includes('low') ? 'low' : label.toLowerCase().includes('high') ? 'high' : 'medium';

  const why = data.why || {};
  const model = why.model || [];
  const rules = why.rules || [];
  const allFactors = [...model, ...rules].slice(0, 6);

  const factorItems = allFactors.length
    ? allFactors.map(f => {
        const isNeg = /mismatch|risk|high|severe|allerg|special|no.*experience/i.test(f);
        const cls = isNeg ? 'factor-negative' : 'factor-positive';
        return `<li class="${cls}">${f}</li>`;
      }).join('')
    : '<li class="factor-neutral">Overall risk based on lifestyle compatibility.</li>';

  const interpretation = tier === 'low'
    ? 'Great news! Based on your profile and this dog\'s characteristics, this adoption looks like a strong, lasting fit.'
    : tier === 'high'
    ? 'There are some potential mismatches. Consider speaking with a shelter advisor before proceeding.'
    : 'Moderate compatibility. With proper preparation and commitment, this could still be a successful adoption.';

  el.innerHTML = `
    <div class="risk-card">
      <div class="risk-dog-summary">
        <h3>${dog.emoji} ${dog.name} &mdash; ${dog.breed}</h3>
        <p>${capitalize(dog.size)} &bull; ${capitalize(dog.energy_level)} energy &bull; ${dog.age_years}y old</p>
      </div>
      <div class="risk-gauge-wrap">
        <div class="risk-gauge ${tier}">
          <span class="risk-pct">${pct}%</span>
          <span class="risk-sub">risk</span>
        </div>
        <span class="risk-label-badge ${tier}">${label}</span>
      </div>
      <p style="font-size:.85rem;color:var(--text-secondary);margin-bottom:20px;line-height:1.6">${interpretation}</p>
      <div class="risk-explanation">
        <h4>Key Factors</h4>
        <ul class="risk-factors">${factorItems}</ul>
      </div>
    </div>`;
}

// ─── UTILS ───────────────────────────────────────────────────────────────────
function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ─── INIT ────────────────────────────────────────────────────────────────────
renderDogPreviewGrid();
renderRiskDogPicker();
