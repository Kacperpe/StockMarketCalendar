/* ── State ───────────────────────────────────────────────────────────────── */
let apiKey         = null;
let ws             = null;
let wsReconnectTimer  = null;
let equityChart       = null;
let overviewInterval  = null;
let activeBroker      = 'mt5';   // 'mt5' | 'ctrader'
let updateCheckTimer  = null;

/* ── Init ────────────────────────────────────────────────────────────────── */
window.addEventListener('DOMContentLoaded', async () => {
  try {
  document.getElementById('show-pass-btn').addEventListener('click', () => {
    const inp = document.getElementById('inp-password');
    inp.type = inp.type === 'password' ? 'text' : 'password';
  });
  document.getElementById('connect-btn').addEventListener('click', handleConnect);
  ['inp-login', 'inp-server', 'inp-password'].forEach(id =>
    document.getElementById(id).addEventListener('keydown', e => {
      if (e.key === 'Enter') handleConnect();
    })
  );
  document.getElementById('logout-btn').addEventListener('click', handleLogout);
  document.getElementById('stats-load-btn').addEventListener('click', loadFullStats);
  await checkForUpdates();
  updateCheckTimer = setInterval(checkForUpdates, 10 * 60 * 1000);

  // ── Broker tab switching ────────────────────────────────────────────────
  document.querySelectorAll('.broker-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.broker-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeBroker = btn.dataset.broker;
      document.getElementById('form-mt5').classList.toggle('hidden', activeBroker !== 'mt5');
      document.getElementById('form-ct').classList.toggle('hidden',  activeBroker !== 'ctrader');
      document.getElementById('login-error').classList.add('hidden');
    });
  });

  // ── cTrader form wiring ─────────────────────────────────────────────────
  document.getElementById('ct-show-secret').addEventListener('click', () => {
    const inp = document.getElementById('ct-client-secret');
    inp.type = inp.type === 'password' ? 'text' : 'password';
  });
  document.getElementById('ct-auth-btn').addEventListener('click', handleCtAuth);
  document.getElementById('ct-connect-btn').addEventListener('click', handleCtConnect);

  // ── Saved cTrader profiles ──────────────────────────────────────────────
  document.getElementById('ct-remember-checkbox').addEventListener('change', e => {
    document.getElementById('ct-remember-name-row').classList.toggle('hidden', !e.target.checked);
  });
  document.getElementById('ct-saved-logins-select').addEventListener('change', async () => {
    const name = document.getElementById('ct-saved-logins-select').value;
    if (name) await applyCtSavedLogin(name);
  });
  document.getElementById('ct-saved-del-btn').addEventListener('click', async () => {
    const name = document.getElementById('ct-saved-logins-select').value;
    if (!name) { showLoginError('Wybierz profil do usunięcia.'); return; }
    if (!confirm(`Usunąć zapisany profil „${name}"?`)) return;
    await deleteCtSavedLogin(name);
  });
  await loadCtSavedLogins();

  // ── Saved login profiles ────────────────────────────────────────────────
  document.getElementById('remember-checkbox').addEventListener('change', e => {
    document.getElementById('remember-name-row').classList.toggle('hidden', !e.target.checked);
  });
  document.getElementById('saved-logins-select').addEventListener('change', async () => {
    const name = document.getElementById('saved-logins-select').value;
    if (name) await applySavedLogin(name);
  });
  document.getElementById('saved-del-btn').addEventListener('click', async () => {
    const name = document.getElementById('saved-logins-select').value;
    if (!name) { showLoginError('Wybierz konto do usunięcia.'); return; }
    if (!confirm(`Usunąć zapisane konto „${name}"?`)) return;
    await deleteSavedLogin(name);
  });
  await loadSavedLogins();

  const stored = sessionStorage.getItem('mt5_token');
  if (stored) {
    const ok = await validateToken(stored);
    if (ok) { apiKey = stored; showDashboard(); return; }
    sessionStorage.removeItem('mt5_token');
  }
  showLogin();
  } catch (err) {
    document.body.innerHTML = `<div style="color:#f85149;background:#161b22;padding:40px;font-family:monospace;font-size:14px;">
      <b>Błąd inicjalizacji strony:</b><br><br>${err.message}<br><br>
      <small>Upewnij się że otwierasz stronę przez: <b>http://localhost:8000</b><br>
      (nie otwieraj pliku index.html bezpośrednio!)</small>
    </div>`;
  }
});

/* ── Auth ────────────────────────────────────────────────────────────────── */
async function validateToken(token) {
  try {
    const res = await fetch('/account', { headers: { 'X-API-Key': token } });
    return res.ok;
  } catch { return false; }
}

function handleAuthExpired() {
  sessionStorage.removeItem('mt5_token');
  apiKey = null;
  activeBroker = 'mt5';
  disconnectWs();
  clearInterval(overviewInterval);
  showLogin();
  showLoginError('Sesja wygasła. Zaloguj się ponownie.');
}

async function handleConnect() {
  const login    = document.getElementById('inp-login').value.trim();
  const server   = document.getElementById('inp-server').value.trim();
  const password = document.getElementById('inp-password').value;
  const btn      = document.getElementById('connect-btn');

  if (!login || !server || !password) { showLoginError('Wypełnij wszystkie pola.'); return; }

  btn.textContent = 'Łączenie…';
  btn.disabled    = true;
  document.getElementById('login-error').classList.add('hidden');

  try {
    const res  = await fetch('/auth/connect', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ login: parseInt(login), server, password }),
    });
    const data = await res.json();

    if (data.ok) {
      const rememberCb = document.getElementById('remember-checkbox');
      if (rememberCb.checked) {
        const rememberName = document.getElementById('remember-name').value.trim()
          || `${login} · ${server}`;
        await saveLoginCredentials(rememberName, parseInt(login), server, password);
        rememberCb.checked = false;
        document.getElementById('remember-name-row').classList.add('hidden');
        document.getElementById('remember-name').value = '';
      }
      apiKey = data.token;
      sessionStorage.setItem('mt5_token', apiKey);
      showDashboard(data);
    } else {
      showLoginError(data.error || 'Błąd połączenia z MT5.');
    }
  } catch {
    showLoginError('Nie można połączyć z serwerem.');
  } finally {
    btn.textContent = 'Połącz z MT5';
    btn.disabled    = false;
  }
}

