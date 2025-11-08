let currentSymbol = 'AAPL';
let newsRefreshInterval = null;

function updateCurrentSymbol(symbol) {
    currentSymbol = symbol;
    const includeKorean = document.getElementById('includeKoreanNews')?.checked || false;
    loadNews(symbol, includeKorean);
}

function loadNews(symbol, includeKorean = false, autoTranslate = true) {
    const newsContainer = document.getElementById('newsContainer');
    newsContainer.innerHTML = '<div class="loading">뉴스를 불러오는 중...</div>';

    const url = `/api/news/${symbol}?includeKorean=${includeKorean}&autoTranslate=${autoTranslate}`;
    
    axios.get(url, {
        timeout: 30000
    })
        .then(response => {
            const news = response.data;
            displayNews(news);
        })
        .catch(error => {
            let errorMessage = '뉴스를 불러올 수 없습니다.';
            
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                
                if (status === 503) {
                    errorMessage = data?.message || data?.detail || '서비스가 일시적으로 사용 불가능합니다. 잠시 후 다시 시도해주세요.';
                } else if (status === 500) {
                    errorMessage = '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
                } else if (status === 404) {
                    errorMessage = '요청한 리소스를 찾을 수 없습니다.';
                }
            } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
                errorMessage = '요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.';
            } else if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
                errorMessage = '네트워크 연결에 실패했습니다. 인터넷 연결을 확인해주세요.';
            }
            
            newsContainer.innerHTML = `<div class="error">
                <p>${errorMessage}</p>
                <button onclick="loadNews('${symbol}', ${includeKorean})" style="margin-top: 10px; padding: 8px 16px; cursor: pointer;">
                    다시 시도
                </button>
            </div>`;
        });
}

function stripHtmlTags(html) {
    if (!html) return '';
    const tmp = document.createElement('DIV');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
}

function displayNews(news) {
    const newsContainer = document.getElementById('newsContainer');
    
    if (!news || news.length === 0) {
        newsContainer.innerHTML = '<div class="no-data">관련 뉴스가 없습니다.</div>';
        return;
    }

    const newsHTML = news.map((item, index) => {
        const publishedDate = item.publishedAt ? new Date(item.publishedAt).toLocaleDateString('ko-KR') : '';
        const providerBadge = item.provider ? `<span class="news-provider">${item.provider}</span>` : '';
        const sentimentBadge = item.sentiment !== null && item.sentiment !== undefined 
            ? `<span class="news-sentiment sentiment-${getSentimentClass(item.sentiment)}">${getSentimentText(item.sentiment)}</span>`
            : '';

        const title = (item.titleKo || item.title_ko || item.title || '').trim();
        const descriptionRaw = (item.descriptionKo || item.description_ko || item.description || '').trim();
        const description = stripHtmlTags(descriptionRaw);
        const url = item.url || '';
        const shortId = url ? (typeof createShortNewsId === 'function' ? createShortNewsId(url) : encodeURIComponent(url)) : '';
        const detailUrl = shortId ? `/news-detail?id=${encodeURIComponent(shortId)}` : '#';
        const titleLink = shortId ? 
            `<a href="${detailUrl}" class="news-title-link" data-short-id="${shortId.replace(/'/g, "&apos;").replace(/"/g, "&quot;")}">${title}</a>` :
            `<span>${title}</span>`;

        const dataShortIdAttr = shortId ? `data-short-id="${shortId.replace(/'/g, "&apos;").replace(/"/g, "&quot;")}"` : '';

        return `
            <div class="news-item" ${dataShortIdAttr}>
                <div class="news-header">
                    <h4 class="news-title">
                        ${titleLink}
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
    
    const newsItems = newsContainer.querySelectorAll('.news-item[data-short-id]');
    newsItems.forEach(item => {
        item.addEventListener('click', function(e) {
            if (e.target.tagName === 'A' || e.target.closest('a') || e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                return;
            }
            const shortId = this.getAttribute('data-short-id');
            if (shortId && shortId.trim() !== '') {
                openNewsDetail(shortId);
            }
        });
    });
    
    const titleLinks = newsContainer.querySelectorAll('.news-title-link');
    titleLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const shortId = this.getAttribute('data-short-id');
            if (shortId && shortId.trim() !== '') {
                openNewsDetail(shortId);
            }
        });
    });
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

function openNewsDetail(shortId) {
    if (!shortId || shortId.trim() === '') {
        return;
    }
    window.location.href = `/news-detail?id=${encodeURIComponent(shortId)}`;
}

window.openNewsDetail = openNewsDetail;

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

