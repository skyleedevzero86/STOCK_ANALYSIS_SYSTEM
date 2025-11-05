function checkAuthStatus() {
    const adminToken = localStorage.getItem("adminToken");
    return adminToken !== null;
}

function logout() {
    localStorage.removeItem("adminToken");
    updateNavigation();
    window.location.href = "/admin-login.html";
}

function updateNavigation() {
    const isLoggedIn = checkAuthStatus();
    const navLinks = document.querySelectorAll('.nav-link');
    const symbolSelectBtn = document.getElementById('symbolSelectBtn');
    const logoutButtons = document.querySelectorAll('.btn-logout-nav');
    const currentPage = window.location.pathname;
    const isMainPage = currentPage === '/' || currentPage === '/index.html';
    const isLoginPage = currentPage === '/admin-login.html' || currentPage === '/admin-login';
    const isSubscriptionPage = currentPage === '/email-subscription.html' || currentPage === '/email-subscription';

    navLinks.forEach(link => {
        const href = link.getAttribute('href');

        if (href === '/') {
            link.style.display = 'inline-block';
        } else if (href === '/admin-login.html') {
            if (isLoggedIn) {
                link.style.display = 'none';
            } else {
                link.style.display = 'inline-block';
            }
        } else if (href === '/email-subscription.html') {
            if (isLoggedIn) {
                link.style.display = 'none';
            } else {
                link.style.display = 'inline-block';
            }
        } else if (href === '/template-management.html') {
            if (isLoggedIn) {
                link.style.display = 'inline-block';
            } else {
                link.style.display = 'none';
            }
        } else if (href === '/api-view.html') {
            if (isLoggedIn) {
                link.style.display = 'inline-block';
            } else {
                link.style.display = 'none';
            }
        } else if (href === '/admin-dashboard.html') {
            if (isLoggedIn) {
                link.style.display = 'inline-block';
            } else {
                link.style.display = 'none';
            }
        }
    });

    logoutButtons.forEach(btn => {
        if (isLoggedIn) {
            btn.style.display = 'inline-block';
        } else {
            btn.style.display = 'none';
        }
    });

    if (symbolSelectBtn) {
        if (isLoginPage || isSubscriptionPage) {
            symbolSelectBtn.style.display = 'none';
        } else if (isLoggedIn && isMainPage) {
            symbolSelectBtn.style.display = 'inline-block';
        } else if (isLoggedIn && !isMainPage) {
            symbolSelectBtn.style.display = 'none';
        } else if (!isLoggedIn && isMainPage) {
            symbolSelectBtn.style.display = 'inline-block';
        } else {
            symbolSelectBtn.style.display = 'none';
        }
    }

    const symbolSelectLinks = document.querySelectorAll('.nav-link.btn-nav');
    symbolSelectLinks.forEach(link => {
        if (isLoginPage || isSubscriptionPage) {
            link.style.display = 'none';
        } else if (isLoggedIn && isMainPage) {
            link.style.display = 'inline-block';
        } else if (isLoggedIn && !isMainPage) {
            link.style.display = 'none';
        } else if (!isLoggedIn && isMainPage) {
            link.style.display = 'inline-block';
        } else {
            link.style.display = 'none';
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
