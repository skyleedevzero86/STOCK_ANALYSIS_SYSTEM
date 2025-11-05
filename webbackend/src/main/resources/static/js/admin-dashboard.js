if (!localStorage.getItem("adminToken")) {
    window.location.href = "/admin-login.html";
}

let currentPage = 0;
let pageSize = 10;
let totalPages = 0;
let totalCount = 0;
let searchName = "";

async function loadSubscriptions(page = 0) {
    const adminToken = localStorage.getItem("adminToken");
    
    if (!adminToken) {
        window.location.href = "/admin-login.html";
        return;
    }

    currentPage = page;
    const searchParam = searchName ? `&name=${encodeURIComponent(searchName)}` : "";

    try {
        const response = await fetch(`/api/admin/subscriptions?page=${page}&size=${pageSize}${searchParam}`, {
            headers: {
                Authorization: adminToken,
            },
        });

        if (response.status === 401) {
            localStorage.removeItem("adminToken");
            window.location.href = "/admin-login.html";
            return;
        }

        const result = await response.json();

        if (result.success) {
            currentPage = result.data.page || 0;
            totalPages = result.data.totalPages || 0;
            totalCount = result.data.total || 0;
            displaySubscriptions(result.data.subscriptions);
            updatePagination();
            loadAllSubscriptionsForStats();
        } else {
            if (result.message && result.message.includes("인증")) {
                localStorage.removeItem("adminToken");
                window.location.href = "/admin-login.html";
            } else {
                showError(result.message || "데이터를 불러오는 중 오류가 발생했습니다.");
            }
        }
    } catch (error) {
        showError("데이터를 불러오는 중 오류가 발생했습니다.");
    }
}

async function loadAllSubscriptionsForStats() {
    const adminToken = localStorage.getItem("adminToken");
    if (!adminToken) return;

    try {
        const response = await fetch("/api/admin/subscriptions?page=0&size=1000", {
            headers: {
                Authorization: adminToken,
            },
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success && result.data.subscriptions) {
                updateStats(result.data.subscriptions);
            }
        }
    } catch (error) {
        console.error("통계 데이터 로드 실패:", error);
    }
}

function displaySubscriptions(subscriptions) {
    const content = document.getElementById("subscriptionsContent");

    if (subscriptions.length === 0) {
        content.innerHTML = '<div class="loading">구독자가 없습니다.</div>';
        return;
    }

    const table = `
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>이름</th>
          <th>이메일</th>
          <th>전화번호</th>
          <th>이메일 동의</th>
          <th>전화 동의</th>
          <th>가입일</th>
          <th>상태</th>
        </tr>
      </thead>
      <tbody>
        ${subscriptions
        .map(
            (sub) => `
            <tr>
              <td>${sub.id}</td>
              <td><a href="#" onclick="viewEmailHistory(${sub.id}, '${sub.email}'); return false;" class="name-link">${sub.name}</a></td>
              <td>${sub.email}</td>
              <td>${sub.phone || "-"}</td>
              <td>
                <label class="consent-toggle">
                  <input type="checkbox" ${sub.isEmailConsent ? "checked" : ""} 
                         onchange="updateEmailConsent(${sub.id}, this.checked)">
                  <span class="consent-badge ${sub.isEmailConsent ? "consent-yes" : "consent-no"}">
                    ${sub.isEmailConsent ? "동의" : "비동의"}
                  </span>
                </label>
              </td>
              <td>
                <label class="consent-toggle">
                  <input type="checkbox" ${sub.isPhoneConsent ? "checked" : ""} 
                         onchange="updatePhoneConsent(${sub.id}, this.checked)">
                  <span class="consent-badge ${sub.isPhoneConsent ? "consent-yes" : "consent-no"}">
                    ${sub.isPhoneConsent ? "동의" : "비동의"}
                  </span>
                </label>
              </td>
              <td>${new Date(sub.createdAt).toLocaleDateString()}</td>
              <td>
                <button class="status-toggle-btn ${sub.isActive ? "status-active-btn" : "status-inactive-btn"}" 
                        onclick="toggleSubscriptionStatus(${sub.id}, ${!sub.isActive})">
                  ${sub.isActive ? "활성" : "비활성"}
                </button>
              </td>
            </tr>
        `
        )
        .join("")}
      </tbody>
    </table>
    <div id="pagination"></div>
  `;

    content.innerHTML = table;
}

