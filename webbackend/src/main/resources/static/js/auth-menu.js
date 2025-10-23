function checkAuthStatus() {
    const adminToken = localStorage.getItem("adminToken");
    return adminToken !== null;
}

function updateNavigation() {
    const isLoggedIn = checkAuthStatus();
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');

        if (href === '/template-management.html' || href === '/api-view.html') {
            if (isLoggedIn) {
                link.style.display = 'inline-block';
            } else {
                link.style.display = 'none';
            }
        }
    });
}

function redirectIfNotLoggedIn() {
    const isLoggedIn = checkAuthStatus();
    const currentPage = window.location.pathname;

    if ((currentPage === '/template-management.html' || currentPage === '/admin-dashboard.html') && !isLoggedIn) {
        window.location.href = '/admin-login.html';
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
