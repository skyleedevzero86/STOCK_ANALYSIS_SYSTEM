let adminToken = localStorage.getItem("adminToken");

if (!adminToken) {
    window.location.href = "/admin-login.html";
}

async function loadSubscriptions() {
    try {
        const response = await fetch("/api/admin/subscriptions", {
            headers: {
                Authorization: adminToken,
            },
        });

        const result = await response.json();

        if (result.success) {
            displaySubscriptions(result.data.subscriptions);
            updateStats(result.data.subscriptions);
        } else {
            if (result.message.includes("인증")) {
                localStorage.removeItem("adminToken");
                window.location.href = "/admin-login.html";
            } else {
                showError(result.message);
            }
        }
    } catch (error) {
        showError("데이터를 불러오는 중 오류가 발생했습니다.");
    }
}

function displaySubscriptions(subscriptions) {
    const content = document.getElementById("subscriptionsContent");

    if (subscriptions.length === 0) {
        content.innerHTML = '<div class="loading">구독자가 없습니다.</div>';
        return;
    }

    const table = `
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>이름</th>
          <th>이메일</th>
          <th>전화번호</th>
          <th>이메일 동의</th>
          <th>전화 동의</th>
          <th>가입일</th>
          <th>상태</th>
        </tr>
      </thead>
      <tbody>
        ${subscriptions
        .map(
            (sub) => `
            <tr>
              <td>${sub.id}</td>
              <td>${sub.name}</td>
              <td>${sub.email}</td>
              <td>${sub.phone || "-"}</td>
              <td><span class="consent-badge ${
                sub.isEmailConsent
                    ? "consent-yes"
                    : "consent-no"
            }">${
                sub.isEmailConsent ? "동의" : "비동의"
            }</span></td>
              <td><span class="consent-badge ${
                sub.isPhoneConsent
                    ? "consent-yes"
                    : "consent-no"
            }">${
                sub.isPhoneConsent ? "동의" : "비동의"
            }</span></td>
              <td>${new Date(
                sub.createdAt
            ).toLocaleDateString()}</td>
              <td><span class="status-badge ${
                sub.isActive
                    ? "status-active"
                    : "status-inactive"
            }">${
                sub.isActive ? "활성" : "비활성"
            }</span></td>
            </tr>
        `
        )
        .join("")}
      </tbody>
    </table>
  `;

    content.innerHTML = table;
}

function updateStats(subscriptions) {
    document.getElementById("totalSubscriptions").textContent =
        subscriptions.length;
    document.getElementById("emailConsentSubscriptions").textContent =
        subscriptions.filter((sub) => sub.isEmailConsent).length;
    document.getElementById("phoneConsentSubscriptions").textContent =
        subscriptions.filter((sub) => sub.isPhoneConsent).length;
}

function showError(message) {
    const content = document.getElementById("subscriptionsContent");
    content.innerHTML = `<div class="error">${message}</div>`;
}

function logout() {
    localStorage.removeItem("adminToken");
    updateNavigation();
    window.location.href = "/admin-login.html";
}

loadSubscriptions();
