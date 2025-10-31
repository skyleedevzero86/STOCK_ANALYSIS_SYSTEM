document
    .getElementById("subscriptionForm")
    .addEventListener("submit", async function (e) {
        e.preventDefault();

        const formData = new FormData(this);
        const data = {
            name: formData.get("name"),
            email: formData.get("email"),
            phone: formData.get("phone"),
            isEmailConsent: formData.get("emailConsent") === "on",
            isPhoneConsent: formData.get("phoneConsent") === "on",
        };

        try {
            const response = await fetch("/api/email-subscriptions/subscribe", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();
            showStatusMessage(result.success, result.message);

            if (result.success) {
                document.getElementById("subscriptionForm").reset();
            }
        } catch (error) {
            showStatusMessage(false, "구독 신청 중 오류가 발생했습니다.");
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
