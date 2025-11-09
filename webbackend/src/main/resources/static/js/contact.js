document
  .getElementById("contactForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const formData = {
      name: document.getElementById("name").value,
      email: document.getElementById("email").value,
      phone: document.getElementById("phone").value,
      category: document.getElementById("category").value,
      subject: document.getElementById("subject").value,
      message: document.getElementById("message").value,
    };

    try {
      const response = await fetch("/api/contact/inquiry", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (result.success) {
        alert("문의가 접수되었습니다. 빠른 시일 내에 답변드리겠습니다.");
        this.reset();
      } else {
        alert("문의 접수에 실패했습니다: " + (result.message || "알 수 없는 오류"));
      }
    } catch (error) {
      alert("문의 접수 중 오류가 발생했습니다: " + error.message);
    }
  });

