let currentPage = 0;
let pageSize = 10;
let totalPages = 0;
let totalCount = 0;
let searchKeyword = "";
let searchCategory = "";

function getCategoryName(category) {
    const categoryMap = {
        "service": "서비스 이용 문의",
        "api": "API 사용 문의",
        "data": "데이터 정확성 문의",
        "technical": "기술적 문제",
        "subscription": "구독 관리",
        "other": "기타"
    };
    return categoryMap[category] || category;
}

async function loadInquiries(page = 0) {
    const adminToken = localStorage.getItem("adminToken");
    
    if (!adminToken) {
        window.location.href = "/admin-login.html";
        return;
    }

    currentPage = page;
    const keywordParam = searchKeyword ? `&keyword=${encodeURIComponent(searchKeyword)}` : "";
    const categoryParam = searchCategory ? `&category=${encodeURIComponent(searchCategory)}` : "";

    try {
        const response = await fetch(`/api/contact/inquiries?page=${page}&size=${pageSize}${keywordParam}${categoryParam}`, {
            headers: {
                Authorization: adminToken,
            },
        });

        if (response.status === 401) {
            localStorage.removeItem("adminToken");
            window.location.href = "/admin-login.html";
            return;
        }

        if (!response.ok) {
            showError("데이터를 불러오는 중 오류가 발생했습니다: " + response.status);
            return;
        }

        const result = await response.json();

        if (result.success) {
            currentPage = result.data.page || 0;
            totalPages = result.data.totalPages || 0;
            totalCount = result.data.total || 0;
            displayInquiries(result.data.inquiries);
            updatePagination();
        } else {
            if (result.message && result.message.includes("인증")) {
                localStorage.removeItem("adminToken");
                window.location.href = "/admin-login.html";
            } else {
                showError(result.message || "데이터를 불러오는 중 오류가 발생했습니다.");
            }
        }
    } catch (error) {
        showError("데이터를 불러오는 중 오류가 발생했습니다: " + error.message);
    }
}

function displayInquiries(inquiries) {
    const content = document.getElementById("inquiriesContent");

    if (inquiries.length === 0) {
        content.innerHTML = '<div class="loading">문의사항이 없습니다.</div>';
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
          <th>카테고리</th>
          <th>제목</th>
          <th>작성일</th>
          <th>읽음</th>
          <th>관리</th>
        </tr>
      </thead>
      <tbody>
        ${inquiries
        .map(
            (inquiry) => `
            <tr>
              <td>${inquiry.id}</td>
              <td>${inquiry.name}</td>
              <td>${inquiry.email}</td>
              <td>${inquiry.phone || "-"}</td>
              <td>${getCategoryName(inquiry.category)}</td>
              <td><a href="#" onclick="viewInquiryDetail(${inquiry.id}); return false;" class="name-link">${inquiry.subject}</a></td>
              <td>${new Date(inquiry.createdAt).toLocaleString()}</td>
              <td>
                <span class="status-badge ${inquiry.isRead ? "status-active" : "status-inactive"}">
                  ${inquiry.isRead ? "읽음" : "안읽음"}
                </span>
              </td>
              <td>
                <button class="status-toggle-btn" onclick="deleteInquiry(${inquiry.id})">
                  삭제
                </button>
              </td>
            </tr>
        `
        )
        .join("")}
      </tbody>
    </table>
    <div id="pagination"></div>
  `;

    content.innerHTML = table;
}

function updatePagination() {
    const pagination = document.getElementById("pagination");
    if (!pagination) return;

    let paginationHTML = '<div class="pagination">';
    
    if (totalPages <= 1) {
        paginationHTML += `<span class="page-info">총 ${totalCount}건</span>`;
    } else {
        if (currentPage > 0) {
            paginationHTML += `<button onclick="loadInquiries(${currentPage - 1})" class="page-btn">이전</button>`;
        }

        const startPage = Math.max(0, currentPage - 2);
        const endPage = Math.min(totalPages - 1, currentPage + 2);

        if (startPage > 0) {
            paginationHTML += `<button onclick="loadInquiries(0)" class="page-btn">1</button>`;
            if (startPage > 1) {
                paginationHTML += `<span class="page-ellipsis">...</span>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `<button onclick="loadInquiries(${i})" 
                                       class="page-btn ${i === currentPage ? 'active' : ''}">${i + 1}</button>`;
        }

        if (endPage < totalPages - 1) {
            if (endPage < totalPages - 2) {
                paginationHTML += `<span class="page-ellipsis">...</span>`;
            }
            paginationHTML += `<button onclick="loadInquiries(${totalPages - 1})" class="page-btn">${totalPages}</button>`;
        }

        if (currentPage < totalPages - 1) {
            paginationHTML += `<button onclick="loadInquiries(${currentPage + 1})" class="page-btn">다음</button>`;
        }

        paginationHTML += `<span class="page-info">총 ${totalCount}건 (${currentPage + 1}/${totalPages} 페이지)</span>`;
    }

    paginationHTML += '</div>';

    pagination.innerHTML = paginationHTML;
}

function viewInquiryDetail(id) {
    window.location.href = `/contact-inquiry-detail.html?id=${id}`;
}

function handleSearch() {
    const searchInput = document.getElementById("searchKeywordInput");
    if (searchInput) {
        searchKeyword = searchInput.value.trim();
    }
    const categorySelect = document.getElementById("categoryFilter");
    if (categorySelect) {
        searchCategory = categorySelect.value;
    }
    currentPage = 0;
    loadInquiries(0);
}

function handleCategoryFilter() {
    const categorySelect = document.getElementById("categoryFilter");
    if (categorySelect) {
        searchCategory = categorySelect.value;
        currentPage = 0;
        loadInquiries(0);
    }
}

function handleSearchKeyUp(event) {
    if (event.key === "Enter") {
        handleSearch();
    }
}

function clearSearch() {
    const searchInput = document.getElementById("searchKeywordInput");
    if (searchInput) {
        searchInput.value = "";
    }
    const categorySelect = document.getElementById("categoryFilter");
    if (categorySelect) {
        categorySelect.value = "";
    }
    searchKeyword = "";
    searchCategory = "";
    currentPage = 0;
    loadInquiries(0);
}

async function deleteInquiry(id) {
    if (!confirm("정말로 이 문의사항을 삭제하시겠습니까?")) {
        return;
    }

    const adminToken = localStorage.getItem("adminToken");
    if (!adminToken) return;

    try {
        const response = await fetch(`/api/contact/inquiries/${id}`, {
            method: "DELETE",
            headers: {
                Authorization: adminToken,
            },
        });

        if (response.status === 401) {
            localStorage.removeItem("adminToken");
            window.location.href = "/admin-login.html";
            return;
        }

        const result = await response.json();

        if (result.success) {
            loadInquiries(currentPage);
        } else {
            alert(result.message || "삭제에 실패했습니다.");
        }
    } catch (error) {
        alert("삭제 중 오류가 발생했습니다: " + error.message);
    }
}

function showError(message) {
    const content = document.getElementById("inquiriesContent");
    content.innerHTML = `<div class="error">${message}</div>`;
}

function logout() {
    localStorage.removeItem("adminToken");
    updateNavigation();
    window.location.href = "/admin-login.html";
}

document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        const adminToken = localStorage.getItem("adminToken");
        if (!adminToken) {
            window.location.href = "/admin-login.html";
            return;
        }
        updateNavigation();
        loadInquiries();
    }, 1000);
});

