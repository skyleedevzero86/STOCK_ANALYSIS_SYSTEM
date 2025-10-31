document
    .getElementById("loginForm")
    .addEventListener("submit", async function (e) {
        e.preventDefault();

        const formData = new FormData(this);
        const data = {
            email: formData.get("email"),
            password: formData.get("password"),
        };

        try {
            const response = await fetch("/api/admin/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (result.success) {
                localStorage.setItem("adminToken", result.data.token);
                updateNavigation();
                showStatusMessage(
                    true,
                    "로그인 성공! 구독자 목록 페이지로 이동합니다."
                );

                setTimeout(() => {
                    window.location.href = "/admin-dashboard.html";
                }, 2000);
            } else {
                showStatusMessage(false, result.message);
            }
        } catch (error) {
            showStatusMessage(false, "로그인 중 오류가 발생했습니다.");
        }
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
