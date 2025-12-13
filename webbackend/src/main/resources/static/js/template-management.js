let templates = [];
let currentPage = 0;
let pageSize = 10;
let totalPages = 0;
let totalElements = 0;
let searchKeyword = "";

function getAuthToken() {
    const token = localStorage.getItem("adminToken");
    if (!token) {
        alert("관리자 로그인이 필요합니다.");
        window.location.href = "/admin-login.html";
        return null;
    }
    return token;
}

function getAuthHeaders() {
    const token = getAuthToken();
    if (!token) {
        return null;
    }
    return {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
    };
}

function handleAuthError(response) {
    if (response.status === 401) {
        localStorage.removeItem("adminToken");
        alert("세션이 만료되었습니다. 다시 로그인해주세요.");
        window.location.href = "/admin-login.html";
        return true;
    }
    return false;
}

document.addEventListener("DOMContentLoaded", function () {
    if (!getAuthToken()) {
        return;
    }
    initSectionNavigation();
    loadTemplates();
    
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener("input", function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchKeyword = this.value.trim();
                currentPage = 0;
                loadTemplates();
            }, 300);
        });
        
        searchInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                searchKeyword = this.value.trim();
                currentPage = 0;
                loadTemplates();
            }
        });
    }
});

function initSectionNavigation() {
    const hash = window.location.hash;
    const dropdownItems = document.querySelectorAll(".nav-dropdown-item");

    dropdownItems.forEach(item => {
        item.addEventListener("click", function(e) {
            e.preventDefault();
            const section = this.getAttribute("data-section");
            showSection(section);
            
            dropdownItems.forEach(i => i.classList.remove("active"));
            this.classList.add("active");
            
            window.location.hash = section;
        });
    });

    const createSection = document.getElementById("create-template-section");
    const aiEmailSection = document.getElementById("ai-email-section");
    
    if (hash) {
        const section = hash.substring(1);
        showSection(section);
        const activeItem = document.querySelector(`.nav-dropdown-item[data-section="${section}"]`);
        if (activeItem) {
            dropdownItems.forEach(i => i.classList.remove("active"));
            activeItem.classList.add("active");
        }
    } else {
        if (createSection) createSection.style.display = "block";
        if (aiEmailSection) aiEmailSection.style.display = "none";
        const firstItem = dropdownItems[0];
        if (firstItem) {
            dropdownItems.forEach(i => i.classList.remove("active"));
            firstItem.classList.add("active");
        }
    }
}

function showSection(sectionName) {
    const createSection = document.getElementById("create-template-section");
    const aiEmailSection = document.getElementById("ai-email-section");

    if (sectionName === "create-template") {
        if (createSection) createSection.style.display = "block";
        if (aiEmailSection) aiEmailSection.style.display = "none";
        loadTemplates();
    } else if (sectionName === "ai-email") {
        if (createSection) createSection.style.display = "none";
        if (aiEmailSection) aiEmailSection.style.display = "block";
    }
}

let isEditMode = false;
let editingTemplateId = null;

document
    .getElementById("templateForm")
    .addEventListener("submit", function (e) {
        e.preventDefault();
        if (isEditMode && editingTemplateId) {
            updateTemplate(editingTemplateId);
        } else {
            createTemplate();
        }
    });

