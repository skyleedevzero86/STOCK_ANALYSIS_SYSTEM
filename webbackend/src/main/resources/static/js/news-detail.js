function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

function loadNewsDetail() {
    const encodedUrl = getUrlParameter('url');
    if (!encodedUrl) {
        document.getElementById('newsDetailContent').innerHTML = 
            '<div class="error">뉴스 URL이 제공되지 않았습니다.</div>';
        return;
    }

    const decodedUrl = decodeURIComponent(encodedUrl);
    const newsId = encodeURIComponent(decodedUrl);
    
    axios.get(`/api/news/detail/${newsId}`)
        .then(response => {
            const news = response.data;
            displayNewsDetail(news, decodedUrl);
        })
        .catch(error => {
            console.error('뉴스 상세 로드 실패:', error);
            document.getElementById('newsDetailContent').innerHTML = 
                '<div class="error">뉴스를 불러올 수 없습니다.<br><br>' +
                '<a href="/" class="btn-back">대시보드로 돌아가기</a></div>';
        });
}

function displayNewsDetail(news, originalUrl) {
    const title = news.titleKo || news.title_ko || news.title || '제목 없음';
    const description = news.descriptionKo || news.description_ko || news.description || '';
    const content = news.contentKo || news.content_ko || news.content || '';
    const source = news.source || '알 수 없음';
    const publishedAt = news.publishedAt || news.published_at || '';
    const provider = news.provider || '';
    const sentiment = news.sentiment;

    let publishedAtFormatted = '';
    if (publishedAt) {
        try {
            publishedAtFormatted = new Date(publishedAt).toLocaleString('ko-KR');
        } catch (e) {
            publishedAtFormatted = publishedAt;
        }
    }

    let sentimentBadge = '';
    if (sentiment !== null && sentiment !== undefined) {
        const sentimentClass = sentiment > 0.1 ? 'positive' : sentiment < -0.1 ? 'negative' : 'neutral';
        const sentimentText = sentiment > 0.1 ? '긍정' : sentiment < -0.1 ? '부정' : '중립';
        sentimentBadge = `<span class="news-sentiment sentiment-${sentimentClass}">${sentimentText}</span>`;
    }

    let contentHtml = '';
    if (content) {
        const contentLines = content.split('\n').filter(line => line.trim());
        contentHtml = contentLines.map(line => `<p>${escapeHtml(line.trim())}</p>`).join('');
    } else if (description) {
        contentHtml = `<p>${escapeHtml(description)}</p>`;
    } else {
        contentHtml = '<p>내용이 제공되지 않았습니다.</p>';
    }

    const html = `
        <div class="news-detail-header">
            <h1 class="news-detail-title">${escapeHtml(title)}</h1>
            <div class="news-detail-meta">
                ${provider ? `<span><strong>출처:</strong> ${escapeHtml(provider)}</span>` : ''}
                ${source ? `<span><strong>소스:</strong> ${escapeHtml(source)}</span>` : ''}
                ${publishedAtFormatted ? `<span><strong>발행일:</strong> ${publishedAtFormatted}</span>` : ''}
                ${sentimentBadge}
            </div>
        </div>
        <div class="news-detail-content">
            ${contentHtml}
        </div>
        <div class="news-detail-actions">
            <a href="/" class="btn-back">대시보드로 돌아가기</a>
            <a href="${originalUrl}" target="_blank" rel="noopener noreferrer" class="btn-original">원문 보기</a>
        </div>
    `;

    document.getElementById('newsDetailContent').innerHTML = html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', function() {
    loadNewsDetail();
});

