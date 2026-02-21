<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="csrf-token" content="{{ csrf_token() if csrf_token else '' }}">

  <title>{% block title %}TVS NIRIX{% endblock %}</title>

  <!-- Bootstrap -->
  <link
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
    rel="stylesheet">

  <style>
    :root {
      --tvs-blue: #143B68;
      --tvs-blue-light: #0d6efd;
      --shadow: 0 4px 16px rgba(0,0,0,0.25);

      --bg-main: #f3f4f6;
      --text-main: #000;
      --drawer-bg: #ffffff;
      --drawer-text: #111;
    }

    body.dark {
      --bg-main: #0f172a;
      --text-main: #e2e8f0;
      --drawer-bg: #1e293b;
      --drawer-text: #e2e8f0;
    }

    body {
      background: var(--bg-main);
      color: var(--text-main);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      transition: background 0.25s, color 0.25s;
    }

    .btn-tvs {
      background-color: var(--tvs-blue);
      color: #fff;
      border: none;
      font-weight: 600;
    }

    .btn-tvs:hover {
      background-color: #0d2c4d;
      color: #fff;
    }

    main {
      padding-top: {% if user %}96px{% else %}40px{% endif %};
      padding-bottom: 60px;
    }

    header.header-bar {
      position: fixed;
      top: 0; left: 0; right: 0;
      background: var(--tvs-blue);
      padding: 8px 16px 6px;
      box-shadow: var(--shadow);
      z-index: 1000;
    }

    footer.footer-bar {
      position: fixed;
      bottom: 0; left: 0; right: 0;
      background: var(--tvs-blue);
      color: #fff;
      padding: 6px 16px;
      text-align: center;
      font-size: 12px;
    }

    .top-nav .nav-link {
      color: #e5f0ff;
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 0.85rem;
      font-weight: 500;
    }

    .top-nav .nav-link.active {
      background: var(--tvs-blue-light);
      color: #fff;
    }

    .drawer-menu {
      position: fixed;
      top: 0; right: -290px;
      width: 260px;
      height: 100%;
      background: var(--drawer-bg);
      color: var(--drawer-text);
      padding: 20px;
      box-shadow: var(--shadow);
      z-index: 2000;
      transition: right 0.3s;
    }
    .drawer-menu.open { right: 0; }

    .drawer-backdrop {
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(0,0,0,0.45);
      opacity: 0;
      visibility: hidden;
      z-index: 1500;
      transition: opacity 0.25s;
    }
    .drawer-backdrop.show {
      opacity: 1;
      visibility: visible;
    }

    .drawer-header {
      font-size: 13px;
      opacity: 0.7;
      margin-top: 14px;
    }

    .drawer-item {
      padding: 10px 0;
      border-bottom: 1px solid rgba(150,150,150,0.25);
      cursor: pointer;
    }

    .hamburger {
      width: 28px;
      cursor: pointer;
    }
    .hamburger span {
      display: block;
      height: 3px;
      margin: 5px 0;
      background: #fff;
      border-radius: 3px;
    }
    
    /* Toast notifications - Minimal addition */
    .toast-container {
      position: fixed;
      top: 100px;
      right: 20px;
      z-index: 9999;
    }
    .toast {
      background: var(--drawer-bg);
      color: var(--drawer-text);
      border-left: 4px solid;
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 8px;
      box-shadow: var(--shadow);
      min-width: 300px;
    }
    .toast.success { border-left-color: #10b981; }
    .toast.error { border-left-color: #ef4444; }
    .toast.warning { border-left-color: #f59e0b; }
    .toast.info { border-left-color: #3b82f6; }
  </style>

  {% block head %}{% endblock %}
</head>

{% set effective_theme =
     user.theme if user and user.theme
     else default_theme %}

<body class="{{ 'dark' if effective_theme == 'dark' else '' }}">

<!-- Toast notifications container - Minimal addition -->
<div id="toast-container" class="toast-container"></div>

{% if user %}
<div id="drawer_backdrop" class="drawer-backdrop" onclick="toggleDrawer()"></div>

<div id="drawer_menu" class="drawer-menu">

  <!-- USER INFO -->
  <div class="drawer-header">User</div>
  <div class="drawer-item">
    <strong>{{ user.name }}</strong><br>
    <small>ID: {{ user.employee_id }}</small><br>
    <small class="text-muted">{{ user.role|capitalize }}</small>
  </div>

  <!-- PREFERENCES -->
  <div class="drawer-header">Preferences</div>
  <div class="drawer-item" onclick="toggleThemeDB()">
    Theme:
    <span id="theme_label">{{ effective_theme|capitalize }}</span>
  </div>

  <!-- ADMIN / SUPER ADMIN -->
  {% if user.role in ["admin", "super_admin"] %}
    <div class="drawer-header">Administration</div>

    <div class="drawer-item"
         onclick="location.href='{{ url_for("admin.admin_dashboard") }}'">
      Admin Dashboard
    </div>

    <div class="drawer-item"
         onclick="location.href='{{ url_for("admin.admin_users") }}'">
      User Management
    </div>

    <div class="drawer-item"
         onclick="location.href='{{ url_for("admin.admin_vehicles") }}'">
      Vehicle Management
    </div>

    <div class="drawer-item"
         onclick="location.href='{{ url_for("admin.admin_tests") }}'">
      Test Management
    </div>

    {% if user.role == "super_admin" %}
      <div class="drawer-item"
           onclick="location.href='{{ url_for("admin.admin_roles") }}'">
        Role Management
      </div>

      <div class="drawer-item"
           onclick="location.href='{{ url_for("admin.admin_config") }}'">
        System Configuration
      </div>
    {% endif %}

    <div class="drawer-item"
         onclick="location.href='{{ url_for("admin.admin_logs") }}'">
      Logs Management
    </div>
  {% endif %}

  <!-- LOGOUT -->
  <div class="drawer-item text-danger"
       onclick="location.href='{{ url_for("logout") }}'">
    Sign Out
  </div>
</div>

<header class="header-bar">
  <div class="d-flex justify-content-between align-items-center">
    <div class="d-flex align-items-center gap-2">
      <img src="{{ url_for('vehicle_image', filename='Nirix_Name_Logo.png') }}" style="height:32px;">
      <span class="text-white fw-bold">NIRIX Diagnostics</span>
    </div>

    <div class="d-flex align-items-center gap-3">
      <div class="hamburger" onclick="toggleDrawer()">
        <span></span><span></span><span></span>
      </div>
    </div>
  </div>

  <!-- MAIN NAV -->
  <ul class="nav top-nav mt-2">
    <li class="nav-item">
      <a class="nav-link {% if request.endpoint=='dashboard' %}active{% endif %}"
         href="{{ url_for('dashboard') }}">Dashboard</a>
    </li>

    <li class="nav-item">
      <a class="nav-link
        {% if request.endpoint in ['tests_root','tests_page'] %}active{% endif %}"
        href="{{ url_for('tests_root') }}">
        Tests
      </a>
    </li>

    <li class="nav-item">
      <a class="nav-link {% if request.endpoint=='logs_page' %}active{% endif %}"
         href="{{ url_for('logs_page') }}">Logs</a>
    </li>

    <li class="nav-item">
      <a class="nav-link {% if request.endpoint=='downloads_page' %}active{% endif %}"
         href="{{ url_for('downloads_page') }}">Downloads</a>
    </li>
  </ul>
</header>
{% endif %}

<main class="container-fluid">
  {% block content %}{% endblock %}
</main>

<footer class="footer-bar">
  © 2025 TVS NIRIX – Internal Diagnostic Tool
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

{% if user %}
<script>
function toggleDrawer() {
  document.getElementById("drawer_menu").classList.toggle("open");
  document.getElementById("drawer_backdrop").classList.toggle("show");
}

async function toggleThemeDB() {
  const isDark = document.body.classList.contains("dark");
  const newTheme = isDark ? "light" : "dark";

  document.body.classList.toggle("dark");
  document.getElementById("theme_label").textContent =
    newTheme.charAt(0).toUpperCase() + newTheme.slice(1);

  await fetch("/api/set_theme", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ theme: newTheme })
  });
}

// Minimal heartbeat for session tracking (FIX-69)
let heartbeatInterval = setInterval(async () => {
  try {
    await fetch('/api/session/heartbeat', { method: 'POST' });
  } catch (e) {}
}, 300000); // 5 minutes

window.addEventListener('beforeunload', () => {
  if (heartbeatInterval) clearInterval(heartbeatInterval);
});

// Minimal toast function
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}
window.showToast = showToast;
</script>
{% endif %}

