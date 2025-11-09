document.addEventListener("DOMContentLoaded", function() {
    const adminToken = localStorage.getItem("adminToken");
    if (adminToken) {
        console.log("로그인 페이지에서 토큰 발견 - 대시보드로 리다이렉트");
        setTimeout(function() {
            window.location.href = "/admin-dashboard.html";
        }, 100);
        return;
    }
    
    updateNavigation();
    
        const loginForm = document.getElementById("loginForm");
        if (!loginForm) {
            console.error("로그인 폼을 찾을 수 없습니다!");
            return;
        }
        
        loginForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            console.log("로그인 폼 제출됨");

            const formData = new FormData(this);
            const data = {
                email: formData.get("email"),
                password: formData.get("password"),
            };
            
            console.log("로그인 데이터:", { email: data.email, password: "***" });

            try {
                console.log("로그인 요청 시작:", data);
                const response = await fetch("/api/admin/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(data),
                });

                console.log("응답 상태:", response.status, response.statusText);
                
                if (!response.ok) {
                    console.error("HTTP 오류:", response.status);
                    const errorText = await response.text();
                    console.error("오류 응답:", errorText);
                    showStatusMessage(false, `로그인 실패: ${response.status} ${response.statusText}`);
                    return;
                }

                const result = await response.json();
                console.log("로그인 응답:", result);

                if (result.success && result.data && result.data.token) {
                    const token = result.data.token;
                    localStorage.setItem("adminToken", token);
                    
                    const verifyToken = localStorage.getItem("adminToken");
                    console.log("토큰 저장 완료:", token);
                    console.log("토큰 저장 검증:", verifyToken ? "성공" : "실패");
                    console.log("저장된 토큰과 응답 토큰 일치:", verifyToken === token);
                    
                    if (!verifyToken || verifyToken !== token) {
                        console.error("토큰 저장 실패!");
                        showStatusMessage(false, "토큰 저장에 실패했습니다. 다시 시도해주세요.");
                        return;
                    }
                    
                    showStatusMessage(
                        true,
                        "로그인 성공! 구독자 목록 페이지로 이동합니다."
                    );

                    setTimeout(() => {
                        const savedToken = localStorage.getItem("adminToken");
                        console.log("리다이렉트 전 토큰 재확인:", savedToken ? "있음" : "없음");
                        if (savedToken && savedToken === token) {
                            console.log("대시보드로 리다이렉트 시작");
                            window.location.href = "/admin-dashboard.html";
                        } else {
                            console.error("토큰이 저장되지 않았거나 변경되었습니다!");
                            console.error("원본 토큰:", token);
                            console.error("저장된 토큰:", savedToken);
                            showStatusMessage(false, "토큰 저장에 실패했습니다. 다시 시도해주세요.");
                        }
                    }, 1000);
                } else {
                    console.error("로그인 실패:", result);
                    showStatusMessage(false, result.message || "로그인에 실패했습니다.");
                }
            } catch (error) {
                console.error("로그인 오류:", error);
                showStatusMessage(false, "로그인 중 오류가 발생했습니다: " + error.message);
            }
        });
});

function showStatusMessage(success, message) {
    const statusDiv = document.getElementById("statusMessage");
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${
        success ? "status-success" : "status-error"
    }`;
    statusDiv.style.display = "block";

    setTimeout(() => {
        statusDiv.style.display = "none";
    }, 5000);
}
