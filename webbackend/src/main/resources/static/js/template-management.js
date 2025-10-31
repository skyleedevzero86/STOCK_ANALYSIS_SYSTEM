let templates = [];
let authToken = localStorage.getItem("adminToken");

document.addEventListener("DOMContentLoaded", function () {
    if (!authToken) {
        alert("관리자 로그인이 필요합니다.");
        window.location.href = "/admin-login.html";
        return;
    }
    loadTemplates();
});

document
    .getElementById("templateForm")
    .addEventListener("submit", function (e) {
        e.preventDefault();
        createTemplate();
    });

async function loadTemplates() {
    try {
        const response = await fetch("/api/templates", {
            headers: {
                Authorization: `Bearer ${authToken}`,
            },
        });

        if (response.ok) {
            templates = await response.json();
            renderTemplates();
        } else {
            console.error("템플릿 로드 실패");
        }
    } catch (error) {
        console.error("템플릿 로드 오류:", error);
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
    const name = document.getElementById("templateName").value;
    const subject = document.getElementById("templateSubject").value;
    const content = document.getElementById("templateContent").value;

    try {
        const response = await fetch("/api/templates", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${authToken}`,
            },
            body: JSON.stringify({ name, subject, content }),
        });

        if (response.ok) {
            alert("템플릿이 생성되었습니다.");
            document.getElementById("templateForm").reset();
            loadTemplates();
        } else {
            alert("템플릿 생성에 실패했습니다.");
        }
    } catch (error) {
        console.error("템플릿 생성 오류:", error);
        alert("템플릿 생성 중 오류가 발생했습니다.");
    }
}

async function deleteTemplate(id) {
    if (!confirm("정말로 이 템플릿을 삭제하시겠습니까?")) {
        return;
    }

    try {
        const response = await fetch(`/api/templates/${id}`, {
            method: "DELETE",
            headers: {
                Authorization: `Bearer ${authToken}`,
            },
        });

        if (response.ok) {
            alert("템플릿이 삭제되었습니다.");
            loadTemplates();
        } else {
            alert("템플릿 삭제에 실패했습니다.");
        }
    } catch (error) {
        console.error("템플릿 삭제 오류:", error);
        alert("템플릿 삭제 중 오류가 발생했습니다.");
    }
}

async function sendAIEmail() {
    const symbol = document.getElementById("symbolInput").value.trim();
    if (!symbol) {
        alert("종목 심볼을 입력해주세요.");
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
                headers: {
                    Authorization: `Bearer ${authToken}`,
                },
            }
        );

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
            resultArea.textContent = "AI 분석 이메일 발송에 실패했습니다.";
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

    const resultArea = document.getElementById("emailResult");
    resultArea.style.display = "block";
    resultArea.textContent = "대량 AI 분석 이메일 발송 중...";

    try {
        const templateId = templates.length > 0 ? templates[0].id : 1;

        const response = await fetch(
            `/api/ai-email/send-bulk/${templateId}`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${authToken}`,
                },
                body: JSON.stringify(symbols),
            }
        );

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
            resultArea.textContent =
                "대량 AI 분석 이메일 발송에 실패했습니다.";
        }
    } catch (error) {
        console.error("대량 AI 이메일 발송 오류:", error);
        resultArea.textContent = `오류 발생: ${error.message}`;
    }
}