{% block scripts %}{% endblock %}
</body>
</html>

login.html,

{% extends "base.html" %}
{% block title %}Login – TVS NIRIX{% endblock %}

{% block content %}

<div class="row justify-content-center" style="margin-top:60px;">
  <div class="col-12 col-sm-10 col-md-6 col-lg-4">

    <div class="card shadow-sm p-4" style="border-radius:14px;">

      <!-- =====================================================
           LOGO + TITLE - EXACTLY AS ORIGINAL
      ====================================================== -->
      <div class="text-center mb-3">
        <img src="{{ url_for('vehicle_image', filename='Nirix_Logo.png') }}"
             alt="NIRIX"
             style="height:80px; object-fit:contain;">
        <h5 class="mt-3 mb-0 fw-bold">Login</h5>
        <div class="small text-muted">
          TVS NIRIX Diagnostic System
        </div>
      </div>

      <!-- =====================================================
           ALERTS - EXACTLY AS ORIGINAL
      ====================================================== -->
      {% if error %}
        <div class="alert alert-danger py-2 small">
          {{ error }}
        </div>
      {% endif %}

      {% if message %}
        <div class="alert alert-success py-2 small">
          {{ message }}
        </div>
      {% endif %}

      <!-- =====================================================
           LOGIN FORM - ONLY ADDED login_id FOR SESSION TRACKING (FIX-66)
      ====================================================== -->
      <form method="post"
            action="{{ url_for('login') }}"
            novalidate>

        <!-- EMAIL -->
        <div class="mb-3">
          <label class="form-label small fw-semibold">
            Email ID
          </label>
          <input type="email"
                 name="email"
                 class="form-control"
                 placeholder="your.name@company.com"
                 autocomplete="username"
                 required>
        </div>

        <!-- PIN -->
        <div class="mb-3 position-relative">
          <label class="form-label small fw-semibold">
            PIN (4 digits)
          </label>

          <input type="password"
                 name="pin"
                 id="pinField"
                 maxlength="4"
                 pattern="[0-9]{4}"
                 inputmode="numeric"
                 autocomplete="current-password"
                 class="form-control"
                 placeholder="••••"
                 required>

          <span id="togglePin"
                title="Show / Hide PIN"
                class="position-absolute"
                style="
                  right:12px;
                  top:38px;
                  cursor:pointer;
                  opacity:0.6;
                  user-select:none;
                ">
            👁
          </span>
        </div>

        <!-- VCI MODE -->
        <div class="mb-3">
          <label class="form-label small fw-semibold">
            VCI Interface
          </label>

          <select name="vci_mode"
                  class="form-select"
                  required>
            <option value="pcan"
              {% if default_vci == 'pcan' %}selected{% endif %}>
              PCAN (Peak – Windows)
            </option>

            <option value="socketcan"
              {% if default_vci == 'socketcan' %}selected{% endif %}>
              SocketCAN (MCP2515 – Linux / RPi)
            </option>
          </select>

          <div class="form-text small">
            This sets the active CAN interface for the session.
          </div>
        </div>

        <!-- SUBMIT - EXACTLY AS ORIGINAL -->
        <button type="submit"
                class="btn btn-tvs w-100 mt-2">
          LOGIN
        </button>

        <!-- Hidden input for login_id tracking (FIX-66) - Added silently -->
        <input type="hidden" name="login_id" value="{{ uuid4() }}">

      </form>

      <!-- =====================================================
           LINKS - EXACTLY AS ORIGINAL
      ====================================================== -->
      <div class="mt-3 text-center small">
        <a href="{{ url_for('forgot_pin') }}">
          Forgot PIN?
        </a>
      </div>

      <div class="mt-2 text-center small">
        New user?
        <a href="{{ url_for('register') }}">
          Register here
        </a>
      </div>

    </div>

  </div>
