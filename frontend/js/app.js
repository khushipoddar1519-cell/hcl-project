/**
 * Hotel Analytics Single Page Application Controller
 */

// Application State
const State = {
  currentView: 'dashboard',
  hotel: 'All',
  startDate: '',
  endDate: '',
  currentUser: null,
  kpis: null,
  trend: null,
  segments: null,
  rooms: null,
  forecast: null,
  settings: null,
  predictDebounce: null,
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  // Always start fresh on the landing page (do not persist user across visits)
  State.currentUser = null;
  API.logout();

  initLandingPage();
  initAuth();
  initNavigation();
  initGlobalFilters();
  initPredictorForm();
  initForecastingControls();
  initRevenueOptimizer();
  initBookingsManager();
  initSettingsView();

  showLandingPage();

  // Responsive re-render on orientation change or screen resize
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      const appLayout = document.getElementById('app-layout');
      if (appLayout && appLayout.style.display !== 'none' && State.currentUser) {
        loadCurrentView();
      }
    }, 250);
  });
});

// View switcher between Public Landing Page and Internal Web App
function showLandingPage() {
  const landing = document.getElementById('landing-page');
  const app = document.getElementById('app-layout');
  if (landing) landing.style.display = 'flex';
  if (app) app.style.display = 'none';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showAppLayout() {
  const landing = document.getElementById('landing-page');
  const app = document.getElementById('app-layout');
  if (landing) landing.style.display = 'none';
  if (app) app.style.display = 'flex';
}

// ----------------------------------------------------------------------------- Landing Page Controls
function initLandingPage() {
  initDynamicParticles();
  animateHeroCounters();

  const heroTabSignIn = document.getElementById('hero-tab-signin');
  const heroTabSignUp = document.getElementById('hero-tab-signup');

  heroTabSignIn?.addEventListener('click', () => focusAuthTab('signin'));
  heroTabSignUp?.addEventListener('click', () => focusAuthTab('signup'));

  // Landing Page Sign In Form
  document.getElementById('hero-login-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ident = document.getElementById('hl-ident').value.trim();
    const pwd = document.getElementById('hl-pwd').value;
    try {
      const res = await API.login(ident, pwd);
      State.currentUser = res.user;
      updateUserUI();
      showAppLayout();
      showToast(`Welcome back, ${res.user.name}!`, 'success');
      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Landing Page Sign Up Form
  document.getElementById('hero-signup-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('hsu-name').value.trim();
    const email = document.getElementById('hsu-email').value.trim();
    const username = document.getElementById('hsu-username').value.trim();
    const role = document.getElementById('hsu-role').value;
    const pwd = document.getElementById('hsu-pwd').value;

    if (pwd.length < 4) {
      showToast('Password must be at least 4 characters', 'error');
      return;
    }

    try {
      const res = await API.register(name, email, username, pwd, role);
      State.currentUser = res.user;
      updateUserUI();
      showAppLayout();
      showToast(`Welcome, ${res.user.name}!`, 'success');
      loadDashboardData();
    } catch (err) {
      showToast(`Sign up failed: ${err.message}`, 'error');
    }
  });
}

// Dynamic Animated Particle Network
function initDynamicParticles() {
  const canvas = document.getElementById('hero-particles');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let width = canvas.width = window.innerWidth;
  let height = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    if (!canvas) return;
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const count = Math.min(Math.floor(width / 22), 65);
  const particles = [];

  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      radius: Math.random() * 1.8 + 1,
      color: i % 2 === 0 ? 'rgba(15, 157, 146, ' : 'rgba(139, 92, 246, '
    });
  }

  let mouseX = -1000;
  let mouseY = -1000;
  window.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  function render() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0 || p.x > width) p.vx *= -1;
      if (p.y < 0 || p.y > height) p.vy *= -1;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = p.color + '0.6)';
      ctx.fill();

      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 110) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(15, 157, 146, ${0.15 * (1 - dist / 110)})`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }

      const mdx = p.x - mouseX;
      const mdy = p.y - mouseY;
      const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
      if (mdist < 130) {
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(mouseX, mouseY);
        ctx.strokeStyle = `rgba(45, 212, 191, ${0.3 * (1 - mdist / 130)})`;
        ctx.lineWidth = 0.9;
        ctx.stroke();
      }
    }

    requestAnimationFrame(render);
  }

  render();
}

// Number Counting Animation
function animateHeroCounters() {
  const bEl = document.getElementById('stat-bookings');
  const aEl = document.getElementById('stat-acc');
  const uEl = document.getElementById('stat-auc');
  if (!bEl) return;

  const targetB = 119390;
  const targetA = 86.9;
  const targetU = 0.944;
  const duration = 1000;
  const startTime = performance.now();

  function update(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);

    bEl.textContent = Math.round(targetB * ease).toLocaleString();
    aEl.textContent = (targetA * ease).toFixed(1) + '%';
    uEl.textContent = (targetU * ease).toFixed(3);

    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

// Global functions accessible from inline HTML on landing page
window.focusAuthTab = function(tabName) {
  const heroTabSignIn = document.getElementById('hero-tab-signin');
  const heroTabSignUp = document.getElementById('hero-tab-signup');
  const heroPanelSignIn = document.getElementById('hero-panel-signin');
  const heroPanelSignUp = document.getElementById('hero-panel-signup');
  const authCard = document.getElementById('landing-auth-card');

  if (tabName === 'signin') {
    if (heroTabSignIn) heroTabSignIn.className = 'auth-toggle-btn active';
    if (heroTabSignUp) heroTabSignUp.className = 'auth-toggle-btn';
    if (heroPanelSignIn) heroPanelSignIn.style.display = 'block';
    if (heroPanelSignUp) heroPanelSignUp.style.display = 'none';
  } else {
    if (heroTabSignUp) heroTabSignUp.className = 'auth-toggle-btn active';
    if (heroTabSignIn) heroTabSignIn.className = 'auth-toggle-btn';
    if (heroPanelSignUp) heroPanelSignUp.style.display = 'block';
    if (heroPanelSignIn) heroPanelSignIn.style.display = 'none';
  }

  authCard?.scrollIntoView({ behavior: 'smooth' });
};

// ----------------------------------------------------------------------------- Auth
function initAuth() {
  State.currentUser = null;

  const userBtn = document.getElementById('user-menu-btn');
  const userDropdown = document.getElementById('user-dropdown-menu');
  const userModal = document.getElementById('login-modal');
  const dropdownLogoutBtn = document.getElementById('dropdown-logout-btn');
  const dropdownSwitchBtn = document.getElementById('dropdown-switch-btn');
  const modalLogoutBtn = document.getElementById('modal-logout-btn');

  // Toggle user dropdown under the user badge
  if (userBtn && userDropdown) {
    userBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('active');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!userBtn.contains(e.target) && !userDropdown.contains(e.target)) {
        userDropdown.classList.remove('active');
      }
    });
  }

  // "Login Another Account" option from dropdown opens the switch account modal
  dropdownSwitchBtn?.addEventListener('click', () => {
    userDropdown?.classList.remove('active');
    userModal?.classList.add('active');
  });

  document.getElementById('modal-close-btn')?.addEventListener('click', () => {
    userModal?.classList.remove('active');
  });

  // Modal Auth Tabs
  const tabBtnSignIn = document.getElementById('tab-btn-signin');
  const tabBtnSignUp = document.getElementById('tab-btn-signup');
  const panelSignIn = document.getElementById('auth-panel-signin');
  const panelSignUp = document.getElementById('auth-panel-signup');

  tabBtnSignIn?.addEventListener('click', () => {
    tabBtnSignIn.className = 'btn btn-sm btn-primary';
    tabBtnSignUp.className = 'btn btn-sm btn-secondary';
    panelSignIn.style.display = 'block';
    panelSignUp.style.display = 'none';
  });

  tabBtnSignUp?.addEventListener('click', () => {
    tabBtnSignUp.className = 'btn btn-sm btn-primary';
    tabBtnSignIn.className = 'btn btn-sm btn-secondary';
    panelSignUp.style.display = 'block';
    panelSignIn.style.display = 'none';
  });

  // Standard Login (from modal)
  document.getElementById('login-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ident = document.getElementById('login-ident').value.trim();
    const pwd = document.getElementById('login-pwd').value;
    try {
      const res = await API.login(ident, pwd);
      State.currentUser = res.user;
      updateUserUI();
      showAppLayout();
      userModal?.classList.remove('active');
      userDropdown?.classList.remove('active');
      showToast(`Welcome back, ${res.user.name}!`, 'success');
      loadCurrentView();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // User Sign Up (Register Any New User from modal)
  document.getElementById('signup-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('su-name').value.trim();
    const email = document.getElementById('su-email').value.trim();
    const username = document.getElementById('su-username').value.trim();
    const role = document.getElementById('su-role').value;
    const pwd = document.getElementById('su-pwd').value;

    if (pwd.length < 4) {
      showToast('Password must be at least 4 characters', 'error');
      return;
    }

    try {
      const res = await API.register(name, email, username, pwd, role);
      State.currentUser = res.user;
      updateUserUI();
      showAppLayout();
      userModal?.classList.remove('active');
      userDropdown?.classList.remove('active');
      showToast(`Account created successfully! Welcome, ${res.user.name}`, 'success');
      loadCurrentView();
    } catch (err) {
      showToast(`Registration failed: ${err.message}`, 'error');
    }
  });

  // Common Logout Function
  const performLogout = () => {
    API.logout();
    State.currentUser = null;
    userDropdown?.classList.remove('active');
    userModal?.classList.remove('active');
    updateUserUI();
    showLandingPage();
    showToast('Signed out successfully. Welcome to the landing page.', 'info');
  };

  // Logout triggers
  dropdownLogoutBtn?.addEventListener('click', performLogout);
  modalLogoutBtn?.addEventListener('click', performLogout);
  document.getElementById('sidebar-logout-btn')?.addEventListener('click', performLogout);

  updateUserUI();
}

function updateUserUI() {
  const nameEl = document.getElementById('topbar-user-name');
  const roleEl = document.getElementById('topbar-user-role');
  const avatarEl = document.getElementById('topbar-user-avatar');

  const dNameEl = document.getElementById('dropdown-user-name');
  const dRoleEl = document.getElementById('dropdown-user-role');
  const dAvatarEl = document.getElementById('dropdown-user-avatar');
  const dLogoutBtn = document.getElementById('dropdown-logout-btn');

  const modalBanner = document.getElementById('modal-current-user-banner');
  const modalSwitchPrompt = document.getElementById('modal-switch-prompt');
  const modalNameEl = document.getElementById('modal-user-name');
  const modalRoleEl = document.getElementById('modal-user-role');
  const modalAvatarEl = document.getElementById('modal-user-avatar');

  if (State.currentUser) {
    const initial = State.currentUser.name.charAt(0).toUpperCase();

    // Topbar
    if (nameEl) nameEl.textContent = State.currentUser.name;
    if (roleEl) roleEl.textContent = State.currentUser.role;
    if (avatarEl) avatarEl.textContent = initial;

    // Dropdown under user
    if (dNameEl) dNameEl.textContent = State.currentUser.name;
    if (dRoleEl) dRoleEl.textContent = State.currentUser.role;
    if (dAvatarEl) dAvatarEl.textContent = initial;
    if (dLogoutBtn) dLogoutBtn.style.display = 'flex';

    // Modal banner
    if (modalBanner) modalBanner.style.display = 'flex';
    if (modalSwitchPrompt) modalSwitchPrompt.style.display = 'block';
    if (modalNameEl) modalNameEl.textContent = State.currentUser.name;
    if (modalRoleEl) modalRoleEl.textContent = State.currentUser.role;
    if (modalAvatarEl) modalAvatarEl.textContent = initial;
  } else {
    // Topbar
    if (nameEl) nameEl.textContent = 'Sign In / Register';
    if (roleEl) roleEl.textContent = 'Guest';
    if (avatarEl) avatarEl.textContent = '👤';

    // Dropdown under user
    if (dNameEl) dNameEl.textContent = 'Guest';
    if (dRoleEl) dRoleEl.textContent = 'Not Signed In';
    if (dAvatarEl) dAvatarEl.textContent = '👤';
    if (dLogoutBtn) dLogoutBtn.style.display = 'none';

    // Modal banner
    if (modalBanner) modalBanner.style.display = 'none';
    if (modalSwitchPrompt) modalSwitchPrompt.style.display = 'none';
  }

  // Toggle admin-only nav items
  const isAdmin = State.currentUser && State.currentUser.role === 'Administrator';
  document.querySelectorAll('.admin-only').forEach(el => {
    el.style.display = isAdmin ? 'flex' : 'none';
  });
}

// ----------------------------------------------------------------------------- Navigation
function initNavigation() {
  const mobileToggle = document.getElementById('mobile-menu-toggle');
  const mobileClose = document.getElementById('mobile-sidebar-close');
  const mobileBackdrop = document.getElementById('mobile-nav-backdrop');
  const sidebar = document.getElementById('app-sidebar');

  const openMobileNav = () => {
    sidebar?.classList.add('mobile-open');
    mobileBackdrop?.classList.add('active');
    document.body.style.overflow = 'hidden';
  };

  const closeMobileNav = () => {
    sidebar?.classList.remove('mobile-open');
    mobileBackdrop?.classList.remove('active');
    document.body.style.overflow = '';
  };

  window.closeMobileNav = closeMobileNav;

  mobileToggle?.addEventListener('click', openMobileNav);
  mobileClose?.addEventListener('click', closeMobileNav);
  mobileBackdrop?.addEventListener('click', closeMobileNav);

  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const view = btn.getAttribute('data-view');
      navigateTo(view);
      closeMobileNav();
    });
  });
}

function navigateTo(viewName) {
  State.currentView = viewName;
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.getAttribute('data-view') === viewName);
  });
  document.querySelectorAll('.view-section').forEach(sec => {
    sec.classList.toggle('active', sec.id === `view-${viewName}`);
  });
  if (window.closeMobileNav) window.closeMobileNav();
  loadCurrentView();
}

function loadCurrentView() {
  switch (State.currentView) {
    case 'dashboard':
      loadDashboardData();
      break;
    case 'predictor':
      calculateRisk();
      break;
    case 'cancellation':
      loadCancellationDeepDive();
      break;
    case 'forecasting':
      loadForecastingData();
      break;
    case 'revenue':
      loadRevenueOptimizer();
      break;
    case 'bookings':
      loadBookingsTable();
      break;
    case 'settings':
      loadSettingsView();
      break;
  }
}

// ----------------------------------------------------------------------------- Global Filters
function initGlobalFilters() {
  const hotelSel = document.getElementById('global-hotel-filter');
  if (hotelSel) {
    hotelSel.addEventListener('change', (e) => {
      State.hotel = e.target.value;
      loadCurrentView();
    });
  }

  const rangeSel = document.getElementById('global-range-filter');
  if (rangeSel) {
    rangeSel.addEventListener('change', (e) => {
      const val = e.target.value;
      if (val === '12m') {
        State.startDate = '2016-09-01';
        State.endDate = '2017-08-31';
      } else if (val === 'all') {
        State.startDate = '';
        State.endDate = '';
      } else if (val === '2016') {
        State.startDate = '2016-01-01';
        State.endDate = '2016-12-31';
      } else if (val === '2017') {
        State.startDate = '2017-01-01';
        State.endDate = '2017-08-31';
      }
      loadCurrentView();
    });
  }
}

// ----------------------------------------------------------------------------- Dashboard View
async function loadDashboardData() {
  try {
    const [kpisRes, trendRes, roomsRes, segsRes] = await Promise.all([
      API.getKPIs(State.startDate, State.endDate, State.hotel),
      API.getTrend(State.startDate, State.endDate, State.hotel),
      API.getRooms(State.startDate, State.endDate, State.hotel),
      API.getSegments(State.startDate, State.endDate, State.hotel)
    ]);

    State.kpis = kpisRes;
    State.trend = trendRes;
    State.rooms = roomsRes;
    State.segments = segsRes;

    renderKPIs(kpisRes);
    Charts.renderTrendChart('chart-trend-container', trendRes);
    Charts.renderRoomDonut('chart-room-container', roomsRes);
    renderTopSegmentsTable(segsRes);
    renderInsights(kpisRes.insights, kpisRes.tip);
  } catch (err) {
    console.error('Error loading dashboard:', err);
    showToast('Failed to load dashboard data', 'error');
  }
}

function renderKPIs(data) {
  const cur = data.current;
  const d = data.deltas;

  document.getElementById('kpi-bookings').textContent = cur.bookings_formatted;
  document.getElementById('kpi-cancel-rate').textContent = `${cur.cancel_rate_pct}%`;
  document.getElementById('kpi-revenue').textContent = cur.revenue_formatted;
  document.getElementById('kpi-adr').textContent = cur.adr_formatted;

  renderDelta('delta-bookings', d.bookings, 'up');
  renderDelta('delta-cancel-rate', d.cancel_rate, 'down');
  renderDelta('delta-revenue', d.revenue, 'up');
  renderDelta('delta-adr', d.adr, 'up');
}

function renderDelta(elemId, deltaVal, goodDir) {
  const el = document.getElementById(elemId);
  if (!el) return;
  if (deltaVal === null || deltaVal === undefined) {
    el.className = 'kpi-delta neutral';
    el.textContent = 'vs. prior period: N/A';
    return;
  }
  const isUp = deltaVal >= 0;
  const isGood = (isUp && goodDir === 'up') || (!isUp && goodDir === 'down');
  el.className = `kpi-delta ${isGood ? 'up' : 'down'}`;
  const arrow = isUp ? '↑' : '↓';
  el.textContent = `${arrow} ${Math.abs(deltaVal)}% vs. previous period`;
}

function renderTopSegmentsTable(segments) {
  const tbody = document.getElementById('top-segments-tbody');
  if (!tbody || !segments) return;

  const top = segments.slice(0, 5);
  tbody.innerHTML = top.map(s => `
    <tr>
      <td style="font-weight:600;">${s.segment}</td>
      <td>${s.bookings.toLocaleString()}</td>
      <td>
        <span class="badge ${s.cancel_rate > 35 ? 'badge-high' : 'badge-low'}">
          ${s.cancel_rate}%
        </span>
      </td>
      <td style="font-weight:600;">${s.revenue_formatted}</td>
      <td>
        <div style="display:flex; align-items:center; gap:8px;">
          <div style="flex:1; height:6px; background:rgba(255,255,255,0.06); border-radius:99px; overflow:hidden;">
            <div style="width:${s.revenue_share}%; height:100%; background:var(--primary); border-radius:99px;"></div>
          </div>
          <span style="font-size:12px; color:#94a3b8;">${s.revenue_share}%</span>
        </div>
      </td>
    </tr>
  `).join('');
}

function renderInsights(insights, tip) {
  const listEl = document.getElementById('insights-container');
  if (!listEl) return;

  let html = '';
  if (tip) {
    html += `
      <div style="background:rgba(15,157,146,0.12); border:1px solid rgba(15,157,146,0.3); border-radius:12px; padding:14px 18px; margin-bottom:16px; display:flex; align-items:center; gap:14px;">
        <span style="font-size:24px;">💡</span>
        <div>
          <div style="font-weight:600; color:#2dd4bf; font-size:14px;">Proactive Revenue Tip</div>
          <div style="font-size:13px; color:#cbd5e1; margin-top:2px;">
            Targeting a 20% cancellation drop in <b>${tip.segment}</b> could recover up to <b>+${tip.uplift.toFixed(1)}% revenue</b>.
          </div>
        </div>
      </div>
    `;
  }

  if (insights && insights.length > 0) {
    html += '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">';
    insights.slice(0, 3).forEach(ins => {
      let icon = '⚡';
      if (ins.kind === 'cancel') icon = '🚫';
      if (ins.kind === 'demand') icon = '📈';
      if (ins.kind === 'revenue') icon = '💰';

      html += `
        <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:12px; padding:16px;">
          <div style="display:flex; align-items:center; gap:8px; font-weight:600; font-size:13px; color:#fff; margin-bottom:6px;">
            <span>${icon}</span>
            <span>${ins.title}</span>
          </div>
          <div style="font-size:12.5px; color:#94a3b8; line-height:1.4;">${ins.desc}</div>
        </div>
      `;
    });
    html += '</div>';
  }

  listEl.innerHTML = html;
}

// ----------------------------------------------------------------------------- Risk Predictor Studio
function initPredictorForm() {
  const form = document.getElementById('booking-predict-form');
  if (!form) return;

  // Real-time live scoring on inputs
  form.querySelectorAll('input, select').forEach(input => {
    input.addEventListener('input', () => {
      clearTimeout(State.predictDebounce);
      State.predictDebounce = setTimeout(calculateRisk, 250);
    });
  });

  // Save Booking Button
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = getFormData();
    try {
      const res = await API.createBooking(data);
      showToast(`Booking ${res.booking_id} saved! Risk: ${res.risk_score}% (${res.risk_level})`, 'success');
      loadDashboardData();
    } catch (err) {
      showToast(`Failed to save booking: ${err.message}`, 'error');
    }
  });

  // Calculate immediately on load
  calculateRisk();
}

function getFormData() {
  return {
    guest_name: document.getElementById('bf-guest-name')?.value || 'Guest',
    hotel: document.getElementById('bf-hotel')?.value || 'City Hotel',
    lead_time: parseInt(document.getElementById('bf-lead-time')?.value || 30),
    arrival_date_month: document.getElementById('bf-month')?.value || 'August',
    arrival_date_day_of_month: parseInt(document.getElementById('bf-day')?.value || 15),
    stays_in_weekend_nights: parseInt(document.getElementById('bf-we-nights')?.value || 1),
    stays_in_week_nights: parseInt(document.getElementById('bf-wk-nights')?.value || 2),
    adults: parseInt(document.getElementById('bf-adults')?.value || 2),
    children: parseFloat(document.getElementById('bf-children')?.value || 0),
    meal: document.getElementById('bf-meal')?.value || 'BB',
    country: document.getElementById('bf-country')?.value || 'PRT',
    market_segment: document.getElementById('bf-segment')?.value || 'Online TA',
    distribution_channel: document.getElementById('bf-channel')?.value || 'TA/TO',
    deposit_type: document.getElementById('bf-deposit')?.value || 'No Deposit',
    customer_type: document.getElementById('bf-customer')?.value || 'Transient',
    reserved_room_type: document.getElementById('bf-room')?.value || 'A',
    adr: parseFloat(document.getElementById('bf-adr')?.value || 120.0),
    is_repeated_guest: document.getElementById('bf-repeat')?.checked ? 1 : 0,
    previous_cancellations: parseInt(document.getElementById('bf-prev-canc')?.value || 0),
    total_of_special_requests: parseInt(document.getElementById('bf-requests')?.value || 0),
    booking_changes: parseInt(document.getElementById('bf-changes')?.value || 0),
    required_car_parking_spaces: parseInt(document.getElementById('bf-parking')?.value || 0),
  };
}

async function calculateRisk() {
  const data = getFormData();
  try {
    const res = await API.predictRisk(data);
    Charts.renderGauge('gauge-container', res.probability_pct, res.risk_level);
    Charts.renderDrivers('drivers-container', res.drivers);

    const levelBadge = document.getElementById('risk-level-badge');
    if (levelBadge) {
      levelBadge.className = `badge badge-${res.risk_level.toLowerCase()}`;
      levelBadge.textContent = `${res.risk_level} Risk`;
    }

    const revRiskEl = document.getElementById('revenue-at-risk');
    if (revRiskEl) {
      revRiskEl.textContent = `${res.currency_symbol} ${res.revenue_at_risk.toLocaleString()}`;
    }

    const recsEl = document.getElementById('recommendations-container');
    if (recsEl) {
      recsEl.innerHTML = res.recommendations.map(r => `
        <div class="rec-item">
          <span class="rec-icon">🛡️</span>
          <span>${r}</span>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Error calculating risk:', err);
  }
}

