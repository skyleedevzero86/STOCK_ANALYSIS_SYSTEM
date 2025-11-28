if (!localStorage.getItem("adminToken")) {
    window.location.href = "/admin-login.html";
}

let currentHistoryPage = 0;
let historyPageSize = 20;
let historyTotalPages = 0;
let historyTotalCount = 0;
let subscriptionId = null;
let userEmail = null;
let actualUserEmail = null;
let userPhone = null;

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

    const userEmailDisplay = document.getElementById("userEmailDisplay");
    if (userEmailDisplay) {
        userEmailDisplay.textContent = `이메일: ${userEmail}`;
    }
    
    const historyTitle = document.getElementById("historyTitle");
    if (historyTitle) {
        historyTitle.textContent = `${userEmail} - 이메일 발송 이력`;
    }
    
    const pageSizeSelect = document.getElementById("pageSizeSelect");
    if (pageSizeSelect) {
        pageSizeSelect.value = historyPageSize.toString();
    }
    
    loadActualEmail();
    loadEmailHistory(0);
});

async function loadActualEmail() {
    const adminToken = localStorage.getItem("adminToken");
    if (!adminToken || !subscriptionId) return;

    try {
        const response = await fetch(`/api/admin/subscriptions/${subscriptionId}`, {
            headers: {
                Authorization: adminToken,
            },
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success && result.data) {
                if (result.data.email) {
                actualUserEmail = result.data.email;
                }
                if (result.data.phone) {
                    userPhone = result.data.phone;
                }
            }
        }
    } catch (error) {
        console.error("이메일 주소 조회 실패:", error);
    }
}

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

    const content = document.getElementById("emailHistoryContent");
    if (!content) {
        console.error("emailHistoryContent 요소를 찾을 수 없습니다.");
        return;
    }
    content.innerHTML = '<div class="loading">데이터를 불러오는 중...</div>';

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
            
            if (result.data.logs && result.data.logs.length > 0) {
                displayEmailHistory(result.data.logs);
                updateHistoryPagination();
            } else {
                content.innerHTML = '<div class="loading">발송 이력이 없습니다.</div><div id="historyPagination"></div>';
                updateHistoryPagination();
            }
        } else {
            if (result.message && result.message.includes("인증")) {
                localStorage.removeItem("adminToken");
                window.location.href = "/admin-login.html";
            } else {
                console.error("이력 로드 실패:", result.message);
                const content = document.getElementById("emailHistoryContent");
                if (content) {
                    content.innerHTML = '<div class="error">데이터를 불러오는 중 오류가 발생했습니다. 페이지를 새로고침해주세요.</div>';
                }
            }
        }
    } catch (error) {
        console.error("이메일 이력 로드 오류:", error);
        const content = document.getElementById("emailHistoryContent");
        if (content) {
            content.innerHTML = '<div class="error">데이터를 불러오는 중 오류가 발생했습니다. 페이지를 새로고침해주세요.</div>';
        }
    }
}