function updatePagination() {
    const pagination = document.getElementById("pagination");
    if (!pagination) return;

    if (totalPages <= 1) {
        pagination.innerHTML = "";
        return;
    }

    let paginationHTML = '<div class="pagination">';
    
    if (currentPage > 0) {
        paginationHTML += `<button onclick="loadSubscriptions(${currentPage - 1})" class="page-btn">이전</button>`;
    }

    const startPage = Math.max(0, currentPage - 2);
    const endPage = Math.min(totalPages - 1, currentPage + 2);

    if (startPage > 0) {
        paginationHTML += `<button onclick="loadSubscriptions(0)" class="page-btn">1</button>`;
        if (startPage > 1) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `<button onclick="loadSubscriptions(${i})" 
                                   class="page-btn ${i === currentPage ? 'active' : ''}">${i + 1}</button>`;
    }

    if (endPage < totalPages - 1) {
        if (endPage < totalPages - 2) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
        paginationHTML += `<button onclick="loadSubscriptions(${totalPages - 1})" class="page-btn">${totalPages}</button>`;
    }

    if (currentPage < totalPages - 1) {
        paginationHTML += `<button onclick="loadSubscriptions(${currentPage + 1})" class="page-btn">다음</button>`;
    }

    paginationHTML += `<span class="page-info">총 ${totalCount}건 (${currentPage + 1}/${totalPages} 페이지)</span>`;
    paginationHTML += '</div>';

    pagination.innerHTML = paginationHTML;
}

async function updateEmailConsent(id, isEmailConsent) {
    const adminToken = localStorage.getItem("adminToken");
    if (!adminToken) return;

    try {
        const response = await fetch(`/api/admin/subscriptions/${id}/consent`, {
            method: "PUT",
            headers: {
                Authorization: adminToken,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ isEmailConsent: isEmailConsent }),
        });

        if (response.status === 401) {
            localStorage.removeItem("adminToken");
            window.location.href = "/admin-login.html";
            return;
        }

        const result = await response.json();

        if (result.success) {
            loadSubscriptions(currentPage);
            loadAllSubscriptionsForStats();
        } else {
            alert(result.message || "수정에 실패했습니다.");
            loadSubscriptions(currentPage);
        }
    } catch (error) {
        alert("수정 중 오류가 발생했습니다: " + error.message);
        loadSubscriptions(currentPage);
    }
}

async function updatePhoneConsent(id, isPhoneConsent) {
    const adminToken = localStorage.getItem("adminToken");
    if (!adminToken) return;

    try {
        const response = await fetch(`/api/admin/subscriptions/${id}/consent`, {
            method: "PUT",
            headers: {
                Authorization: adminToken,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ isPhoneConsent: isPhoneConsent }),
        });

        if (response.status === 401) {
            localStorage.removeItem("adminToken");
            window.location.href = "/admin-login.html";
            return;
        }

        const result = await response.json();

        if (result.success) {
            loadSubscriptions(currentPage);
            loadAllSubscriptionsForStats();
        } else {
            alert(result.message || "수정에 실패했습니다.");
            loadSubscriptions(currentPage);
        }
    } catch (error) {
        alert("수정 중 오류가 발생했습니다: " + error.message);
        loadSubscriptions(currentPage);
    }
}

async function toggleSubscriptionStatus(id, isActive) {
    const adminToken = localStorage.getItem("adminToken");
    if (!adminToken) return;

    try {
        const response = await fetch(`/api/admin/subscriptions/${id}/status`, {
            method: "PUT",
            headers: {
                Authorization: adminToken,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ isActive: isActive }),
        });

        if (response.status === 401) {
            localStorage.removeItem("adminToken");
            window.location.href = "/admin-login.html";
            return;
        }

        const result = await response.json();

        if (result.success) {
            loadSubscriptions(currentPage);
            loadAllSubscriptionsForStats();
        } else {
            alert(result.message || "상태 변경에 실패했습니다.");
            loadSubscriptions(currentPage);
        }
    } catch (error) {
        alert("상태 변경 중 오류가 발생했습니다: " + error.message);
        loadSubscriptions(currentPage);
    }
}

function viewEmailHistory(id, email) {
    window.location.href = `/email-history.html?id=${id}&email=${encodeURIComponent(email)}`;
}

function handleSearch() {
    const searchInput = document.getElementById("searchNameInput");
    if (searchInput) {
        searchName = searchInput.value.trim();
        currentPage = 0;
        loadSubscriptions(0);
    }
}

function handleSearchKeyUp(event) {
    if (event.key === "Enter") {
        handleSearch();
    }
}

function clearSearch() {
    const searchInput = document.getElementById("searchNameInput");
    if (searchInput) {
        searchInput.value = "";
    }
    searchName = "";
    currentPage = 0;
    loadSubscriptions(0);
}

function updateStats(subscriptions) {
    document.getElementById("totalSubscriptions").textContent =
        subscriptions.length;
    document.getElementById("emailConsentSubscriptions").textContent =
        subscriptions.filter((sub) => sub.isEmailConsent).length;
    document.getElementById("phoneConsentSubscriptions").textContent =
        subscriptions.filter((sub) => sub.isPhoneConsent).length;
}

function showError(message) {
    const content = document.getElementById("subscriptionsContent");
    content.innerHTML = `<div class="error">${message}</div>`;
}

function logout() {
    localStorage.removeItem("adminToken");
    updateNavigation();
    window.location.href = "/admin-login.html";
}

document.addEventListener("DOMContentLoaded", function() {
    updateNavigation();
    loadSubscriptions();
});
