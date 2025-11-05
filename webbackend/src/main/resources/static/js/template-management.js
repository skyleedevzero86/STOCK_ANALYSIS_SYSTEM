let templates = [];

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
    loadTemplates();
});

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
        const response = await fetch("/api/templates", {
            headers: headers
        });

        if (handleAuthError(response)) {
            return;
        }

        if (response.ok) {
            templates = await response.json();
            renderTemplates();
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
    templateList.innerHTML = "";

    templates.forEach((template) => {
        const templateItem = document.createElement("div");
        templateItem.className = "template-item";
        templateItem.innerHTML = `
      <div class="template-header">
        <div class="template-name">${template.name}</div>
        <div class="template-actions">
          <button class="btn" onclick="editTemplate(${
            template.id
        })">수정</button>
          <button class="btn btn-danger" onclick="deleteTemplate(${
            template.id
        })">삭제</button>
        </div>
      </div>
      <div class="template-content">
        <strong>제목:</strong> ${template.subject}<br>
        <strong>내용:</strong> ${template.content.substring(
            0,
            100
        )}...
      </div>
      <div class="template-meta">
        생성일: ${new Date(template.createdAt).toLocaleString()}
      </div>
    `;
        templateList.appendChild(templateItem);
    });
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

    const headers = getAuthHeaders();
    if (!headers) {
        return;
    }

    const resultArea = document.getElementById("emailResult");
    resultArea.style.display = "block";
    resultArea.textContent = "AI 분석 이메일 발송 중...";

    try {
        const templateId = templates.length > 0 ? templates[0].id : 1;

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
            const result = await response.json();
            resultArea.textContent = `AI 분석 이메일 발송 완료!\n\n템플릿: ${
                result.template
            }\n종목: ${result.symbol}\n구독자 수: ${
                result.totalSubscribers
            }\n\nAI 분석 결과:\n${
                result.aiAnalysis
            }\n\n발송 결과:\n${result.results.join("\n")}`;
        } else {
            const errorText = await response.text();
            console.error("AI 이메일 발송 실패:", response.status, errorText);
            resultArea.textContent = `AI 분석 이메일 발송에 실패했습니다. (${response.status})`;
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

    const headers = getAuthHeaders();
    if (!headers) {
        return;
    }

    const resultArea = document.getElementById("emailResult");
    resultArea.style.display = "block";
    resultArea.textContent = "대량 AI 분석 이메일 발송 중...";

    try {
        const templateId = templates.length > 0 ? templates[0].id : 1;

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
            const result = await response.json();
            resultArea.textContent = `대량 AI 분석 이메일 발송 완료!\n\n템플릿: ${
                result.template
            }\n종목들: ${result.symbols.join(", ")}\n구독자 수: ${
                result.totalSubscribers
            }\n\n발송 결과:\n${result.results
                .map(
                    (r) =>
                        `${r.symbol}: ${r.subscriber} - ${
                            r.success ? "성공" : "실패"
                        }`
                )
                .join("\n")}`;
        } else {
            const errorText = await response.text();
            console.error("대량 AI 이메일 발송 실패:", response.status, errorText);
            resultArea.textContent =
                `대량 AI 분석 이메일 발송에 실패했습니다. (${response.status})`;
        }
    } catch (error) {
        console.error("대량 AI 이메일 발송 오류:", error);
        resultArea.textContent = `오류 발생: ${error.message}`;
    }
}