async function handleLogout() {
  try { await fetch('/auth/logout', { method: 'POST', headers: { 'X-API-Key': apiKey } }); } catch {}
  sessionStorage.removeItem('mt5_token');
  apiKey = null;
  activeBroker = 'mt5';
  disconnectWs();
  clearInterval(overviewInterval);
  showLogin();
}

/* ── Saved login profiles ─────────────────────────────────────────────────── */
async function loadSavedLogins() {
  try {
    const res  = await fetch('/auth/saved-logins');
    const data = await res.json();
    const select = document.getElementById('saved-logins-select');
    select.innerHTML = '<option value="">\uD83D\uDCC2 Wybierz zapisane konto\u2026</option>';
    data.forEach(entry => {
      const opt = document.createElement('option');
      opt.value       = entry.name;
      opt.textContent = `${entry.name}  (${entry.login} \u00B7 ${entry.server})`;
      select.appendChild(opt);
    });
    document.getElementById('saved-logins-row').classList.toggle('hidden', data.length === 0);
  } catch { /* server not ready yet — ignore */ }
}

async function applySavedLogin(name) {
  try {
    const res = await fetch(`/auth/saved-logins/${encodeURIComponent(name)}`);
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('inp-login').value    = data.login;
    document.getElementById('inp-server').value   = data.server;
    document.getElementById('inp-password').value = data.password;
  } catch {}
}

async function deleteSavedLogin(name) {
  try {
    const res = await fetch(`/auth/saved-logins/${encodeURIComponent(name)}`, { method: 'DELETE' });
    if (res.ok) {
      await loadSavedLogins();
      document.getElementById('inp-login').value    = '';
      document.getElementById('inp-server').value   = '';
      document.getElementById('inp-password').value = '';
    }
  } catch {}
}

async function saveLoginCredentials(name, login, server, password) {
  try {
    await fetch('/auth/saved-logins', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ name, login, server, password }),
    });
    await loadSavedLogins();
  } catch {}
}

/* ── Saved cTrader profiles ───────────────────────────────────────────────── */
async function loadCtSavedLogins() {
  try {
    const res  = await fetch('/auth/saved-ct-logins');
    const data = await res.json();
    const select = document.getElementById('ct-saved-logins-select');
    select.innerHTML = '<option value="">\uD83D\uDCC2 Wybierz zapisany profil\u2026</option>';
    data.forEach(entry => {
      const opt = document.createElement('option');
      opt.value       = entry.name;
      opt.textContent = `${entry.name}  (${entry.client_id})`;
      select.appendChild(opt);
    });
    document.getElementById('ct-saved-logins-row').classList.toggle('hidden', data.length === 0);
  } catch {}
}

async function applyCtSavedLogin(name) {
  try {
    const res = await fetch(`/auth/saved-ct-logins/${encodeURIComponent(name)}`);
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('ct-client-id').value     = data.client_id;
    document.getElementById('ct-client-secret').value = data.client_secret;
  } catch {}
}

async function deleteCtSavedLogin(name) {
  try {
    const res = await fetch(`/auth/saved-ct-logins/${encodeURIComponent(name)}`, { method: 'DELETE' });
    if (res.ok) {
      await loadCtSavedLogins();
      document.getElementById('ct-client-id').value     = '';
      document.getElementById('ct-client-secret').value = '';
    }
  } catch {}
}

async function saveCtLoginCredentials(name, clientId, clientSecret) {
  try {
    await fetch('/auth/saved-ct-logins', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ name, client_id: clientId, client_secret: clientSecret }),
    });
    await loadCtSavedLogins();
  } catch {}
}

/* ── cTrader auth ─────────────────────────────────────────────────────── */
async function handleCtAuth() {
  const clientId     = document.getElementById('ct-client-id').value.trim();
  const clientSecret = document.getElementById('ct-client-secret').value.trim();
  const btn          = document.getElementById('ct-auth-btn');

  if (!clientId || !clientSecret) { showLoginError('Wpisz Client ID i Client Secret.'); return; }

  btn.textContent = 'Przekierowywanie…';
  btn.disabled    = true;
  document.getElementById('login-error').classList.add('hidden');

  try {
    const res  = await fetch('/auth/ctrader/authorize', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
    });
    const data = await res.json();
    if (!data.ok) { showLoginError(data.error || 'Błąd inicjalizacji OAuth'); return; }

    // Save credentials if requested
    const rememberCb = document.getElementById('ct-remember-checkbox');
    if (rememberCb.checked) {
      const rememberName = document.getElementById('ct-remember-name').value.trim()
        || clientId;
      await saveCtLoginCredentials(rememberName, clientId, clientSecret);
      rememberCb.checked = false;
      document.getElementById('ct-remember-name-row').classList.add('hidden');
      document.getElementById('ct-remember-name').value = '';
    }

    // Open Spotware login popup
    const popup = window.open(data.auth_url, 'spotware_auth',
      'width=520,height=640,menubar=no,toolbar=no,location=yes,status=no');

    btn.textContent = 'Czekam na autoryzację…';

    // Poll until access token is available
    const poll = setInterval(async () => {
      try {
        const sr = await fetch('/auth/ctrader/token-status');
        const sd = await sr.json();
        if (sd.ready) {
          clearInterval(poll);
          if (popup && !popup.closed) popup.close();
          await loadCtAccounts();
        }
      } catch { /* keep polling */ }
    }, 1500);

  } catch {
    showLoginError('Błąd połączenia z serwerem.');
  } finally {
    btn.textContent = 'Autoryzuj przez Spotware';
    btn.disabled    = false;
  }
}

