async function testEndpoint(url, method) {
    try {
        const response = await fetch(url, { method });
        const data = await response.json();

        const responseId = `response-${url.split("/").pop()}`;
        const contentId = `content-${url.split("/").pop()}`;

        document.getElementById(responseId).style.display = "block";
        document.getElementById(contentId).textContent = JSON.stringify(
            data,
            null,
            2
        );
    } catch (error) {
        alert("API 호출 중 오류가 발생했습니다: " + error.message);
    }
}

async function testSubscribe() {
    const testData = {
        name: "테스트 사용자",
        email: "test@example.com",
        phone: "010-1234-5678",
        isEmailConsent: true,
        isPhoneConsent: false,
    };

    try {
        const response = await fetch("/api/email-subscriptions/subscribe", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(testData),
        });

        const data = await response.json();

        document.getElementById("response-subscribe").style.display = "block";
        document.getElementById("content-subscribe").textContent =
            JSON.stringify(data, null, 2);
    } catch (error) {
        alert("구독 테스트 중 오류가 발생했습니다: " + error.message);
    }
}

async function testAdminLogin() {
    const testData = {
        email: "admin@admin.com",
        password: "1234",
    };

    try {
        const response = await fetch("/api/admin/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(testData),
        });

        const data = await response.json();

        document.getElementById("response-admin-login").style.display =
            "block";
        document.getElementById("content-admin-login").textContent =
            JSON.stringify(data, null, 2);
    } catch (error) {
        alert(
            "관리자 로그인 테스트 중 오류가 발생했습니다: " + error.message
        );
    }
}