async function loadTemplates() {
    const headers = getAuthHeaders();
    if (!headers) {
        return;
    }

    try {
        let url = `/api/templates?page=${currentPage}&size=${pageSize}`;
        if (searchKeyword) {
            url += `&keyword=${encodeURIComponent(searchKeyword)}`;
        }
        
        const response = await fetch(url, {
            headers: headers
        });

        if (handleAuthError(response)) {
            return;
        }

        if (response.ok) {
            const responseData = await response.json();
            console.log("템플릿 API 응답:", responseData);
            if (responseData.templates) {
                templates = Array.isArray(responseData.templates) ? responseData.templates : [];
                totalPages = responseData.totalPages || 0;
                totalElements = responseData.totalElements || 0;
                currentPage = responseData.currentPage || 0;
            } else if (Array.isArray(responseData)) {
                templates = responseData;
                totalPages = Math.ceil(responseData.length / pageSize);
                totalElements = responseData.length;
            } else {
                templates = [];
                totalPages = 0;
                totalElements = 0;
            }
            console.log("페이징 정보:", { currentPage, totalPages, totalElements, templatesCount: templates.length });
            renderTemplates();
            renderPagination();
        } else {
            const errorText = await response.text();
            console.error("템플릿 로드 실패:", response.status, errorText);
            alert(`템플릿 로드에 실패했습니다. (${response.status})`);
        }
    } catch (error) {
        console.error("템플릿 로드 오류:", error);
        alert("템플릿 로드 중 오류가 발생했습니다: " + error.message);
    }
}

function renderTemplates() {
    const templateList = document.getElementById("templateList");
    const templateSelect = document.getElementById("templateSelect");
    templateList.innerHTML = "";

    if (templateSelect) {
        templateSelect.innerHTML = '<option value="">템플릿을 선택하세요</option>';
    }

    if (templates.length === 0) {
        const message = searchKeyword 
            ? `"${searchKeyword}"에 대한 검색 결과가 없습니다.` 
            : "등록된 템플릿이 없습니다. 새 템플릿을 생성해주세요.";
        templateList.innerHTML = `<div class="no-templates">${message}</div>`;
        return;
    }

    templates.forEach((template) => {
        if (templateSelect) {
            const option = document.createElement("option");
            option.value = template.id;
            option.textContent = template.name;
            templateSelect.appendChild(option);
        }

        const templateItem = document.createElement("div");
        templateItem.className = "template-board-item";
        templateItem.innerHTML = `
      <div class="template-board-header" onclick="toggleTemplateDetails(${template.id})" data-template-id="${template.id}">
        <div class="template-board-title">
          <div class="template-board-title-name">${template.name}</div>
          <div class="template-board-title-subject">${template.subject}</div>
        </div>
        <div class="template-board-actions">
          <span class="template-board-toggle">▼</span>
          <button class="btn" onclick="event.stopPropagation(); editTemplate(${template.id})">수정</button>
          <button class="btn btn-danger" onclick="event.stopPropagation(); deleteTemplate(${template.id})">삭제</button>
        </div>
      </div>
      <div class="template-board-content" id="template-content-${template.id}">
        <div class="template-board-details">
          <div class="template-board-details-item">
            <span class="template-board-details-label">이메일 제목:</span>
            <span class="template-board-details-value">${template.subject}</span>
          </div>
          <div class="template-board-details-item">
            <span class="template-board-details-label">이메일 내용:</span>
            <div class="template-board-details-value" style="white-space: pre-wrap; margin-top: 8px;">${template.content || "(내용 없음)"}</div>
          </div>
          <div class="template-board-details-item">
            <span class="template-board-details-label">생성일:</span>
            <span class="template-board-details-value">${template.createdAt ? new Date(template.createdAt).toLocaleString() : "-"}</span>
          </div>
        </div>
        <div class="template-board-history">
          <div class="template-board-history-title">발송 내역</div>
          <div class="template-board-history-list" id="template-history-${template.id}">
            <div style="text-align: center; padding: 20px; color: #999;">로딩 중...</div>
          </div>
        </div>
      </div>
    `;
        templateList.appendChild(templateItem);
    });
}