async function loadCtAccounts() {
  try {
    const res   = await fetch('/auth/ctrader/accounts-pre');
    const data  = await res.json();
    if (!data.ok || !data.accounts?.length) {
      showLoginError(data.error || 'Brak kont na tym tokenie.');
      return;
    }
    const select = document.getElementById('ct-account-list');
    select.innerHTML = data.accounts.map(a =>
      `<option value="${a.id}" data-is-live="${a.is_live ? '1' : '0'}">${a.broker} — ${a.id} (${a.is_live ? 'LIVE' : 'DEMO'})</option>`
    ).join('');
    document.getElementById('ct-account-row').classList.remove('hidden');
  } catch {
    showLoginError('Nie można załadować listy kont.');
  }
}

async function handleCtConnect() {
  const select    = document.getElementById('ct-account-list');
  const accountId = parseInt(select.value);
  const selected  = select.options[select.selectedIndex];
  const isLive    = (selected?.dataset?.isLive || '0') === '1';
  const btn       = document.getElementById('ct-connect-btn');
  if (!accountId) return;

  btn.textContent = 'Łączenie…';
  btn.disabled    = true;
  document.getElementById('login-error').classList.add('hidden');

  try {
    const res  = await fetch('/auth/ctrader/connect', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ account_id: accountId, is_live: isLive }),
    });
    const data = await res.json();
    if (data.ok) {
      apiKey       = data.token;
      activeBroker = 'ctrader';
      sessionStorage.setItem('mt5_token', apiKey);
      showDashboard(data);
    } else {
      showLoginError(data.error || 'Błąd połączenia z cTrader.');
    }
  } catch {
    showLoginError('Nie można połączyć z serwerem.');
  } finally {
    btn.textContent = 'Połącz z cTrader';
    btn.disabled    = false;
  }
}

function showLoginError(msg) {
  const errEl = document.getElementById('login-error');
  errEl.textContent = msg;
  errEl.classList.remove('hidden');
}

/* ── Screens ─────────────────────────────────────────────────────────────── */
async function checkForUpdates() {
  try {
    const res = await fetch('/api/check-update');
    if (!res.ok) return;

    const data = await res.json();
    if (data.update_available) {
      showUpdateBanner(data.local || 'unknown', data.remote || 'unknown');
    } else {
      hideUpdateBanner();
    }
  } catch {
    // Ignore temporary connectivity issues.
  }
}

function showUpdateBanner(local, remote) {
  let banner = document.getElementById('update-banner');
  if (!banner) {
    banner = document.createElement('div');
    banner.id = 'update-banner';
    banner.className = 'update-banner';
    document.body.prepend(banner);
  }

  banner.innerHTML = `
    <div class="update-banner-text">
      Dostępna nowa wersja <strong>${escapeHtml(remote)}</strong> (masz ${escapeHtml(local)}).
    </div>
    <div class="update-banner-actions">
      <button id="update-now-btn" class="update-btn-primary">Aktualizuj teraz</button>
      <button id="update-hide-btn" class="update-btn-secondary">Ukryj</button>
    </div>
    <div id="update-status" class="update-banner-status"></div>
  `;

  banner.querySelector('#update-now-btn')?.addEventListener('click', doUpdate);
  banner.querySelector('#update-hide-btn')?.addEventListener('click', hideUpdateBanner);
}

function hideUpdateBanner() {
  document.getElementById('update-banner')?.remove();
}

function setUpdateStatus(message, isError = false) {
  const status = document.getElementById('update-status');
  if (!status) return;
  status.textContent = message;
  status.classList.toggle('error', isError);
}

async function doUpdate() {
  const btn = document.getElementById('update-now-btn');
  if (!btn) return;

  btn.disabled = true;
  btn.textContent = 'Aktualizacja...';
  setUpdateStatus('Pobieram najnowsze zmiany...');

  try {
    const res = await fetch('/api/update', { method: 'POST' });
    const data = await res.json();

    if (data.success) {
      setUpdateStatus('Aktualizacja zakończona. Odświeżam aplikację...');
      setTimeout(() => location.reload(), 700);
      return;
    }
    setUpdateStatus(data.output || 'Aktualizacja nie powiodła się.', true);
  } catch {
    setUpdateStatus('Błąd podczas łączenia z API aktualizacji.', true);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Aktualizuj teraz';
  }
}

function showLogin() {
  document.getElementById('login-screen').classList.remove('hidden');
  document.getElementById('dashboard').classList.add('hidden');
}

async function showDashboard(initialData = null) {
  document.getElementById('login-screen').classList.add('hidden');
  document.getElementById('dashboard').classList.remove('hidden');

  if (initialData) {
    setText('account-name',   initialData.name   || '—');
    setText('account-server', `${initialData.server || '—'} · ${initialData.currency || '—'}`);
  }

  initChart();
  connectWs();
  const now = new Date();
  calYear  = now.getFullYear();
  calMonth = now.getMonth() + 1;
  await Promise.all([loadOverview(), loadEquityCurve(), loadFullStats()]);
  overviewInterval = setInterval(loadOverview, 5000);
  loadCalendar();
  initMenuDrawer();
}

