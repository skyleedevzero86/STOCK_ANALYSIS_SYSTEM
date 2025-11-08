document
  .getElementById("contactForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = {
      name: document.getElementById("name").value,
      email: document.getElementById("email").value,
      phone: document.getElementById("phone").value,
      category: document.getElementById("category").value,
      subject: document.getElementById("subject").value,
      message: document.getElementById("message").value,
    };

    alert(
      "문의가 접수되었습니다. 빠른 시일 내에 답변드리겠습니다.\n\n문의 내용: " +
        formData.subject
    );

    this.reset();
  });

