// AttendX Main JS
document.addEventListener('DOMContentLoaded', function() {

  // ── Live date/time in topbar (updates every second)
  const dateEl = document.getElementById('liveDate');
  if (dateEl) {
    function updateTime() {
      const now  = new Date();
      const date = now.toLocaleDateString('en-US', {
        weekday: 'long',
        year:    'numeric',
        month:   'long',
        day:     'numeric'
      });
      const time = now.toLocaleTimeString('en-US', {
        hour:   '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
      dateEl.textContent = date + '   ' + time;
    }
    updateTime();
    setInterval(updateTime, 1000);
  }

  // ── Auto-dismiss flash messages after 5s
  document.querySelectorAll('.flash').forEach(function(flash) {
    setTimeout(function() {
      flash.style.opacity    = '0';
      flash.style.transform  = 'translateY(-8px)';
      flash.style.transition = 'all .4s ease';
      setTimeout(function() { flash.remove(); }, 400);
    }, 5000);
  });

  // ── Animate stat card values
  document.querySelectorAll('.stat-value').forEach(function(el) {
    const target = parseInt(el.textContent);
    if (!isNaN(target) && target > 0) {
      let current = 0;
      const step  = Math.ceil(target / 30);
      const timer = setInterval(function() {
        current = Math.min(current + step, target);
        el.textContent = current;
        if (current >= target) clearInterval(timer);
      }, 30);
    }
  });

  // ── Progress bar animation
  document.querySelectorAll('.att-progress .progress-bar, .progress-bar-wrap .progress-bar').forEach(function(bar) {
    const width = bar.style.width;
    bar.style.width = '0';
    setTimeout(function() { bar.style.width = width; }, 200);
  });

});

// ── Mobile sidebar toggle
(function() {
  const menuBtn = document.getElementById('mobileMenuBtn');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');

  if (!menuBtn) return;

  menuBtn.addEventListener('click', function() {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
  });

  overlay.addEventListener('click', function() {
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  });

  // Close sidebar when a nav link is clicked on mobile
  document.querySelectorAll('.nav-item').forEach(function(item) {
    item.addEventListener('click', function() {
      if (window.innerWidth <= 768) {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
      }
    });
  });

})();

function togglePw(inputId, btn) {
  const input = document.getElementById(inputId);
  const icon  = btn.querySelector('i');
  if (input.type === 'password') {
    input.type = 'text';
    icon.className = 'fas fa-eye-slash';
  } else {
    input.type = 'password';
    icon.className = 'fas fa-eye';
  }
}