function displayEmailHistory(logs) {
    const content = document.getElementById("emailHistoryContent");
    if (!content) {
        console.error("emailHistoryContent 요소를 찾을 수 없습니다.");
        return;
    }

    if (!logs || logs.length === 0) {
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

    let paginationHTML = '<div class="pagination" style="display: flex; justify-content: center; align-items: center; gap: 8px; margin-top: 20px; padding: 20px; flex-wrap: wrap;">';
    
    if (historyTotalPages <= 1) {
        paginationHTML += `<span class="page-info" style="margin-left: 16px; color: #666; font-size: 0.875rem;">총 ${historyTotalCount}건</span>`;
    } else {
        if (currentHistoryPage > 0) {
            paginationHTML += `<button onclick="loadEmailHistory(${currentHistoryPage - 1})" class="page-btn" style="padding: 8px 16px; border: 1px solid #e0e0e0; background: #fff; color: #2f456e; border-radius: 8px; cursor: pointer; font-size: 0.875rem; font-weight: 500; transition: all 0.3s ease;">이전</button>`;
        }

        const startPage = Math.max(0, currentHistoryPage - 2);
        const endPage = Math.min(historyTotalPages - 1, currentHistoryPage + 2);

        if (startPage > 0) {
            paginationHTML += `<button onclick="loadEmailHistory(0)" class="page-btn" style="padding: 8px 16px; border: 1px solid #e0e0e0; background: #fff; color: #2f456e; border-radius: 8px; cursor: pointer; font-size: 0.875rem; font-weight: 500; transition: all 0.3s ease;">1</button>`;
            if (startPage > 1) {
                paginationHTML += `<span class="page-ellipsis" style="padding: 8px 4px; color: #666;">...</span>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === currentHistoryPage;
            paginationHTML += `<button onclick="loadEmailHistory(${i})" 
                                       class="page-btn ${isActive ? 'active' : ''}" 
                                       style="padding: 8px 16px; border: 1px solid ${isActive ? '#2f456e' : '#e0e0e0'}; background: ${isActive ? '#2f456e' : '#fff'}; color: ${isActive ? '#fff' : '#2f456e'}; border-radius: 8px; cursor: pointer; font-size: 0.875rem; font-weight: 500; transition: all 0.3s ease;">${i + 1}</button>`;
        }

        if (endPage < historyTotalPages - 1) {
            if (endPage < historyTotalPages - 2) {
                paginationHTML += `<span class="page-ellipsis" style="padding: 8px 4px; color: #666;">...</span>`;
            }
            paginationHTML += `<button onclick="loadEmailHistory(${historyTotalPages - 1})" class="page-btn" style="padding: 8px 16px; border: 1px solid #e0e0e0; background: #fff; color: #2f456e; border-radius: 8px; cursor: pointer; font-size: 0.875rem; font-weight: 500; transition: all 0.3s ease;">${historyTotalPages}</button>`;
        }

        if (currentHistoryPage < historyTotalPages - 1) {
            paginationHTML += `<button onclick="loadEmailHistory(${currentHistoryPage + 1})" class="page-btn" style="padding: 8px 16px; border: 1px solid #e0e0e0; background: #fff; color: #2f456e; border-radius: 8px; cursor: pointer; font-size: 0.875rem; font-weight: 500; transition: all 0.3s ease;">다음</button>`;
        }

        paginationHTML += `<span class="page-info" style="margin-left: 16px; color: #666; font-size: 0.875rem;">총 ${historyTotalCount}건 (${currentHistoryPage + 1}/${historyTotalPages} 페이지)</span>`;
    }

    paginationHTML += '</div>';

    pagination.innerHTML = paginationHTML;
}

function showError(message) {
    const content = document.getElementById("emailHistoryContent");
    if (!content) {
        console.error("emailHistoryContent 요소를 찾을 수 없습니다.");
        return;
    }
    content.innerHTML = `<div class="error">${message}</div>`;
}

function changePageSize() {
    const select = document.getElementById("pageSizeSelect");
    historyPageSize = parseInt(select.value);
    currentHistoryPage = 0;
    loadEmailHistory(0);
}

function maskEmail(email) {
    if (!email || !email.includes("@")) return email;
    
    const parts = email.split("@");
    if (parts.length !== 2) return email;
    
    const username = parts[0];
    const domain = parts[1];
    
    if (username.length <= 2) {
        return `*@${domain}`;
    } else if (username.length <= 4) {
        return `${username[0]}***@${domain}`;
    } else {
        const masked = `${username[0]}${"*".repeat(username.length - 2)}${username[username.length - 1]}`;
        return `${masked}@${domain}`;
    }
}

function maskPhone(phone) {
    if (!phone) return phone;
    
    const cleaned = phone.replace(/-/g, "").replace(/\s/g, "");
    
    if (cleaned.length <= 4) {
        return "*".repeat(cleaned.length);
    } else {
        return `${cleaned.substring(0, 2)}${"*".repeat(cleaned.length - 4)}${cleaned.substring(cleaned.length - 2)}`;
    }
}

function openSendEmailModal() {
    const modal = document.getElementById("sendEmailModal");
    const recipientEmailInput = document.getElementById("recipientEmail");
    const actualRecipientEmailInput = document.getElementById("actualRecipientEmail");
    
    let actualEmail = "";
    if (actualUserEmail) {
        actualEmail = actualUserEmail;
    } else if (userEmail) {
        actualEmail = userEmail;
    }
    
    recipientEmailInput.value = maskEmail(actualEmail);
    actualRecipientEmailInput.value = actualEmail;
    
    document.getElementById("emailSubject").value = "";
    document.getElementById("emailBody").value = "";
    modal.style.display = "flex";
}

function closeSendEmailModal() {
    const modal = document.getElementById("sendEmailModal");
    modal.style.display = "none";
}

async function sendEmail(event) {
    const adminToken = localStorage.getItem("adminToken");
    if (!adminToken) {
        alert("인증이 필요합니다.");
        return;
    }

    const recipientEmail = document.getElementById("actualRecipientEmail").value.trim();
    const maskedEmail = document.getElementById("recipientEmail").value.trim();
    const subject = document.getElementById("emailSubject").value.trim();
    const body = document.getElementById("emailBody").value.trim();

    if (!recipientEmail || !subject || !body) {
        alert("이메일 주소, 제목, 내용을 모두 입력해주세요.");
        return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(recipientEmail)) {
        alert("올바른 이메일 주소가 아닙니다.");
        return;
    }

    if (!confirm(`다음 이메일 주소로 이메일을 발송하시겠습니까?\n\n${maskedEmail}`)) {
        return;
    }

    const sendButton = document.getElementById("sendEmailBtn");
    if (sendButton) {
        sendButton.disabled = true;
        sendButton.textContent = "발송 중...";
        sendButton.style.cursor = "not-allowed";
        sendButton.style.opacity = "0.6";
    }

    try {
        const response = await fetch(`/api/admin/subscriptions/${subscriptionId}/send-email`, {
            method: "POST",
            headers: {
                Authorization: adminToken,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                toEmail: recipientEmail,
                subject: subject,
                body: body
            }),
        });

        if (response.status === 401) {
            localStorage.removeItem("adminToken");
            window.location.href = "/admin-login.html";
            return;
        }

        const result = await response.json();

        if (result.success) {
            if (sendButton) {
                sendButton.disabled = false;
                sendButton.textContent = "발송";
                sendButton.style.cursor = "pointer";
                sendButton.style.opacity = "1";
            }
            alert("이메일이 성공적으로 발송되었습니다.");
            closeSendEmailModal();
            setTimeout(() => {
                loadEmailHistory(currentHistoryPage).catch(error => {
                    console.error("이력 로드 실패:", error);
                });
            }, 500);
        } else {
            if (sendButton) {
                sendButton.disabled = false;
                sendButton.textContent = "발송";
                sendButton.style.cursor = "pointer";
                sendButton.style.opacity = "1";
            }
            alert(result.message || "이메일 발송에 실패했습니다.");
        }
    } catch (error) {
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.textContent = "발송";
            sendButton.style.cursor = "pointer";
            sendButton.style.opacity = "1";
        }
        alert("이메일 발송 중 오류가 발생했습니다: " + error.message);
    }
}

function openSendSmsModal() {
    const modal = document.getElementById("sendSmsModal");
    const recipientPhoneInput = document.getElementById("recipientPhone");
    const actualRecipientPhoneInput = document.getElementById("actualRecipientPhone");
    
    let actualPhone = "";
    if (userPhone) {
        actualPhone = userPhone.replace(/-/g, "");
    }
    
    recipientPhoneInput.value = maskPhone(actualPhone);
    actualRecipientPhoneInput.value = actualPhone;
    
    document.getElementById("smsBody").value = "";
    modal.style.display = "flex";
}

function closeSendSmsModal() {
    const modal = document.getElementById("sendSmsModal");
    modal.style.display = "none";
}

async function sendSms(event) {
    const adminToken = localStorage.getItem("adminToken");
    if (!adminToken) {
        alert("인증이 필요합니다.");
        return;
    }

    const recipientPhone = document.getElementById("actualRecipientPhone").value.trim().replace(/-/g, "");
    const body = document.getElementById("smsBody").value.trim();
    const maskedRecipientPhone = maskPhone(recipientPhone);

    if (!recipientPhone || !body) {
        alert("전화번호와 메시지 내용을 모두 입력해주세요.");
        return;
    }

    const phoneRegex = /^010\d{8}$/;
    if (!phoneRegex.test(recipientPhone)) {
        alert("올바른 수신자 전화번호 형식이 아닙니다. (01012345678 형식)");
        return;
    }

    if (!confirm("문자를 발송하시겠습니까?")) {
        return;
    }

    const sendButton = document.getElementById("sendSmsBtn");
    if (sendButton) {
        sendButton.disabled = true;
        sendButton.textContent = "발송 중...";
        sendButton.style.cursor = "not-allowed";
        sendButton.style.opacity = "0.6";
    }

    try {
        const response = await fetch(`/api/admin/subscriptions/${subscriptionId}/send-sms`, {
            method: "POST",
            headers: {
                Authorization: adminToken,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                toPhone: recipientPhone,
                message: body
            }),
        });

        if (response.status === 401) {
            localStorage.removeItem("adminToken");
            window.location.href = "/admin-login.html";
            return;
        }

        const result = await response.json();

        if (result.success) {
            if (sendButton) {
                sendButton.disabled = false;
                sendButton.textContent = "발송";
                sendButton.style.cursor = "pointer";
                sendButton.style.opacity = "1";
            }
            alert("문자가 성공적으로 발송되었습니다.");
            closeSendSmsModal();
            setTimeout(() => {
                loadEmailHistory(currentHistoryPage).catch(error => {
                    console.error("이력 로드 실패:", error);
                });
            }, 500);
        } else {
            if (sendButton) {
                sendButton.disabled = false;
                sendButton.textContent = "발송";
                sendButton.style.cursor = "pointer";
                sendButton.style.opacity = "1";
            }
            alert(result.message || "문자 발송에 실패했습니다.");
        }
    } catch (error) {
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.textContent = "발송";
            sendButton.style.cursor = "pointer";
            sendButton.style.opacity = "1";
        }
        alert("문자 발송 중 오류가 발생했습니다: " + error.message);
    }
}

function logout() {
    localStorage.removeItem("adminToken");
    updateNavigation();
    window.location.href = "/admin-login.html";
}