// ----------------------------------------------------------------------------- Cancellation Deep Dive
async function loadCancellationDeepDive() {
  try {
    const drivers = await API.getCancellationDrivers(State.startDate, State.endDate, State.hotel);
    const geo = await API.getGeography(10);

    // Lead time buckets
    const leadEl = document.getElementById('lead-time-bars');
    if (leadEl && drivers.lead_time) {
      leadEl.innerHTML = drivers.lead_time.map(b => `
        <div style="margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
            <span>${b.bucket}</span>
            <span style="font-weight:600; color:${b.cancel_rate > 35 ? '#f43f5e' : '#10b981'};">${b.cancel_rate}% Cancelled (${b.bookings.toLocaleString()} Bookings)</span>
          </div>
          <div style="height:8px; background:rgba(255,255,255,0.06); border-radius:99px; overflow:hidden;">
            <div style="width:${b.cancel_rate}%; height:100%; background:${b.cancel_rate > 35 ? '#f43f5e' : '#10b981'}; border-radius:99px;"></div>
          </div>
        </div>
      `).join('');
    }

    // Deposit types
    const depEl = document.getElementById('deposit-types-bars');
    if (depEl && drivers.deposit_types) {
      depEl.innerHTML = drivers.deposit_types.map(d => `
        <div style="margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
            <span>${d.deposit_type}</span>
            <span style="font-weight:600; color:${d.cancel_rate > 50 ? '#f43f5e' : '#10b981'};">${d.cancel_rate}% (${d.bookings.toLocaleString()} Bookings)</span>
          </div>
          <div style="height:8px; background:rgba(255,255,255,0.06); border-radius:99px; overflow:hidden;">
            <div style="width:${d.cancel_rate}%; height:100%; background:${d.cancel_rate > 50 ? '#f43f5e' : '#10b981'}; border-radius:99px;"></div>
          </div>
        </div>
      `).join('');
    }

    // Country rankings
    const geoTbody = document.getElementById('country-risk-tbody');
    if (geoTbody && geo) {
      geoTbody.innerHTML = geo.map(g => `
        <tr>
          <td><b>${g.country_code}</b> · ${g.country_name}</td>
          <td>${g.bookings.toLocaleString()}</td>
          <td>
            <span class="badge ${g.cancel_rate > 35 ? 'badge-high' : 'badge-low'}">
              ${g.cancel_rate}%
            </span>
          </td>
          <td>${g.revenue_formatted}</td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading cancellation deep dive:', err);
  }
}

// ----------------------------------------------------------------------------- Demand Forecasting
function initForecastingControls() {
  const metricSel = document.getElementById('fc-metric-select');
  const horizonSel = document.getElementById('fc-horizon-select');
  const scenarioSlider = document.getElementById('fc-scenario-slider');
  const scenarioVal = document.getElementById('fc-scenario-val');

  if (scenarioSlider && scenarioVal) {
    scenarioSlider.addEventListener('input', (e) => {
      const v = e.target.value;
      scenarioVal.textContent = (v >= 0 ? '+' : '') + v + '%';
      loadForecastingData();
    });
  }

  [metricSel, horizonSel].forEach(ctrl => {
    ctrl?.addEventListener('change', () => loadForecastingData());
  });
}

async function loadForecastingData() {
  const metric = document.getElementById('fc-metric-select')?.value || 'net_bookings';
  const horizon = parseInt(document.getElementById('fc-horizon-select')?.value || 6);
  const scenario = parseFloat(document.getElementById('fc-scenario-slider')?.value || 0);

  try {
    const data = await API.getForecast(metric, horizon, scenario, State.hotel);
    Charts.renderForecastChart('chart-forecast-container', data);

    // Render seasonality index
    const seasEl = document.getElementById('seasonal-index-container');
    if (seasEl && data.seasonal_index) {
      seasEl.innerHTML = Object.entries(data.seasonal_index).map(([month, val]) => {
        const isPeak = val >= 1.1;
        const isLow = val <= 0.85;
        const color = isPeak ? '#10b981' : (isLow ? '#f43f5e' : '#3b82f6');
        return `
          <div style="text-align:center; padding:10px; background:rgba(255,255,255,0.03); border:1px solid var(--border-color); border-radius:8px;">
            <div style="font-size:11px; color:#94a3b8;">${month}</div>
            <div style="font-size:15px; font-weight:700; color:${color}; margin-top:4px;">${val}x</div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error loading forecast:', err);
  }
}

// ----------------------------------------------------------------------------- Revenue Optimizer
function initRevenueOptimizer() {
  const redSlider = document.getElementById('rev-reduc-slider');
  const redVal = document.getElementById('rev-reduc-val');

  if (redSlider && redVal) {
    redSlider.addEventListener('input', (e) => {
      redVal.textContent = e.target.value + '%';
      updateRevenueSimulation();
    });
  }
}

async function loadRevenueOptimizer() {
  if (!State.segments) {
    State.segments = await API.getSegments(State.startDate, State.endDate, State.hotel);
  }
  updateRevenueSimulation();
}

function updateRevenueSimulation() {
  const redPct = parseFloat(document.getElementById('rev-reduc-slider')?.value || 20) / 100;
  if (!State.segments) return;

  const totalRev = State.segments.reduce((acc, s) => acc + s.revenue, 0);
  let totalRecovered = 0;

  const tbody = document.getElementById('rev-sim-tbody');
  if (tbody) {
    tbody.innerHTML = State.segments.map(s => {
      // Estimated lost revenue proportional to cancel rate
      const lostEst = s.revenue * (s.cancel_rate / (100 - s.cancel_rate || 1));
      const recovered = lostEst * redPct;
      totalRecovered += recovered;

      return `
        <tr>
          <td><b>${s.segment}</b></td>
          <td>${s.revenue_formatted}</td>
          <td>${s.cancel_rate}%</td>
          <td style="color:#10b981; font-weight:600;">+₹ ${(recovered / 1e5).toFixed(2)} L</td>
        </tr>
      `;
    }).join('');
  }

  const upliftPct = totalRev > 0 ? (totalRecovered / totalRev) * 100 : 0;
  const upliftEl = document.getElementById('rev-sim-total-uplift');
  if (upliftEl) {
    upliftEl.textContent = `+₹ ${(totalRecovered / 1e7).toFixed(2)} Cr (+${upliftPct.toFixed(1)}% Revenue Uplift)`;
  }
}

// ----------------------------------------------------------------------------- Bookings Database
function initBookingsManager() {
  const searchInput = document.getElementById('booking-search');
  const filterHotel = document.getElementById('booking-filter-hotel');
  const filterStatus = document.getElementById('booking-filter-status');

  let deb;
  searchInput?.addEventListener('input', () => {
    clearTimeout(deb);
    deb = setTimeout(loadBookingsTable, 300);
  });

  [filterHotel, filterStatus].forEach(ctrl => {
    ctrl?.addEventListener('change', () => loadBookingsTable());
  });
}

async function loadBookingsTable() {
  const search = document.getElementById('booking-search')?.value || '';
  const hotel = document.getElementById('booking-filter-hotel')?.value || 'All';
  const status = document.getElementById('booking-filter-status')?.value || 'All';

  try {
    const res = await API.listBookings({
      search,
      hotel,
      status,
      limit: 25,
      offset: 0
    });

    const tbody = document.getElementById('bookings-tbody');
    const countEl = document.getElementById('bookings-count-label');
    if (countEl) countEl.textContent = `Showing ${res.bookings.length} of ${res.total.toLocaleString()} bookings`;

    if (tbody) {
      if (res.bookings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:30px; color:#94a3b8;">No reservations match the filters.</td></tr>';
        return;
      }

      tbody.innerHTML = res.bookings.map(b => {
        let statusBadge = 'badge-confirmed';
        if (b.reservation_status === 'Canceled') statusBadge = 'badge-canceled';
        if (b.reservation_status === 'Check-Out') statusBadge = 'badge-checkout';

        let riskBadge = '';
        if (b.risk_level) {
          riskBadge = `<span class="badge badge-${b.risk_level.toLowerCase()}">${b.risk_score || ''}% ${b.risk_level}</span>`;
        }

        return `
          <tr>
            <td><code style="color:#2dd4bf;">${b.booking_id}</code></td>
            <td><b>${b.guest_name}</b></td>
            <td>${b.hotel}</td>
            <td>${b.arrival_date}</td>
            <td>${b.room_group}</td>
            <td>${b.revenue_formatted}</td>
            <td><span class="badge ${statusBadge}">${b.reservation_status}</span></td>
            <td>${riskBadge}</td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error loading bookings table:', err);
  }
}

// ----------------------------------------------------------------------------- Settings & Diagnostics
function initSettingsView() {
  document.getElementById('retrain-model-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('retrain-model-btn');
    btn.disabled = true;
    btn.textContent = 'Training Model (~15s)...';
    try {
      const res = await API.retrainModel();
      showToast(`Model retrained! Accuracy: ${(res.accuracy * 100).toFixed(1)}% | AUC: ${res.auc}`, 'success');
      loadSettingsView();
    } catch (err) {
      showToast(`Training failed: ${err.message}`, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Retrain ML Model';
    }
  });

  // Admin add user form
  document.getElementById('admin-add-user-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('au-username').value.trim();
    const name = document.getElementById('au-name').value.trim();
    const email = document.getElementById('au-email').value.trim();
    const role = document.getElementById('au-role').value;
    const password = document.getElementById('au-pwd').value;

    try {
      await API.createUser({ username, name, email, role, password });
      showToast(`User '${username}' created successfully!`, 'success');
      document.getElementById('admin-add-user-form').reset();
      loadSettingsUsers();
    } catch (err) {
      showToast(`Failed to create user: ${err.message}`, 'error');
    }
  });
}

async function loadSettingsView() {
  try {
    const diag = await API.getDiagnostics();
    document.getElementById('diag-accuracy').textContent = `${(diag.accuracy * 100).toFixed(1)}%`;
    document.getElementById('diag-auc').textContent = diag.auc;
    document.getElementById('diag-precision').textContent = `${(diag.precision * 100).toFixed(1)}%`;
    document.getElementById('diag-recall').textContent = `${(diag.recall * 100).toFixed(1)}%`;
    document.getElementById('diag-trained-at').textContent = diag.trained_at;
    document.getElementById('diag-rows').textContent = diag.n_training_rows.toLocaleString();

    // Top features
    const featsEl = document.getElementById('diag-features-container');
    if (featsEl && diag.top_features) {
      featsEl.innerHTML = diag.top_features.map(f => `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:rgba(255,255,255,0.03); border-radius:6px; margin-bottom:6px; font-size:12.5px;">
          <span>${f.feature}</span>
          <span style="font-weight:600; color:#2dd4bf;">${f.importance.toFixed(4)}</span>
        </div>
      `).join('');
    }

    loadSettingsUsers();
  } catch (err) {
    console.error('Error loading diagnostics:', err);
  }
}

async function loadSettingsUsers() {
  const tbody = document.getElementById('settings-users-tbody');
  if (!tbody) return;

  try {
    const users = await API.listUsers();
    tbody.innerHTML = users.map(u => `
      <tr>
        <td><code style="color:#2dd4bf;">${u.username}</code></td>
        <td><b>${u.name}</b></td>
        <td>${u.email}</td>
        <td><span class="badge ${u.role === 'Administrator' ? 'badge-high' : 'badge-low'}">${u.role}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" style="padding:3px 8px; font-size:11px;" onclick="deleteUserAccount('${u.username}')">
            Delete
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error loading users:', err);
  }
}

window.deleteUserAccount = async function(username) {
  if (!confirm(`Are you sure you want to delete user account '${username}'?`)) return;
  try {
    await API.deleteUser(username);
    showToast(`User '${username}' deleted`, 'success');
    loadSettingsUsers();
  } catch (err) {
    showToast(`Failed to delete user: ${err.message}`, 'error');
  }
};

// ----------------------------------------------------------------------------- Utilities: Toast
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ')}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