function renderPagination() {
    const pagination = document.getElementById("pagination");
    if (!pagination) {
        console.warn("pagination 요소를 찾을 수 없습니다");
        return;
    }
    
    if (totalPages <= 1 && totalElements === 0) {
        pagination.innerHTML = "";
        return;
    }
    
    let paginationHTML = "";
    
    if (totalPages > 1) {
        if (currentPage > 0) {
            paginationHTML += `<button onclick="goToPage(${currentPage - 1})" style="
                padding: 8px 16px;
                border: 1px solid #ddd;
                background: #fff;
                border-radius: 4px;
                cursor: pointer;
                margin-right: 4px;
            ">이전</button>`;
        }
        
        const startPage = Math.max(0, currentPage - 2);
        const endPage = Math.min(totalPages - 1, currentPage + 2);
        
        if (startPage > 0) {
            paginationHTML += `<button onclick="goToPage(0)" style="
                padding: 8px 12px;
                border: 1px solid #ddd;
                background: #fff;
                border-radius: 4px;
                cursor: pointer;
                margin-right: 4px;
            ">1</button>`;
            if (startPage > 1) {
                paginationHTML += `<span style="padding: 8px; margin-right: 4px;">...</span>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            if (i === currentPage) {
                paginationHTML += `<button style="
                    padding: 8px 12px;
                    border: 1px solid #2f456e;
                    background: #2f456e;
                    color: #fff;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                    margin-right: 4px;
                ">${i + 1}</button>`;
            } else {
                paginationHTML += `<button onclick="goToPage(${i})" style="
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    background: #fff;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-right: 4px;
                ">${i + 1}</button>`;
            }
        }
        
        if (endPage < totalPages - 1) {
            if (endPage < totalPages - 2) {
                paginationHTML += `<span style="padding: 8px; margin-right: 4px;">...</span>`;
            }
            paginationHTML += `<button onclick="goToPage(${totalPages - 1})" style="
                padding: 8px 12px;
                border: 1px solid #ddd;
                background: #fff;
                border-radius: 4px;
                cursor: pointer;
                margin-right: 4px;
            ">${totalPages}</button>`;
        }
        
        if (currentPage < totalPages - 1) {
            paginationHTML += `<button onclick="goToPage(${currentPage + 1})" style="
                padding: 8px 16px;
                border: 1px solid #ddd;
                background: #fff;
                border-radius: 4px;
                cursor: pointer;
                margin-right: 4px;
            ">다음</button>`;
        }
    }
    
    paginationHTML += `<span style="margin-left: 20px; color: #666; font-size: 0.9rem;">총 ${totalElements}개`;
    if (totalPages > 1) {
        paginationHTML += ` (${currentPage + 1}/${totalPages} 페이지)`;
    }
    paginationHTML += `</span>`;
    
    pagination.innerHTML = paginationHTML;
}

function goToPage(page) {
    currentPage = page;
    loadTemplates();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function toggleTemplateDetails(templateId) {
    const header = document.querySelector(`[data-template-id="${templateId}"]`);
    const content = document.getElementById(`template-content-${templateId}`);
    const historyList = document.getElementById(`template-history-${templateId}`);
    
    if (!header || !content) return;
    
    const isExpanded = header.classList.contains("active");
    
    if (isExpanded) {
        header.classList.remove("active");
        content.classList.remove("expanded");
    } else {
        header.classList.add("active");
        content.classList.add("expanded");
        
        if (historyList && historyList.innerHTML.includes("로딩 중")) {
            await loadTemplateHistory(templateId);
        }
    }
}

async function loadTemplateHistory(templateId) {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;
    
    const historyList = document.getElementById(`template-history-${templateId}`);
    if (!historyList) return;
    
    const headers = getAuthHeaders();
    if (!headers) return;
    
    try {
        const response = await fetch(`/api/templates/${templateId}/email-history?page=0&size=50`, {
            headers: headers
        });
        
        if (handleAuthError(response)) {
            return;
        }
        
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.data) {
                const logs = result.data.logs || [];
                displayTemplateHistory(templateId, logs);
            } else {
                historyList.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">발송 내역이 없습니다.</div>';
            }
        } else {
            historyList.innerHTML = '<div style="text-align: center; padding: 20px; color: #e74c3c;">발송 내역을 불러올 수 없습니다.</div>';
        }
    } catch (error) {
        console.error("발송 내역 로드 오류:", error);
        historyList.innerHTML = '<div style="text-align: center; padding: 20px; color: #e74c3c;">오류가 발생했습니다.</div>';
    }
}