</div>

{% endblock %}

{% block scripts %}
<script>
/* =====================================================
   PIN VISIBILITY TOGGLE - EXACTLY AS ORIGINAL
===================================================== */
(function () {
  const toggle = document.getElementById("togglePin");
  const field  = document.getElementById("pinField");

  if (!toggle || !field) return;

  toggle.addEventListener("click", () => {
    field.type = (field.type === "password") ? "text" : "password";
  });
})();
</script>
{% endblock %}


dashboard.html,

{% extends "base.html" %}
{% block title %}Dashboard – TVS NIRIX{% endblock %}

{% block head %}
<style>
  .card-shadow {
    box-shadow: 0 0.25rem 0.75rem rgba(15,23,42,.15);
    border-radius: 12px;
    border: 1px solid rgba(148,163,184,.3);
    background: #ffffff;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }

  body.dark .card-shadow {
    background: #1e293b;
    border-color: rgba(255,255,255,.08);
  }

  .card-shadow:hover {
    transform: translateY(-3px);
    box-shadow: 0 0.75rem 1.25rem rgba(15,23,42,.2);
  }

  .vehicle-card-img {
    max-height: 150px;
    object-fit: contain;
    background: #f8fafc;
    border-bottom: 1px solid rgba(148,163,184,.3);
  }

  body.dark .vehicle-card-img {
    background: #0f172a;
  }

  .vehicle-link {
    text-decoration: none;
    color: inherit;
    display: block;
    height: 100%;
  }

  .vehicle-link:focus-visible {
    outline: 2px solid #0d6efd;
    outline-offset: 3px;
    border-radius: 12px;
  }
  
  /* Minimal addition for VIN display */
  .vin-badge {
    background: var(--tvs-blue);
    color: white;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    margin-left: 4px;
  }
</style>
{% endblock %}

{% block content %}
<div class="row justify-content-center">
  <div class="col-11 col-xl-11">

    <!-- =====================================================
         HEADER - EXACTLY AS ORIGINAL
    ====================================================== -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h5 class="mb-0 fw-bold">Vehicle Selection</h5>
        <div class="small text-muted">
          Vehicles you are authorized to access
        </div>
      </div>
    </div>

    <!-- =====================================================
         FILTERS - EXACTLY AS ORIGINAL
    ====================================================== -->
    <div class="card card-shadow p-3 mb-3">
      <form id="filterForm" method="get" action="{{ url_for('dashboard') }}">
        <div class="row g-2">

          <!-- VIN FILTER -->
          <div class="col-12 col-md-4">
            <label class="form-label small mb-1">VIN Filter</label>
            <input
              name="vin"
              id="vinInput"
              type="text"
              class="form-control form-control-sm"
              value="{{ vin or '' }}"
              placeholder="VIN (partial allowed)"
              maxlength="17"
              autocomplete="off">
          </div>

          <!-- MODEL SEARCH -->
          <div class="col-12 col-md-4">
            <label class="form-label small mb-1">Search Model</label>
            <input
              name="search"
              id="searchInput"
              type="text"
              class="form-control form-control-sm"
              value="{{ search or '' }}"
              placeholder="Model name"
              autocomplete="off">
          </div>

          <!-- CATEGORY -->
          <div class="col-12 col-md-4">
            <label class="form-label small mb-1">Category</label>
            <select
              name="category"
              id="categorySelect"
              class="form-select form-select-sm">
              <option value="">All Categories</option>
              {% for cat in categories %}
                <option value="{{ cat }}"
                  {% if selected_category == cat %}selected{% endif %}>
                  {{ cat }}
                </option>
              {% endfor %}
            </select>
          </div>

          <!-- RESET -->
          <div class="col-12 d-flex justify-content-end mt-1">
            <a href="{{ url_for('dashboard') }}"
               class="btn btn-sm btn-outline-secondary">
              Reset Filters
            </a>
          </div>

        </div>
      </form>
    </div>

    <!-- =====================================================
         VEHICLE GRID - EXACTLY AS ORIGINAL
    ====================================================== -->
    <div class="row g-3" id="vehicleGrid">

      {% if vehicles %}
        {% for v in vehicles %}
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">

          <a href="{{ url_for('tests_page', model_name=v.name) }}"
             class="vehicle-link">

            <div class="card card-shadow h-100 d-flex flex-column">

              {% if v.image_filename %}
                <img
                  src="{{ url_for('vehicle_image', filename=v.image_filename) }}"
                  class="vehicle-card-img"
                  alt="{{ v.name }}">
              {% endif %}

              <div class="card-body p-2 d-flex flex-column">

                <h6 class="text-truncate mb-1" title="{{ v.name }}">
                  {{ v.name }}
                </h6>

                {% if v.description %}
                  <div class="small text-muted text-truncate"
                       title="{{ v.description }}">
                    {{ v.description }}
                  </div>
                {% endif %}

                {% if v.vin_pattern %}
                  <div class="small text-muted mt-1">
                    VIN Pattern:
                    <strong>{{ v.vin_pattern }}</strong>
                  </div>
                {% endif %}

                <div class="btn btn-sm btn-tvs w-100 mt-auto disabled"
                     style="border-radius:8px; pointer-events:none;">
                  Open Test Sequence →
                </div>

              </div>
            </div>

          </a>
        </div>
        {% endfor %}
      {% else %}
        <div class="col-12">
          <div class="alert alert-warning">
            No vehicle models are available for your account
            or match the applied filters.
          </div>
        </div>
      {% endif %}

    </div>

  </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener("DOMContentLoaded", () => {

  const form = document.getElementById("filterForm");
  const vinInput = document.getElementById("vinInput");
  const searchInput = document.getElementById("searchInput");
  const categorySelect = document.getElementById("categorySelect");

  if (!form) return;

  /* VIN → uppercase only */
  if (vinInput) {
    vinInput.addEventListener("input", () => {
      vinInput.value = vinInput.value.toUpperCase();
    });
  }

  /* Submit on ENTER only */
  function submitOnEnter(e) {
    if (e.key !== "Enter") return;
    e.preventDefault();

    if (vinInput) vinInput.value = vinInput.value.trim();
    if (searchInput) searchInput.value = searchInput.value.trim();

    form.submit();
  }

  if (vinInput) vinInput.addEventListener("keydown", submitOnEnter);
  if (searchInput) searchInput.addEventListener("keydown", submitOnEnter);

  /* Category → auto submit */
  if (categorySelect) {
    categorySelect.addEventListener("change", () => {
      form.submit();
    });
  }

});
</script>
{% endblock %}


