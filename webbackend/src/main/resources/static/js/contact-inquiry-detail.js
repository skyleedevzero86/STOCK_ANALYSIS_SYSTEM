let inquiryId = null;

function getCategoryName(category) {
    const categoryMap = {
        "service": "서비스 이용 문의",
        "api": "API 사용 문의",
        "data": "데이터 정확성 문의",
        "technical": "기술적 문제",
        "subscription": "구독 관리",
        "other": "기타"
    };
    return categoryMap[category] || category;
}

document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        const adminToken = localStorage.getItem("adminToken");
        if (!adminToken) {
            window.location.href = "/admin-login.html";
            return;
        }

        const urlParams = new URLSearchParams(window.location.search);
        inquiryId = urlParams.get("id");

        if (!inquiryId) {
            alert("잘못된 접근입니다.");
            window.location.href = "/contact-inquiry-list.html";
            return;
        }

        updateNavigation();
        loadInquiryDetail();
    }, 1000);
});

async function loadInquiryDetail() {
    const adminToken = localStorage.getItem("adminToken");
    
    if (!adminToken) {
        window.location.href = "/admin-login.html";
        return;
    }

    if (!inquiryId) {
        showError("문의사항 ID가 없습니다.");
        return;
    }

    const detailContent = document.getElementById("inquiryDetailContent");
    const repliesContent = document.getElementById("repliesContent");
    
    detailContent.innerHTML = '<div class="loading">데이터를 불러오는 중...</div>';
    repliesContent.innerHTML = '<div class="loading">답변을 불러오는 중...</div>';

    try {
        const response = await fetch(`/api/contact/inquiries/${inquiryId}`, {
            headers: {
                Authorization: adminToken,
            },
        });

        if (response.status === 401) {
            localStorage.removeItem("adminToken");
            window.location.href = "/admin-login.html";
            return;
        }

        if (!response.ok) {
            showError("데이터를 불러오는 중 오류가 발생했습니다: " + response.status);
            return;
        }

        const result = await response.json();

        if (result.success) {
            const inquiry = result.data.inquiry;
            const replies = result.data.replies || [];

            displayInquiryDetail(inquiry);
            displayReplies(replies);
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

function displayInquiryDetail(inquiry) {
    const content = document.getElementById("inquiryDetailContent");

    const html = `
        <div style="margin-bottom: 24px">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px">
                <div>
                    <strong>이름:</strong> ${inquiry.name}
                </div>
                <div>
                    <strong>이메일:</strong> ${inquiry.email}
                </div>
                <div>
                    <strong>전화번호:</strong> ${inquiry.phone || "-"}
                </div>
                <div>
                    <strong>카테고리:</strong> ${getCategoryName(inquiry.category)}
                </div>
                <div>
                    <strong>작성일:</strong> ${new Date(inquiry.createdAt).toLocaleString()}
                </div>
                <div>
                    <strong>읽음 상태:</strong> 
                    <span class="status-badge ${inquiry.isRead ? "status-active" : "status-inactive"}">
                        ${inquiry.isRead ? "읽음" : "안읽음"}
                    </span>
                </div>
            </div>
            <div style="margin-bottom: 16px">
                <strong>제목:</strong>
                <div style="padding: 12px; background: #f5f5f5; border-radius: 8px; margin-top: 8px">
                    ${inquiry.subject}
                </div>
            </div>
            <div>
                <strong>내용:</strong>
                <div style="padding: 12px; background: #f5f5f5; border-radius: 8px; margin-top: 8px; white-space: pre-wrap">
                    ${inquiry.message}
                </div>
            </div>
        </div>
    `;

    content.innerHTML = html;
}

function displayReplies(replies) {
    const content = document.getElementById("repliesContent");

    if (replies.length === 0) {
        content.innerHTML = '<div class="loading">등록된 답변이 없습니다.</div>';
        return;
    }

    const html = replies.map((reply, index) => `
        <div style="padding: 16px; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 12px; background: #f9f9f9">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px">
                <div>
                    <strong>${reply.createdBy}</strong>
                </div>
                <div style="color: #666; font-size: 0.875rem">
                    ${new Date(reply.createdAt).toLocaleString()}
                </div>
            </div>
            <div style="white-space: pre-wrap; line-height: 1.6">
                ${reply.content}
            </div>
        </div>
    `).join("");

    content.innerHTML = html;
}

async function addReply() {
    const adminToken = localStorage.getItem("adminToken");
    if (!adminToken) {
        alert("인증이 필요합니다.");
        return;
    }

    const contentInput = document.getElementById("replyContent");
    const content = contentInput.value.trim();

    if (!content) {
        alert("답변 내용을 입력해주세요.");
        return;
    }

    try {
        const response = await fetch(`/api/contact/inquiries/${inquiryId}/reply`, {
            method: "POST",
            headers: {
                Authorization: adminToken,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                content: content,
                createdBy: "관리자"
            }),
        });

        if (response.status === 401) {
            localStorage.removeItem("adminToken");
            window.location.href = "/admin-login.html";
            return;
        }

        const result = await response.json();

        if (result.success) {
            contentInput.value = "";
            alert("답변이 성공적으로 등록되었습니다.");
            loadInquiryDetail();
        } else {
            alert(result.message || "답변 등록에 실패했습니다.");
        }
    } catch (error) {
        alert("답변 등록 중 오류가 발생했습니다: " + error.message);
    }
}

function showError(message) {
    const content = document.getElementById("inquiryDetailContent");
    content.innerHTML = `<div class="error">${message}</div>`;
}

function logout() {
    localStorage.removeItem("adminToken");
    updateNavigation();
    window.location.href = "/admin-login.html";
}