function displayTemplateHistory(templateId, logs) {
    const historyList = document.getElementById(`template-history-${templateId}`);
    if (!historyList) return;
    
    if (!logs || logs.length === 0) {
        historyList.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">발송 내역이 없습니다.</div>';
        return;
    }
    
    historyList.innerHTML = logs.map(log => {
        const statusClass = log.status === "SENT" ? "sent" : "failed";
        const statusText = log.status === "SENT" ? "성공" : "실패";
        const itemClass = log.status === "SENT" ? "" : "failed";
        const sentDate = new Date(log.sentAt).toLocaleString();
        const messagePreview = log.message ? (log.message.length > 100 ? log.message.substring(0, 100) + "..." : log.message) : "-";
        
        return `
          <div class="template-board-history-item ${itemClass}">
            <div class="template-board-history-header">
              <span class="template-board-history-email">${log.userEmail}</span>
              <span class="template-board-history-status ${statusClass}">${statusText}</span>
            </div>
            <div class="template-board-history-meta">
              <span>발송일: ${sentDate}</span>
              ${log.symbol ? `<span>종목: ${log.symbol}</span>` : ""}
            </div>
            <div class="template-board-history-message">${messagePreview}</div>
            ${log.errorMessage ? `<div style="margin-top: 8px; color: #e74c3c; font-size: 0.75rem;">오류: ${log.errorMessage}</div>` : ""}
          </div>
        `;
    }).join("");
}

async function createTemplate() {
    const headers = getAuthHeaders();
    if (!headers) {
        return;
    }

    const name = document.getElementById("templateName").value;
    const subject = document.getElementById("templateSubject").value;
    const content = document.getElementById("templateContent").value;

    if (!name || !subject || !content) {
        alert("모든 필드를 입력해주세요.");
        return;
    }

    try {
        const response = await fetch("/api/templates", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({ name, subject, content }),
        });

        if (handleAuthError(response)) {
            return;
        }

        if (response.ok) {
            alert("템플릿이 생성되었습니다.");
            document.getElementById("templateForm").reset();
            
            isEditMode = false;
            editingTemplateId = null;
            
            currentPage = 0;
            searchKeyword = "";
            const searchInput = document.getElementById("searchInput");
            if (searchInput) {
                searchInput.value = "";
            }
            loadTemplates();
        } else {
            const errorText = await response.text();
            console.error("템플릿 생성 실패:", response.status, errorText);
            alert(`템플릿 생성에 실패했습니다. (${response.status})`);
        }
    } catch (error) {
        console.error("템플릿 생성 오류:", error);
        alert("템플릿 생성 중 오류가 발생했습니다: " + error.message);
    }
}

