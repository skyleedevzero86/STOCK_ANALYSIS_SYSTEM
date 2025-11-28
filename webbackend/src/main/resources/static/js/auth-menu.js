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
        } else if (href === '/contact-inquiry-list.html') {
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

    const systemMonitorCard = document.getElementById('systemMonitorCard');
    if (systemMonitorCard) {
        if (isLoggedIn && isMainPage) {
            systemMonitorCard.style.display = 'block';
        } else {
            systemMonitorCard.style.display = 'none';
        }
    }

    const statusControls = document.querySelector('.status-controls');
    if (statusControls) {
        if (isLoggedIn && isMainPage) {
            statusControls.style.display = 'flex';
        } else {
            statusControls.style.display = 'none';
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
    
    console.log("redirectIfNotLoggedIn 실행 - 로그인 상태:", isLoggedIn, "현재 페이지:", currentPage);

    if ((currentPage === '/template-management.html' || currentPage === '/admin-dashboard.html' || currentPage === '/contact-inquiry-list.html' || currentPage === '/contact-inquiry-detail.html') && !isLoggedIn) {
        console.log("보호된 페이지인데 로그인 안 됨 - 로그인 페이지로 리다이렉트");
        window.location.href = '/admin-login.html';
    } else if ((currentPage === '/admin-login.html' || currentPage === '/admin-login') && isLoggedIn) {
        console.log("로그인 페이지인데 이미 로그인됨 - 대시보드로 리다이렉트");
        setTimeout(function() {
            window.location.href = '/admin-dashboard.html';
        }, 100);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const currentPage = window.location.pathname;
    const isLoginPage = currentPage === '/admin-login.html' || currentPage === '/admin-login';
    const isDashboardPage = currentPage === '/admin-dashboard.html' || currentPage === '/admin-dashboard';
    const isInquiryPage = currentPage === '/contact-inquiry-list.html' || currentPage === '/contact-inquiry-detail.html';
    
    updateNavigation();
    
    if (isDashboardPage || isInquiryPage) {
        setTimeout(function() {
            updateNavigation();
        }, 800);
    } else if (isLoginPage) {
        setTimeout(function() {
            updateNavigation();
            redirectIfNotLoggedIn();
        }, 400);
    } else {
        redirectIfNotLoggedIn();
    }
});

window.addEventListener('storage', function(e) {
    if (e.key === 'adminToken') {
        updateNavigation();
    }
});
