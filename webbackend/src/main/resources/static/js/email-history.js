if (!localStorage.getItem("adminToken")) {
    window.location.href = "/admin-login.html";
}

let currentHistoryPage = 0;
let historyPageSize = 20;
let historyTotalPages = 0;
let historyTotalCount = 0;
let subscriptionId = null;
let userEmail = null;

document.addEventListener("DOMContentLoaded", function() {
    updateNavigation();
    
    const urlParams = new URLSearchParams(window.location.search);
    subscriptionId = urlParams.get("id");
    userEmail = urlParams.get("email");

    if (!subscriptionId || !userEmail) {
        alert("잘못된 접근입니다.");
        window.location.href = "/admin-dashboard.html";
        return;
    }

    document.getElementById("userEmailDisplay").textContent = `이메일: ${userEmail}`;
    document.getElementById("historyTitle").textContent = `${userEmail} - 이메일 발송 이력`;
    
    loadEmailHistory(0);
});

async function loadEmailHistory(page = 0) {
    const adminToken = localStorage.getItem("adminToken");
    
    if (!adminToken) {
        window.location.href = "/admin-login.html";
        return;
    }

    if (!subscriptionId) {
        showError("구독자 ID가 없습니다.");
        return;
    }

    try {
        const response = await fetch(`/api/admin/subscriptions/${subscriptionId}/email-history?page=${page}&size=${historyPageSize}`, {
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
            currentHistoryPage = result.data.page || 0;
            historyTotalPages = result.data.totalPages || 0;
            historyTotalCount = result.data.total || 0;
            displayEmailHistory(result.data.logs);
            updateHistoryPagination();
        } else {
            if (result.message && result.message.includes("인증")) {
                localStorage.removeItem("adminToken");
                window.location.href = "/admin-login.html";
            } else {
                showError(result.message || "데이터를 불러오는 중 오류가 발생했습니다.");
            }
        }
    } catch (error) {
        showError("데이터를 불러오는 중 오류가 발생했습니다: " + error.message);
    }
}

function displayEmailHistory(logs) {
    const content = document.getElementById("emailHistoryContent");

    if (logs.length === 0) {
        content.innerHTML = '<div class="loading">발송 이력이 없습니다.</div>';
        return;
    }

    const table = `
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>종목</th>
          <th>알림 유형</th>
          <th>상태</th>
          <th>발송 시간</th>
          <th>메시지</th>
          <th>오류 메시지</th>
        </tr>
      </thead>
      <tbody>
        ${logs
        .map(
            (log) => `
            <tr>
              <td>${log.id}</td>
              <td>${log.symbol || "-"}</td>
              <td>${log.notificationType}</td>
              <td><span class="status-badge ${
                log.status === "SENT"
                    ? "status-active"
                    : log.status === "FAILED"
                    ? "status-inactive"
                    : ""
            }">${
                log.status === "SENT" ? "성공" : log.status === "FAILED" ? "실패" : "대기"
            }</span></td>
              <td>${new Date(log.sentAt).toLocaleString()}</td>
              <td>${log.message ? (log.message.length > 100 ? log.message.substring(0, 100) + "..." : log.message) : "-"}</td>
              <td>${log.errorMessage || "-"}</td>
            </tr>
        `
        )
        .join("")}
      </tbody>
    </table>
    <div id="historyPagination"></div>
  `;

    content.innerHTML = table;
}

function updateHistoryPagination() {
    const pagination = document.getElementById("historyPagination");
    if (!pagination) return;

    if (historyTotalPages <= 1) {
        pagination.innerHTML = "";
        return;
    }

    let paginationHTML = '<div class="pagination">';
    
    if (currentHistoryPage > 0) {
        paginationHTML += `<button onclick="loadEmailHistory(${currentHistoryPage - 1})" class="page-btn">이전</button>`;
    }

    const startPage = Math.max(0, currentHistoryPage - 2);
    const endPage = Math.min(historyTotalPages - 1, currentHistoryPage + 2);

    if (startPage > 0) {
        paginationHTML += `<button onclick="loadEmailHistory(0)" class="page-btn">1</button>`;
        if (startPage > 1) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `<button onclick="loadEmailHistory(${i})" 
                                   class="page-btn ${i === currentHistoryPage ? 'active' : ''}">${i + 1}</button>`;
    }

    if (endPage < historyTotalPages - 1) {
        if (endPage < historyTotalPages - 2) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
        paginationHTML += `<button onclick="loadEmailHistory(${historyTotalPages - 1})" class="page-btn">${historyTotalPages}</button>`;
    }

    if (currentHistoryPage < historyTotalPages - 1) {
        paginationHTML += `<button onclick="loadEmailHistory(${currentHistoryPage + 1})" class="page-btn">다음</button>`;
    }

    paginationHTML += `<span class="page-info">총 ${historyTotalCount}건 (${currentHistoryPage + 1}/${historyTotalPages} 페이지)</span>`;
    paginationHTML += '</div>';

    pagination.innerHTML = paginationHTML;
}

function showError(message) {
    const content = document.getElementById("emailHistoryContent");
    content.innerHTML = `<div class="error">${message}</div>`;
}

function logout() {
    localStorage.removeItem("adminToken");
    updateNavigation();
    window.location.href = "/admin-login.html";
}