/* ── Menu Drawer ─────────────────────────────────────────────────────────── */
function initMenuDrawer() {
  const btn     = document.getElementById('hamburger-btn');
  const drawer  = document.getElementById('menu-drawer');
  const overlay = document.getElementById('menu-overlay');
  const closeBtn = document.getElementById('menu-close-btn');

  function openDrawer()  {
    drawer.classList.remove('hidden');
    overlay.classList.remove('hidden');
    // Show CT account switcher only when cTrader is active
    const ctSection = document.getElementById('ct-switch-section');
    if (activeBroker === 'ctrader') {
      ctSection.classList.remove('hidden');
      loadCtAccountsForSwitch();
    } else {
      ctSection.classList.add('hidden');
    }
  }
  function closeDrawer() { drawer.classList.add('hidden');    overlay.classList.add('hidden'); }

  btn?.addEventListener('click', openDrawer);
  closeBtn?.addEventListener('click', closeDrawer);
  overlay?.addEventListener('click', closeDrawer);

  // ── Theme ──────────────────────────────────────────────────────────────
  const THEMES = {
    dark: {
      '--bg': '#0d1117', '--surface': '#161b22', '--border': '#30363d',
      '--text': '#e6edf3', '--muted': '#8b949e', '--green': '#3fb950',
      '--red': '#f85149', '--blue': '#388bfd',
      '--cal-pos-bg': '#0d2318', '--cal-pos-border': '#1a4731',
      '--cal-neg-bg': '#220d0d', '--cal-neg-border': '#5c1a1a',
      '--cal-we-bg': '#08080f', '--cal-we-border': '#1c1c28', '--cal-we-day-color': '#4a4a5e',
    },
    light: {
      '--bg':      '#F0F0F0',
      '--surface': '#FFFFFF',
      '--border':  '#DDDDDD',
      '--text':    '#333333',
      '--muted':   '#888888',
      '--green':   '#2E7D32',
      '--red':     '#C62828',
      '--blue':    '#0969da',
      '--cal-pos-bg': '#E8F5E9', '--cal-pos-border': '#6BBF7A',
      '--cal-neg-bg': '#FFEBEE', '--cal-neg-border': '#EF9A9A',
      '--cal-we-bg': '#E8E8E8', '--cal-we-border': '#CCCCCC', '--cal-we-day-color': '#BBBBBB',
    },
  };

  function applyThemeVars(vars) {
    const root = document.documentElement;
    Object.entries(vars).forEach(([k, v]) => root.style.setProperty(k, v));
  }

  function setActiveThemeBtn(name) {
    document.querySelectorAll('.theme-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.theme === name);
    });
  }

  function applyTheme(name) {
    if (name === 'dark' || name === 'light') {
      applyThemeVars(THEMES[name]);
    } else if (name === 'custom') {
      applyCustomTheme();
    }
    localStorage.setItem('mt5_theme', name);
    setActiveThemeBtn(name);
    const customRow = document.getElementById('custom-theme-row');
    customRow?.classList.toggle('hidden', name !== 'custom');
  }

  function applyCustomTheme() {
    const map = {
      'c-bg':      '--bg',
      'c-surface': '--surface',
      'c-text':    '--text',
      'c-accent':  '--blue',
      'c-green':   '--green',
      'c-red':     '--red',
    };
    const vars = {};
    Object.entries(map).forEach(([id, varName]) => {
      const el = document.getElementById(id);
      if (el) vars[varName] = el.value;
    });
    // derive border from bg slightly lighter
    vars['--border'] = vars['--bg'] ? lightenHex(vars['--bg'], 30) : '#30363d';
    vars['--muted']  = vars['--text'] ? hexWithAlpha(vars['--text'], 0.55) : '#8b949e';
    applyThemeVars(vars);
  }

  function lightenHex(hex, amount) {
    const num = parseInt(hex.slice(1), 16);
    const r = Math.min(255, (num >> 16) + amount);
    const g = Math.min(255, ((num >> 8) & 0xff) + amount);
    const b = Math.min(255, (num & 0xff) + amount);
    return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
  }
  function hexWithAlpha(hex, alpha) {
    // returns a fixed muted color composed of the text hex blended with bg
    return hex; // simplified — just return as-is
  }

  // Load saved custom colors into pickers
  function loadSavedCustom() {
    const saved = localStorage.getItem('mt5_custom_theme');
    if (!saved) return;
    try {
      const c = JSON.parse(saved);
      ['c-bg','c-surface','c-text','c-accent','c-green','c-red'].forEach(id => {
        const el = document.getElementById(id);
        if (el && c[id]) el.value = c[id];
      });
    } catch(e) {}
  }

  function saveCustomColors() {
    const ids = ['c-bg','c-surface','c-text','c-accent','c-green','c-red'];
    const c = {};
    ids.forEach(id => { const el = document.getElementById(id); if (el) c[id] = el.value; });
    localStorage.setItem('mt5_custom_theme', JSON.stringify(c));
  }

  document.querySelectorAll('.theme-btn').forEach(b => {
    b.addEventListener('click', () => applyTheme(b.dataset.theme));
  });

  ['c-bg','c-surface','c-text','c-accent','c-green','c-red'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', () => {
      saveCustomColors();
      applyCustomTheme();
    });
  });

  loadSavedCustom();
  const savedTheme = localStorage.getItem('mt5_theme') || 'dark';
  applyTheme(savedTheme);

  // ── Panel toggles ──────────────────────────────────────────────────────
  const PANELS = [
    { id: 'tog-overview',  panelId: 'panel-overview' },
    { id: 'tog-positions', panelId: 'panel-positions' },
    { id: 'tog-stats',     panelId: 'panel-stats' },
    { id: 'tog-calendar',  panelId: 'panel-calendar' },
  ];

  function applyPanelVisibility(togId, panelId, visible) {
    const panel = document.getElementById(panelId);
    if (panel) panel.classList.toggle('hidden', !visible);
    localStorage.setItem('mt5_panel_' + togId, visible ? '1' : '0');
  }

  PANELS.forEach(({ id, panelId }) => {
    const checkbox = document.getElementById(id);
    if (!checkbox) return;

    // Restore saved state
    const saved = localStorage.getItem('mt5_panel_' + id);
    if (saved === '0') {
      checkbox.checked = false;
      applyPanelVisibility(id, panelId, false);
    }

    checkbox.addEventListener('change', () => {
      applyPanelVisibility(id, panelId, checkbox.checked);
    });
  });

  // ── cTrader account switcher ───────────────────────────────────────────
  document.getElementById('ct-switch-btn').addEventListener('click', handleCtSwitchAccount);
}

/* ── cTrader account switcher ────────────────────────────────────────────── */
async function loadCtAccountsForSwitch() {
  const select = document.getElementById('ct-switch-select');
  const status = document.getElementById('ct-switch-status');
  select.innerHTML = '<option value="">Ładowanie…</option>';
  status.className = 'ct-switch-status hidden';
  try {
    const res  = await fetch('/auth/ctrader/accounts', { headers: { 'X-API-Key': apiKey } });
    const data = await res.json();
    if (!data.ok || !data.accounts?.length) {
      select.innerHTML = '<option value="">Brak dostępnych kont</option>';
      return;
    }
    select.innerHTML = data.accounts.map(a =>
      `<option value="${a.id}" data-is-live="${a.is_live ? '1' : '0'}">${a.broker} — ${a.id} (${a.is_live ? 'LIVE' : 'DEMO'})</option>`
    ).join('');
  } catch {
    select.innerHTML = '<option value="">Błąd ładowania kont</option>';
  }
}