async function editTemplate(id) {
    const template = templates.find((t) => t.id === id);
    if (!template) {
        alert("템플릿을 찾을 수 없습니다.");
        return;
    }

    document.getElementById("templateName").value = template.name;
    document.getElementById("templateSubject").value = template.subject;
    document.getElementById("templateContent").value = template.content;

    isEditMode = true;
    editingTemplateId = id;
    
    const submitButton = document.getElementById("templateForm").querySelector('button[type="submit"]');
    submitButton.textContent = "템플릿 수정";
    
    document.getElementById("templateForm").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function updateTemplate(id) {
    const headers = getAuthHeaders();
    if (!headers) {
        return;
    }

    const name = document.getElementById("templateName").value;
    const subject = document.getElementById("templateSubject").value;
    const content = document.getElementById("templateContent").value;

    if (!name || !subject || !content) {
        alert("모든 필드를 입력해주세요.");
        return;
    }

    try {
        const response = await fetch(`/api/templates/${id}`, {
            method: "PUT",
            headers: headers,
            body: JSON.stringify({ name, subject, content }),
        });

        if (handleAuthError(response)) {
            return;
        }

        if (response.ok) {
            alert("템플릿이 수정되었습니다.");
            document.getElementById("templateForm").reset();
            const submitButton = document.getElementById("templateForm").querySelector('button[type="submit"]');
            submitButton.textContent = "템플릿 생성";
            
            isEditMode = false;
            editingTemplateId = null;
            
            loadTemplates();
        } else {
            const errorText = await response.text();
            console.error("템플릿 수정 실패:", response.status, errorText);
            alert(`템플릿 수정에 실패했습니다. (${response.status})`);
        }
    } catch (error) {
        console.error("템플릿 수정 오류:", error);
        alert("템플릿 수정 중 오류가 발생했습니다: " + error.message);
    }
}

async function deleteTemplate(id) {
    if (!confirm("정말로 이 템플릿을 삭제하시겠습니까?")) {
        return;
    }

    const headers = getAuthHeaders();
    if (!headers) {
        return;
    }

    try {
        const response = await fetch(`/api/templates/${id}`, {
            method: "DELETE",
            headers: headers
        });

        if (handleAuthError(response)) {
            return;
        }

        if (response.ok) {
            alert("템플릿이 삭제되었습니다.");
            if (templates.length === 1 && currentPage > 0) {
                currentPage--;
            }
            loadTemplates();
        } else {
            const errorText = await response.text();
            console.error("템플릿 삭제 실패:", response.status, errorText);
            alert(`템플릿 삭제에 실패했습니다. (${response.status})`);
        }
    } catch (error) {
        console.error("템플릿 삭제 오류:", error);
        alert("템플릿 삭제 중 오류가 발생했습니다: " + error.message);
    }
}

async function sendAIEmail() {
    const symbol = document.getElementById("symbolInput").value.trim();
    if (!symbol) {
        alert("종목 심볼을 입력해주세요.");
        return;
    }

    const templateSelect = document.getElementById("templateSelect");
    const templateId = templateSelect ? templateSelect.value : null;
    
    if (!templateId || templateId === "") {
        alert("템플릿을 선택해주세요.");
        return;
    }

    const headers = getAuthHeaders();
    if (!headers) {
        return;
    }

    const resultArea = document.getElementById("emailResult");
    resultArea.style.display = "block";
    resultArea.textContent = "AI 분석 이메일 발송 중...";

    try {
        const response = await fetch(
            `/api/ai-email/send/${templateId}/${symbol}`,
            {
                method: "POST",
                headers: headers
            }
        );

        if (handleAuthError(response)) {
            resultArea.style.display = "none";
            return;
        }

        if (response.ok) {
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                const text = await response.text();
                console.error("AI 이메일 발송 응답 오류: JSON이 아닌 응답", text);
                resultArea.textContent = `서버 응답 오류: 유효하지 않은 응답 형식입니다.`;
                return;
            }

            try {
                const text = await response.text();
                if (!text || text.trim() === "") {
                    console.error("AI 이메일 발송 응답 오류: 빈 응답");
                    resultArea.textContent = `서버 응답 오류: 빈 응답을 받았습니다.`;
                    return;
                }

                const result = JSON.parse(text);
                resultArea.textContent = `AI 분석 이메일 발송 완료!\n\n템플릿: ${
                    result.template || "N/A"
                }\n종목: ${result.symbol || "N/A"}\n구독자 수: ${
                    result.totalSubscribers || 0
                }\n\nAI 분석 결과:\n${
                    result.aiAnalysis || "분석 결과 없음"
                }\n\n발송 결과:\n${(result.results || []).join("\n")}`;
            } catch (jsonError) {
                console.error("AI 이메일 발송 JSON 파싱 오류:", jsonError);
                resultArea.textContent = `응답 파싱 오류: 서버 응답을 처리할 수 없습니다.`;
            }
        } else {
            let errorText = "";
            try {
                errorText = await response.text();
                if (errorText) {
                    try {
                        const errorJson = JSON.parse(errorText);
                        errorText = errorJson.message || errorJson.detail || errorText;
                    } catch (e) {
                    }
                }
            } catch (e) {
                errorText = `HTTP ${response.status}`;
            }
            console.error("AI 이메일 발송 실패:", response.status, errorText);
            resultArea.textContent = `AI 분석 이메일 발송에 실패했습니다. (${response.status})\n${errorText ? `\n오류: ${errorText}` : ""}`;
        }
    } catch (error) {
        console.error("AI 이메일 발송 오류:", error);
        resultArea.textContent = `오류 발생: ${error.message}`;
    }
}

