function checkAuthStatus() {
    const adminToken = localStorage.getItem("adminToken");
    return adminToken !== null;
}

function updateNavigation() {
    const isLoggedIn = checkAuthStatus();
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');

        if (href === '/email-subscription.html') {
            if (isLoggedIn) {
                link.style.display = 'none';
            } else {
                link.style.display = 'inline-block';
            }
        } else if (href === '/template-management.html' || href === '/api-view.html') {
            if (isLoggedIn) {
                link.style.display = 'inline-block';
            } else {
                link.style.display = 'none';
            }
        } else if (href === '/admin-login.html' || href === '/admin-dashboard.html') {
            if (isLoggedIn && window.location.pathname !== '/admin-dashboard.html') {
                link.setAttribute('href', '/admin-dashboard.html');
                link.textContent = link.textContent === '관리자' ? '관리자 대시보드' : link.textContent;
            }
        }
    });
}

function redirectIfNotLoggedIn() {
    const isLoggedIn = checkAuthStatus();
    const currentPage = window.location.pathname;

    if ((currentPage === '/template-management.html' || currentPage === '/admin-dashboard.html') && !isLoggedIn) {
        window.location.href = '/admin-login.html';
    } else if (currentPage === '/admin-login.html' && isLoggedIn) {
        window.location.href = '/admin-dashboard.html';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    updateNavigation();
    redirectIfNotLoggedIn();
});

window.addEventListener('storage', function(e) {
    if (e.key === 'adminToken') {
        updateNavigation();
    }
});