async function handleCtSwitchAccount() {
  const select  = document.getElementById('ct-switch-select');
  const btn     = document.getElementById('ct-switch-btn');
  const status  = document.getElementById('ct-switch-status');
  const accountId = parseInt(select.value);
  const selected  = select.options[select.selectedIndex];
  const isLive    = (selected?.dataset?.isLive || '0') === '1';
  if (!accountId) return;

  btn.disabled    = true;
  btn.textContent = 'Przełączanie…';
  status.className = 'ct-switch-status hidden';

  try {
    const res  = await fetch('/auth/ctrader/switch-account', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body:    JSON.stringify({ account_id: accountId, is_live: isLive }),
    });
    const data = await res.json();
    if (data.ok) {
      setText('account-name',   data.name   || '—');
      setText('account-server', `${data.server || '—'} · ${data.currency || ''}`);
      status.textContent = '✓ Konto zmienione';
      status.className   = 'ct-switch-status ok';
      // Reload overview data for the new account
      await Promise.all([loadOverview(), loadEquityCurve(), loadFullStats()]);
      loadCalendar();
    } else {
      status.textContent = data.error || 'Błąd przełączania konta';
      status.className   = 'ct-switch-status error';
    }
  } catch {
    status.textContent = 'Nie można połączyć z serwerem';
    status.className   = 'ct-switch-status error';
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Przełącz konto';
  }
}

/* ── Overview stats ──────────────────────────────────────────────────────── */
async function loadOverview() {
  try {
    const res  = await fetch('/overview', { headers: { 'X-API-Key': apiKey } });
    if (res.status === 401) {
      handleAuthExpired();
      return;
    }
    const data = await res.json();
    if (!res.ok || data.error) {
      await loadOverviewFallback();
      return;
    }
    const cur = data.currency || '';

    setText('top-equity', fmtMoney(data.equity, cur));

    const gEl = document.getElementById('top-growth');
    gEl.textContent = fmtPct(data.gain_pct);
    gEl.className   = `card-value ${cls(data.gain_pct)}`;

    setText('top-deposit',     fmtMoney(data.deposits, cur));
    setText('top-withdrawals', data.withdrawals > 0 ? `\u2212${fmtMoney(data.withdrawals, cur)}` : `\u2014 ${cur}`);

    const gainEl = document.getElementById('s-gain');
    gainEl.textContent = fmtPct(data.gain_pct);
    gainEl.className   = `stat-value ${cls(data.gain_pct)}`;

    const dailyEl = document.getElementById('s-daily');
    dailyEl.textContent = `${fmtPnl(data.daily_avg)} ${cur}`;
    dailyEl.className   = `stat-value ${cls(data.daily_avg)}`;

    const monthEl = document.getElementById('s-monthly');
    monthEl.textContent = `${fmtPnl(data.monthly_avg)} ${cur}`;
    monthEl.className   = `stat-value ${cls(data.monthly_avg)}`;

    setText('s-dd',        `${NUM.format(data.max_drawdown_pct)}%`);
    setText('s-balance',   fmtMoney(data.balance, cur));
    setText('s-equity-sb', fmtMoney(data.equity,  cur));

    const profEl = document.getElementById('s-profit');
    profEl.textContent = `${fmtPnl(data.total_profit)} ${cur}`;
    profEl.className   = `stat-value ${cls(data.total_profit)}`;

  } catch {
    await loadOverviewFallback();
  }
}

async function loadOverviewFallback() {
  try {
    const res = await fetch('/snapshot', { headers: { 'X-API-Key': apiKey } });
    if (res.status === 401) {
      handleAuthExpired();
      return;
    }
    if (!res.ok) return;
    const data = await res.json();
    const account = data.account || {};
    const cur = account.currency || '';
    const bal = Number(account.balance || 0);
    const eq = Number(account.equity || bal);
    const fallbackGrowth = bal > 0 ? ((eq - bal) / bal) * 100 : 0;

    setText('top-equity', fmtMoney(eq, cur));
    setText('top-deposit', fmtMoney(bal, cur));
    setText('top-withdrawals', `${fmtMoney(0, cur)}`);

    const gEl = document.getElementById('top-growth');
    if (gEl) {
      gEl.textContent = fmtPct(fallbackGrowth);
      gEl.className = `card-value ${cls(fallbackGrowth)}`;
    }

    setText('s-balance', fmtMoney(bal, cur));
    setText('s-equity-sb', fmtMoney(eq, cur));
  } catch {
    // no-op
  }
}

/* ── Full equity curve ───────────────────────────────────────────────────── */
async function loadEquityCurve() {
  try {
    setText('chart-pts', 'Ładowanie…');
    const res    = await fetch('/equity-curve', { headers: { 'X-API-Key': apiKey } });
    if (res.status === 401) {
      handleAuthExpired();
      return;
    }
    const points = await res.json();
    if (!Array.isArray(points) || !points.length) { setText('chart-pts', 'Brak historii'); return; }

    setText('chart-pts', `${points.length} punktów`);
    const labels = points.map(p => {
      const d = new Date(p.ts.endsWith('Z') ? p.ts : p.ts + 'Z');
      return d.toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit', year: '2-digit' });
    });
    const values = points.map(p => p.balance);
    const baseline = values[0];

    // Per-segment colors: green above baseline, red below
    const segColor = (y0, y1) => ((y0 + y1) / 2) >= baseline ? '#3fb950' : '#f85149';
    const segBg    = (y0, y1) => ((y0 + y1) / 2) >= baseline
      ? 'rgba(63,185,80,0.09)' : 'rgba(248,81,73,0.09)';

    equityChart.data.labels           = labels;
    equityChart.data.datasets[0].data = values;
    equityChart.data.datasets[0].borderColor     = '#3fb950'; // fallback
    equityChart.data.datasets[0].backgroundColor = 'rgba(63,185,80,0.09)';
    equityChart.data.datasets[0].segment = {
      borderColor:     ctx => segColor(ctx.p0.parsed.y, ctx.p1.parsed.y),
      backgroundColor: ctx => segBg(ctx.p0.parsed.y, ctx.p1.parsed.y),
    };

    // Horizontal baseline reference line
    equityChart.options.plugins.annotation = undefined; // no annotation plugin needed
    equityChart.options.scales.y.grid.color = ctx =>
      ctx.tick.value === baseline
        ? 'rgba(180,180,180,0.35)'
        : 'rgba(128,128,128,0.12)';

    equityChart.update('none');
  } catch {}
}