async function sendBulkAIEmail() {
    const symbolsText = document
        .getElementById("bulkSymbolsInput")
        .value.trim();
    if (!symbolsText) {
        alert("종목 심볼들을 입력해주세요.");
        return;
    }

    const symbols = symbolsText
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s);
    if (symbols.length === 0) {
        alert("유효한 종목 심볼을 입력해주세요.");
        return;
    }

    const templateSelect = document.getElementById("templateSelect");
    const templateId = templateSelect ? templateSelect.value : null;
    
    if (!templateId || templateId === "") {
        alert("템플릿을 선택해주세요.");
        return;
    }

    const headers = getAuthHeaders();
    if (!headers) {
        return;
    }

    const resultArea = document.getElementById("emailResult");
    resultArea.style.display = "block";
    resultArea.textContent = "대량 AI 분석 이메일 발송 중...";

    try {
        const response = await fetch(
            `/api/ai-email/send-bulk/${templateId}`,
            {
                method: "POST",
                headers: headers,
                body: JSON.stringify(symbols),
            }
        );

        if (handleAuthError(response)) {
            resultArea.style.display = "none";
            return;
        }

        if (response.ok) {
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                const text = await response.text();
                console.error("대량 AI 이메일 발송 응답 오류: JSON이 아닌 응답", text);
                resultArea.textContent = `서버 응답 오류: 유효하지 않은 응답 형식입니다.`;
                return;
            }

            try {
                const text = await response.text();
                if (!text || text.trim() === "") {
                    console.error("대량 AI 이메일 발송 응답 오류: 빈 응답");
                    resultArea.textContent = `서버 응답 오류: 빈 응답을 받았습니다.`;
                    return;
                }

                const result = JSON.parse(text);
                resultArea.textContent = `대량 AI 분석 이메일 발송 완료!\n\n템플릿: ${
                    result.template || "N/A"
                }\n종목들: ${(result.symbols || []).join(", ")}\n구독자 수: ${
                    result.totalSubscribers || 0
                }\n\n발송 결과:\n${(result.results || [])
                    .map(
                        (r) =>
                            `${r.symbol || "N/A"}: ${r.subscriber || "N/A"} - ${
                                r.success ? "성공" : "실패"
                            }`
                    )
                    .join("\n")}`;
            } catch (jsonError) {
                console.error("대량 AI 이메일 발송 JSON 파싱 오류:", jsonError);
                resultArea.textContent = `응답 파싱 오류: 서버 응답을 처리할 수 없습니다.`;
            }
        } else {
            let errorText = "";
            try {
                errorText = await response.text();
                if (errorText) {
                    try {
                        const errorJson = JSON.parse(errorText);
                        errorText = errorJson.message || errorJson.detail || errorText;
                    } catch (e) {
                    }
                }
            } catch (e) {
                errorText = `HTTP ${response.status}`;
            }
            console.error("대량 AI 이메일 발송 실패:", response.status, errorText);
            resultArea.textContent =
                `대량 AI 분석 이메일 발송에 실패했습니다. (${response.status})\n${errorText ? `\n오류: ${errorText}` : ""}`;
        }
    } catch (error) {
        console.error("대량 AI 이메일 발송 오류:", error);
        resultArea.textContent = `오류 발생: ${error.message}`;
    }
}
