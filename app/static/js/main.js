// Sidebar toggle (mobile) + dark mode toggle, both self-contained so
// every page gets them for free just by extending layout.html.
document.addEventListener('DOMContentLoaded', function () {
  var sidebar = document.getElementById('appSidebar');
  var backdrop = document.getElementById('sidebarBackdrop');
  var toggleBtn = document.getElementById('sidebarToggle');

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      backdrop.classList.toggle('open');
    });
  }
  if (backdrop) backdrop.addEventListener('click', closeSidebar);

  var themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      var html = document.documentElement;
      var current = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-bs-theme', current);
      localStorage.setItem('theme', current);
    });
  }

  // Auto-dismiss success/info flash messages after a few seconds.
  document.querySelectorAll('.alert-success, .alert-info').forEach(function (alertEl) {
    setTimeout(function () {
      var alert = bootstrap.Alert.getOrCreateInstance(alertEl);
      alert.close();
    }, 5000);
  });
});