/* ── Chart init ──────────────────────────────────────────────────────────── */
function initChart() {
  Chart.defaults.color       = '#8b949e';
  Chart.defaults.borderColor = '#30363d';
  Chart.defaults.font.family = 'Segoe UI, system-ui, sans-serif';
  Chart.defaults.font.size   = 12;

  if (equityChart) { equityChart.destroy(); equityChart = null; }

  equityChart = new Chart(document.getElementById('equity-chart'), {
    type: 'line',
    data: { labels: [], datasets: [{
      label: 'Balance / Equity', data: [],
      borderColor: '#3fb950', backgroundColor: 'rgba(63,185,80,0.09)',
      borderWidth: 2, pointRadius: 0, tension: 0.3, fill: true,
      segment: {},
    }]},
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: { ticks: { maxTicksLimit: 10, maxRotation: 0 }, grid: { color: 'rgba(128,128,128,0.12)' } },
        y: { ticks: { maxTicksLimit: 8 }, grid: { color: 'rgba(128,128,128,0.12)' } },
      },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ${NUM.format(ctx.parsed.y)}` } },
      },
    },
  });
}

/* ── WebSocket ───────────────────────────────────────────────────────────── */
function connectWs() {
  disconnectWs();
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/live?key=${encodeURIComponent(apiKey)}`);
  ws.onopen    = () => { setWsDot(true);  clearTimeout(wsReconnectTimer); };
  ws.onmessage = ({ data }) => { try { renderSnapshot(JSON.parse(data)); } catch {} };
  ws.onclose   = () => {
    setWsDot(false);
    if (!apiKey) return;
    validateToken(apiKey).then(ok => {
      if (!ok) {
        handleAuthExpired();
        return;
      }
      wsReconnectTimer = setTimeout(connectWs, 3000);
    });
  };
  ws.onerror   = () => ws.close();
}
function disconnectWs() {
  clearTimeout(wsReconnectTimer);
  if (ws) { ws.onclose = null; ws.close(); ws = null; }
  setWsDot(false);
}
function setWsDot(ok) {
  const el = document.getElementById('ws-status');
  el.className = `dot ${ok ? 'connected' : 'disconnected'}`;
  el.title     = ok ? 'Live (WebSocket aktywny)' : 'Rozłączony…';
}
setInterval(() => { if (ws && ws.readyState === WebSocket.OPEN) ws.send('ping'); }, 25000);

