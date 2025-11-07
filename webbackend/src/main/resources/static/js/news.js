let currentSymbol = 'AAPL';
let newsRefreshInterval = null;

function updateCurrentSymbol(symbol) {
    currentSymbol = symbol;
    const includeKorean = document.getElementById('includeKoreanNews')?.checked || false;
    loadNews(symbol, includeKorean);
}

function loadNews(symbol, includeKorean = false) {
    const newsContainer = document.getElementById('newsContainer');
    newsContainer.innerHTML = '<div class="loading">뉴스를 불러오는 중...</div>';

    const url = `/api/news/${symbol}?includeKorean=${includeKorean}`;
    
    axios.get(url)
        .then(response => {
            const news = response.data;
            displayNews(news);
        })
        .catch(error => {
            console.error('뉴스 로드 실패:', error);
            newsContainer.innerHTML = '<div class="error">뉴스를 불러올 수 없습니다.</div>';
        });
}

function displayNews(news) {
    const newsContainer = document.getElementById('newsContainer');
    
    if (!news || news.length === 0) {
        newsContainer.innerHTML = '<div class="no-data">관련 뉴스가 없습니다.</div>';
        return;
    }

    const newsHTML = news.map(item => {
        const publishedDate = item.publishedAt ? new Date(item.publishedAt).toLocaleDateString('ko-KR') : '';
        const providerBadge = item.provider ? `<span class="news-provider">${item.provider}</span>` : '';
        const sentimentBadge = item.sentiment !== null && item.sentiment !== undefined 
            ? `<span class="news-sentiment sentiment-${getSentimentClass(item.sentiment)}">${getSentimentText(item.sentiment)}</span>`
            : '';

        const title = item.title_ko || item.title || '';
        const description = item.description_ko || item.description || '';
        const encodedUrl = encodeURIComponent(item.url || '');
        const detailUrl = `/news-detail?url=${encodedUrl}`;

        return `
            <div class="news-item">
                <div class="news-header">
                    <h4 class="news-title">
                        <a href="${detailUrl}" onclick="event.preventDefault(); openNewsDetail('${encodedUrl}'); return false;">
                            ${title}
                        </a>
                    </h4>
                    <div class="news-badges">
                        ${providerBadge}
                        ${sentimentBadge}
                    </div>
                </div>
                ${description ? `<p class="news-description">${description}</p>` : ''}
                <div class="news-footer">
                    ${item.source ? `<span class="news-source">${item.source}</span>` : ''}
                    ${publishedDate ? `<span class="news-date">${publishedDate}</span>` : ''}
                </div>
            </div>
        `;
    }).join('');

    newsContainer.innerHTML = newsHTML;
}

function getSentimentClass(sentiment) {
    if (sentiment > 0.1) return 'positive';
    if (sentiment < -0.1) return 'negative';
    return 'neutral';
}

function getSentimentText(sentiment) {
    if (sentiment > 0.1) return '긍정';
    if (sentiment < -0.1) return '부정';
    return '중립';
}

function startNewsAutoRefresh(symbol, includeKorean) {
    if (newsRefreshInterval) {
        clearInterval(newsRefreshInterval);
    }
    
    newsRefreshInterval = setInterval(() => {
        loadNews(symbol, includeKorean);
    }, 300000);
}

function stopNewsAutoRefresh() {
    if (newsRefreshInterval) {
        clearInterval(newsRefreshInterval);
        newsRefreshInterval = null;
    }
}

function openNewsDetail(encodedUrl) {
    window.location.href = `/news-detail?url=${encodedUrl}`;
}

document.addEventListener('DOMContentLoaded', function() {
    const includeKoreanCheckbox = document.getElementById('includeKoreanNews');
    const refreshNewsBtn = document.getElementById('refreshNewsBtn');

    if (includeKoreanCheckbox) {
        includeKoreanCheckbox.addEventListener('change', function() {
            const includeKorean = this.checked;
            loadNews(currentSymbol, includeKorean);
            startNewsAutoRefresh(currentSymbol, includeKorean);
        });
    }

    if (refreshNewsBtn) {
        refreshNewsBtn.addEventListener('click', function() {
            const includeKorean = includeKoreanCheckbox ? includeKoreanCheckbox.checked : false;
            loadNews(currentSymbol, includeKorean);
        });
    }

    if (typeof window.dashboard !== 'undefined' && window.dashboard) {
        const originalSymbolChange = window.dashboard.currentSymbol;
        const symbolObserver = new MutationObserver(() => {
            const newSymbol = window.dashboard?.currentSymbol || 'AAPL';
            if (newSymbol !== currentSymbol) {
                currentSymbol = newSymbol;
                const includeKorean = includeKoreanCheckbox ? includeKoreanCheckbox.checked : false;
                loadNews(newSymbol, includeKorean);
                startNewsAutoRefresh(newSymbol, includeKorean);
            }
        });
        
        setInterval(() => {
            const newSymbol = window.dashboard?.currentSymbol || 'AAPL';
            if (newSymbol !== currentSymbol) {
                currentSymbol = newSymbol;
                const includeKorean = includeKoreanCheckbox ? includeKoreanCheckbox.checked : false;
                loadNews(newSymbol, includeKorean);
                startNewsAutoRefresh(newSymbol, includeKorean);
            }
        }, 1000);
    }
    
    window.updateCurrentSymbol = updateCurrentSymbol;

    const includeKorean = includeKoreanCheckbox ? includeKoreanCheckbox.checked : false;
    loadNews(currentSymbol, includeKorean);
    startNewsAutoRefresh(currentSymbol, includeKorean);
});