/* ── Snapshot renderer ───────────────────────────────────────────────────── */
function renderSnapshot({ account, positions, timestamp }) {
  if (timestamp) {
    const d = new Date(timestamp.endsWith('Z') ? timestamp : timestamp + 'Z');
    setText('last-update', d.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
  }
  if (account) {
    setText('account-name',   account.name   || '—');
    setText('account-server', `${account.server} · ${account.currency}`);
    setText('top-equity', fmtMoney(account.equity, account.currency));
    const fpEl = document.getElementById('floating-pnl');
    if (fpEl) {
      fpEl.textContent = `Floating P&L: ${fmtPnl(account.floating_pnl)} ${account.currency || ''}`;
      fpEl.className   = `muted-sm ${cls(account.floating_pnl)}`;
    }
  }
  renderPositions(positions || []);
}

/* ── Positions table ─────────────────────────────────────────────────────── */
function renderPositions(positions) {
  const tbody = document.getElementById('positions-tbody');
  document.getElementById('positions-count').textContent = positions.length;
  if (!positions.length) {
    tbody.innerHTML = '<tr><td colspan="12" class="empty">Brak otwartych pozycji</td></tr>';
    return;
  }
  tbody.innerHTML = positions.map(p => `
    <tr>
      <td class="neutral">${p.ticket}</td>
      <td><strong>${p.symbol}</strong></td>
      <td class="${p.type === 'BUY' ? 'type-buy' : 'type-sell'}">${p.type}</td>
      <td>${p.volume}</td><td>${p.open_price}</td><td><strong>${p.current_price}</strong></td>
      <td class="neutral">${p.sl || '—'}</td><td class="neutral">${p.tp || '—'}</td>
      <td class="${cls(p.profit_raw)}">${fmtPnl(p.profit_raw)}</td>
      <td class="${cls(p.swap)}">${p.swap !== 0 ? fmtPnl(p.swap) : '—'}</td>
      <td class="${cls(p.pnl_net)}"><strong>${fmtPnl(p.pnl_net)}</strong></td>
      <td class="neutral">${fmtDate(p.open_time)}</td>
    </tr>`).join('');
}

/* ── Myfxbook-style Statistics ───────────────────────────────────────────── */
async function loadFullStats() {
  const btn     = document.getElementById('stats-load-btn');
  const days    = document.getElementById('stats-days').value;
  const content = document.getElementById('stats-content');

  btn.textContent = 'Ładowanie…';
  btn.disabled    = true;
  content.innerHTML = '<p class="empty">Obliczam statystyki…</p>';

  try {
    const res = await fetch(`/statistics/full?days=${days}`, { headers: { 'X-API-Key': apiKey } });
    if (res.status === 401) {
      handleAuthExpired();
      return;
    }
    const d   = await res.json();

    if (d.error) { content.innerHTML = `<p class="empty">${d.error}</p>`; return; }
    const cur = d.currency || '';

    content.innerHTML =
      '<div class="stats-section">'

      /* Top row */
      + '<div class="stats-top-row">'
      + statBig('Gain',   fmtPct(d.gain_pct),            cls(d.gain_pct))
      + statBig('Profit', `${fmtPnl(d.profit)} ${cur}`,   cls(d.profit))
      + statBig('Pips',   (d.pips >= 0 ? '+' : '') + NUM.format(d.pips), cls(d.pips))
      + statBig('Win %',  `${NUM.format(d.win_rate_pct)}%`, d.win_rate_pct >= 50 ? 'positive' : 'negative')
      + statBig('Trades', d.total_trades, '')
      + statBig('Lots',   NUM.format(d.total_lots), '')
      + '</div>'

      /* Profitability bar */
      + '<div class="profit-bar-wrap">'
      + `<div class="profit-bar"><div class="profit-bar-win" style="width:${d.win_rate_pct}%">${NUM.format(d.win_rate_pct)}%</div>`
      + `<div class="profit-bar-loss" style="width:${100 - d.win_rate_pct}%">${NUM.format(100 - d.win_rate_pct)}%</div></div>`
      + `<div class="profit-bar-labels"><span>Zyski (${d.winning_trades})</span><span>Straty (${d.losing_trades})</span></div>`
      + '</div>'

      /* Advanced grid */
      + '<div class="adv-grid">'
      + advRow('Avg Win / Avg Loss',
          `<span class="positive">${fmtPnl(d.avg_win_eur)} ${cur}</span> / <span class="negative">${fmtPnl(d.avg_loss_eur)} ${cur}</span>`)
      + advRow('Avg Win / Loss (pips)',
          `<span class="positive">+${NUM.format(d.avg_win_pips)}</span> / <span class="negative">${NUM.format(d.avg_loss_pips)}</span>`)
      + advRow('Longs Won',
          `<span class="${d.longs_win_pct >= 50 ? 'positive' : 'negative'}">(${d.longs_won}/${d.longs_total}) ${NUM.format(d.longs_win_pct)}%</span>`)
      + advRow('Shorts Won',
          `<span class="${d.shorts_win_pct >= 50 ? 'positive' : 'negative'}">(${d.shorts_won}/${d.shorts_total}) ${NUM.format(d.shorts_win_pct)}%</span>`)
      + advRow('Best Trade',
          `<span class="positive">${fmtPnl(d.best_trade_eur)} ${cur}</span> <span class="muted-sm">/ ${NUM.format(d.best_trade_pips)} pips</span>`
          + (d.best_trade_date ? ` <span class="muted-sm">(${fmtDateShort(d.best_trade_date)})</span>` : ''))
      + advRow('Worst Trade',
          `<span class="negative">${fmtPnl(d.worst_trade_eur)} ${cur}</span> <span class="muted-sm">/ ${NUM.format(d.worst_trade_pips)} pips</span>`
          + (d.worst_trade_date ? ` <span class="muted-sm">(${fmtDateShort(d.worst_trade_date)})</span>` : ''))
      + advRow('Profit Factor',
          d.profit_factor != null
            ? `<span class="${d.profit_factor >= 1 ? 'positive' : 'negative'}">${NUM.format(d.profit_factor)}</span>`
            : '<span class="positive">\u221e</span>')
      + advRow('Std. Deviation', `${NUM.format(d.std_dev)} ${cur}`)
      + advRow('Sharpe Ratio',
          `<span class="${d.sharpe_ratio >= 1 ? 'positive' : d.sharpe_ratio > 0 ? 'neutral' : 'negative'}">${NUM.format(d.sharpe_ratio)}</span>`)
      + advRow('Z-Score',
          `${NUM.format(d.z_score)} <span class="muted-sm">(${NUM.format(d.z_probability)}%)</span>`)
      + advRow('Expectancy',
          `<span class="${cls(d.expectancy_eur)}">${fmtPnl(d.expectancy_eur)} ${cur}</span>`
          + ` <span class="muted-sm">/ ${d.expectancy_pips >= 0 ? '+' : ''}${NUM.format(d.expectancy_pips)} pips</span>`)
      + advRow('Avg. Trade Length', d.avg_trade_fmt || '—')
      + advRow('AHPR / GHPR', `${NUM.format(d.ahpr_pct)}% / ${NUM.format(d.ghpr_pct)}%`)
      + advRow('Gross Profit / Loss',
          `<span class="positive">+${fmtMoney(d.gross_profit, cur)}</span> / <span class="negative">\u2212${fmtMoney(d.gross_loss, cur)}</span>`)
      + '</div></div>';

  } catch {
    content.innerHTML = '<p class="empty" style="color:var(--red)">Błąd podczas ładowania statystyk.</p>';
  } finally {
    btn.textContent = 'Załaduj';
    btn.disabled    = false;
  }
}

function statBig(label, value, colorCls) {
  return `<div class="stat-big"><div class="stat-big-label">${label}</div><div class="stat-big-value ${colorCls}">${value}</div></div>`;
}
function advRow(label, valueHtml) {
  return `<div class="adv-row"><span class="adv-label">${label}</span><span class="adv-value">${valueHtml}</span></div>`;
}

/* ── Helpers ─────────────────────────────────────────────────────────────── */
const NUM = new Intl.NumberFormat('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function fmtMoney(val, currency) {
  if (val == null) return '—';
  return NUM.format(val) + (currency ? ` ${currency}` : '');
}
function fmtPnl(val) {
  if (val == null) return '—';
  return (val > 0 ? '+' : '') + NUM.format(val);
}
function fmtPct(val) {
  if (val == null) return '—';
  return (val > 0 ? '+' : '') + NUM.format(val) + '%';
}
function cls(val) {
  if (val == null || val === 0) return 'neutral';
  return val > 0 ? 'positive' : 'negative';
}
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val != null ? val : '—';
}
function escapeHtml(val) {
  return String(val)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}
function fmtDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
  return d.toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}
function fmtDateShort(iso) {
  if (!iso) return '—';
  const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
  return d.toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit', year: '2-digit' });
}

/* ── Calendar ────────────────────────────────────────────────────────────── */
let calYear  = new Date().getFullYear();
let calMonth = new Date().getMonth() + 1;

const MONTHS_PL = [
  'Styczeń','Luty','Marzec','Kwiecień','Maj','Czerwiec',
  'Lipiec','Sierpień','Wrzesień','Październik','Listopad','Grudzień'
];
const DOW = ['PON','WTO','ŚRO','CZW','PIĄ','SOB','NED'];

async function loadCalendar() {
  const label = document.getElementById('cal-month-label');
  if (label) label.textContent = `${MONTHS_PL[calMonth - 1]} ${calYear}`;

  try {
    const res  = await fetch(`/calendar?year=${calYear}&month=${calMonth}`, { headers: { 'X-API-Key': apiKey } });
    if (res.status === 401) {
      handleAuthExpired();
      return;
    }
    const data = await res.json();
    if (!res.ok) { renderCalendarError(); return; }
    renderCalendar(calYear, calMonth, data);
  } catch (e) {
    renderCalendarError();
  }
}

function renderCalendarError() {
  const el = document.getElementById('cal-content');
  if (el) el.innerHTML = '<p class="empty">Błąd ładowania kalendarza.</p>';
}

function renderCalendar(year, month, data) {
  const el = document.getElementById('cal-content');
  if (!el) return;

  const grid = buildCalGrid(year, month, data.days || {});
  const weeks = data.weeks || {};

  let html = `<div class="cal-grid">`;

  // Nagłówek dni tygodnia
  html += `<div class="cal-header-row">`;
  DOW.forEach((d, i) => {
    const weCls = (i === 5 || i === 6) ? 'cal-dow-weekend' : '';
    html += `<div class="cal-dow ${weCls}">${d}</div>`;
  });
  html += `<div class="cal-dow cal-week-header">Tydzień</div>`;
  html += `</div>`;

  // Wiersze
  grid.forEach((week, wi) => {
    html += `<div class="cal-row">`;
    week.forEach(day => {
      html += renderDayCell(day);
    });
    html += renderWeekCell(wi + 1, weeks[wi + 1]);
    html += `</div>`;
  });

  html += `</div>`;
  el.innerHTML = html;
}

function renderDayCell(day) {
  if (!day || day.dayNum === null) {
    const weCls = day?.weekend ? 'cal-weekend' : '';
    return `<div class="cal-cell cal-cell-empty ${weCls}"></div>`;
  }
  const s = day.stats;
  const hasTrades = s && s.trades > 0;
  const pnl = hasTrades ? s.pnl : 0;
  const weCls    = day.weekend ? 'cal-weekend' : '';
  const colorCls = hasTrades ? (pnl > 0 ? 'cal-pos' : (pnl < 0 ? 'cal-neg' : 'cal-zero')) : '';
  const pnlSign  = pnl > 0 ? '+' : (pnl < 0 ? '-' : '');
  const pnlStr   = hasTrades ? `${pnlSign}€${Math.abs(pnl).toLocaleString('de-DE',{minimumFractionDigits:2,maximumFractionDigits:2})}` : '';

  return `
    <div class="cal-cell ${weCls} ${colorCls}">
      <span class="cal-day-num">${day.dayNum}</span>
      ${hasTrades ? `
        <span class="cal-pnl ${pnl >= 0 ? 'positive' : 'negative'}">${pnlStr}</span>
        <span class="cal-meta">${s.trades} trade${s.trades !== 1 ? 's' : ''}</span>
        <span class="cal-meta">WR: ${s.win_rate.toFixed(1)}%</span>
      ` : ''}
    </div>
  `;
}

function renderWeekCell(weekNum, data) {
  const pnl  = data?.pnl  ?? 0;
  const days = data?.trading_days ?? 0;
  const colorCls  = pnl > 0 ? 'cal-pos' : (pnl < 0 ? 'cal-neg' : 'cal-zero');
  const pnlSign   = pnl > 0 ? '+' : (pnl < 0 ? '-' : '');
  const pnlStr    = `${pnlSign}€${Math.abs(pnl).toLocaleString('de-DE',{minimumFractionDigits:2,maximumFractionDigits:2})}`;
  const pnlClr    = days === 0 || pnl === 0 ? 'neutral' : (pnl > 0 ? 'positive' : 'negative');

  return `
    <div class="cal-cell cal-week-cell ${colorCls}">
      <span class="cal-week-label">Tydz. ${weekNum}</span>
      <span class="cal-pnl ${pnlClr}">${days > 0 ? pnlStr : '€0,00'}</span>
      <span class="cal-meta">${days} ${days === 1 ? 'dzień' : 'dni'}</span>
    </div>
  `;
}

function buildCalGrid(year, month, dayData) {
  const firstDay    = new Date(year, month - 1, 1);
  const daysInMonth = new Date(year, month, 0).getDate();

  // Offset Monday = 0 … Sunday = 6
  let startOffset = firstDay.getDay() - 1;
  if (startOffset < 0) startOffset = 6;

  const cells = [];
  for (let i = 0; i < startOffset; i++) {
    const col = i % 7;
    cells.push({ dayNum: null, stats: null, weekend: col === 5 || col === 6 });
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const col = cells.length % 7;
    const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    cells.push({ dayNum: d, stats: dayData[dateStr] ?? null, weekend: col === 5 || col === 6 });
  }

  while (cells.length % 7 !== 0) {
    const col = cells.length % 7;
    cells.push({ dayNum: null, stats: null, weekend: col === 5 || col === 6 });
  }

  const weeks = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));
  return weeks;
}

// Nawigacja miesiącami
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('cal-prev-btn')?.addEventListener('click', () => {
    calMonth--;
    if (calMonth < 1) { calMonth = 12; calYear--; }
    loadCalendar();
  });
  document.getElementById('cal-next-btn')?.addEventListener('click', () => {
    calMonth++;
    if (calMonth > 12) { calMonth = 1; calYear++; }
    loadCalendar();
  });
  document.getElementById('cal-today-btn')?.addEventListener('click', () => {
    const now = new Date();
    calYear  = now.getFullYear();
    calMonth = now.getMonth() + 1;
    loadCalendar();
  });
});

