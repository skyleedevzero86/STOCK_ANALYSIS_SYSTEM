let currentSymbol = 'AAPL';
let newsRefreshInterval = null;

function updateCurrentSymbol(symbol) {
    currentSymbol = symbol;
    const autoTranslate = document.getElementById('includeKoreanNews')?.checked || false;
    loadNews(symbol, false, autoTranslate);
}

function loadNews(symbol, includeKorean = false, autoTranslate = false) {
    const newsContainer = document.getElementById('newsContainer');
    if (!newsContainer) {
        console.error('newsContainer element not found');
        return;
    }
    
    newsContainer.innerHTML = '<div class="loading">뉴스를 불러오는 중...</div>';

    const url = `/api/news/${symbol}?includeKorean=${includeKorean}&autoTranslate=${autoTranslate}`;
    
    axios.get(url, {
        timeout: 30000
    })
        .then(response => {
            const news = response.data;
            if (Array.isArray(news) && news.length > 0) {
                displayNews(news);
            } else {
                if (newsContainer) {
                    newsContainer.innerHTML = '<div class="no-data">관련 뉴스가 없습니다.</div>';
                }
            }
        })
        .catch(error => {
            let errorMessage = '뉴스를 불러올 수 없습니다.';
            
            if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
                errorMessage = '뉴스 조회 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.';
            } else if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                
                if (status === 503) {
                    errorMessage = data?.message || data?.detail || '서비스가 일시적으로 사용 불가능합니다. 잠시 후 다시 시도해주세요.';
                } else if (status === 500) {
                    errorMessage = '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
                } else if (status === 404) {
                    errorMessage = '요청한 리소스를 찾을 수 없습니다.';
                }
            } else if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
                errorMessage = '네트워크 연결에 실패했습니다. 인터넷 연결을 확인해주세요.';
            }
            
            if (newsContainer) {
                newsContainer.innerHTML = `<div class="error">
                    <p>${errorMessage}</p>
                    <button onclick="loadNews('${symbol}', ${includeKorean})" style="margin-top: 10px; padding: 8px 16px; cursor: pointer;">
                        다시 시도
                    </button>
                </div>`;
            }
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
    if (!newsContainer) {
        console.error('newsContainer element not found in displayNews');
        return;
    }
    
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
        
        let url = item.url || '';
        if (!url && descriptionRaw) {
            const urlMatch = descriptionRaw.match(/href=["']([^"']+)["']/i);
            if (urlMatch && urlMatch[1]) {
                url = urlMatch[1];
            }
        }
        
        let shortId = '';
        let detailUrl = '#';
        
        if (url) {
            try {
                if (typeof createShortNewsId === 'function') {
                    shortId = createShortNewsId(url);
                } else if (typeof encodeUrlToBase64 === 'function') {
                    shortId = encodeUrlToBase64(url);
                } else {
                    shortId = encodeURIComponent(url);
                }
                
                if (!shortId || shortId.trim() === '') {
                    shortId = encodeURIComponent(url);
                }
                
                detailUrl = `/news-detail?id=${encodeURIComponent(shortId)}`;
            } catch (e) {
                console.warn('Failed to create shortId:', e);
                shortId = encodeURIComponent(url);
                detailUrl = `/news-detail?id=${shortId}`;
            }
        }
        
        const titleLink = url ? 
            `<a href="${detailUrl}" class="news-title-link" data-short-id="${shortId ? shortId.replace(/'/g, "&apos;").replace(/"/g, "&quot;") : ''}" data-url="${url.replace(/'/g, "&apos;").replace(/"/g, "&quot;")}">${title}</a>` :
            `<span>${title}</span>`;

        const dataShortIdAttr = url ? `data-short-id="${shortId ? shortId.replace(/'/g, "&apos;").replace(/"/g, "&quot;") : encodeURIComponent(url).replace(/'/g, "&apos;").replace(/"/g, "&quot;")}" data-url="${url.replace(/'/g, "&apos;").replace(/"/g, "&quot;")}"` : '';

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
    
    const newsItems = newsContainer.querySelectorAll('.news-item[data-short-id], .news-item[data-url]');
    newsItems.forEach(item => {
        item.style.cursor = 'pointer';
        item.addEventListener('click', function(e) {
            if (e.target.tagName === 'A' || e.target.closest('a') || 
                e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                return;
            }
            
            const shortId = this.getAttribute('data-short-id');
            const url = this.getAttribute('data-url');
            
            if (shortId && shortId.trim() !== '') {
                e.preventDefault();
                e.stopPropagation();
                openNewsDetail(shortId);
            } else if (url && url.trim() !== '') {
                e.preventDefault();
                e.stopPropagation();
                try {
                    let generatedShortId = '';
                    if (typeof createShortNewsId === 'function') {
                        generatedShortId = createShortNewsId(url);
                    } else if (typeof encodeUrlToBase64 === 'function') {
                        generatedShortId = encodeUrlToBase64(url);
                    } else {
                        generatedShortId = encodeURIComponent(url);
                    }
                    if (generatedShortId && generatedShortId.trim() !== '') {
                        openNewsDetail(generatedShortId);
                    } else {
                        openNewsDetail(encodeURIComponent(url));
                    }
                } catch (err) {
                    console.warn('Error generating shortId from url:', err);
                    openNewsDetail(encodeURIComponent(url));
                }
            }
        });
    });
    
    const titleLinks = newsContainer.querySelectorAll('.news-title-link');
    titleLinks.forEach(link => {
        link.style.cursor = 'pointer';
        link.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const shortId = this.getAttribute('data-short-id');
            const url = this.getAttribute('data-url');
            const href = this.getAttribute('href');
            
            console.log('News link clicked:', { shortId, url, href });
            
            if (shortId && shortId.trim() !== '') {
                console.log('Opening news detail with shortId:', shortId);
                const detailUrl = `/news-detail?id=${encodeURIComponent(shortId)}`;
                console.log('Navigating to:', detailUrl);
                window.location.href = detailUrl;
            } 
            else if (url && url.trim() !== '') {
                console.log('Opening news detail with url:', url);
                try {
                    let encodedUrl;
                    if (typeof encodeUrlToBase64 === 'function') {
                        encodedUrl = encodeUrlToBase64(url);
                    } else if (typeof createShortNewsId === 'function') {
                        encodedUrl = createShortNewsId(url);
                    } else {
                        encodedUrl = encodeURIComponent(url);
                    }
                    
                    if (!encodedUrl || encodedUrl.trim() === '') {
                        encodedUrl = encodeURIComponent(url);
                    }
                    
                    const detailUrl = `/news-detail?id=${encodeURIComponent(encodedUrl)}`;
                    console.log('Navigating to:', detailUrl);
                    window.location.href = detailUrl;
                } catch (err) {
                    console.error('Error encoding URL:', err);
                    const detailUrl = `/news-detail?id=${encodeURIComponent(url)}`;
                    console.log('Navigating to (fallback):', detailUrl);
                    window.location.href = detailUrl;
                }
            } 
            else if (href && href !== '#') {
                console.log('Navigating to href:', href);
                window.location.href = href;
            } 
            else {
                console.warn('No valid URL found for news item');
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

function startNewsAutoRefresh(symbol, includeKorean = false, autoTranslate = false) {
    if (newsRefreshInterval) {
        clearInterval(newsRefreshInterval);
    }
    
    newsRefreshInterval = setInterval(() => {
        loadNews(symbol, includeKorean, autoTranslate);
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
        console.warn('openNewsDetail: shortId is empty');
        return;
    }
    const detailUrl = `/news-detail?id=${encodeURIComponent(shortId)}`;
    console.log('openNewsDetail: Navigating to', detailUrl);
    window.location.href = detailUrl;
}

window.openNewsDetail = openNewsDetail;

document.addEventListener('DOMContentLoaded', function() {
    const includeKoreanCheckbox = document.getElementById('includeKoreanNews');
    const refreshNewsBtn = document.getElementById('refreshNewsBtn');

    if (includeKoreanCheckbox) {
        includeKoreanCheckbox.addEventListener('change', function() {
            const autoTranslate = this.checked;
            localStorage.setItem('newsAutoTranslate', autoTranslate.toString());
            loadNews(currentSymbol, false, autoTranslate);
            startNewsAutoRefresh(currentSymbol, false, autoTranslate);
        });
        
        const savedAutoTranslate = localStorage.getItem('newsAutoTranslate');
        if (savedAutoTranslate !== null) {
            includeKoreanCheckbox.checked = savedAutoTranslate === 'true';
        }
    }

    if (refreshNewsBtn) {
        refreshNewsBtn.addEventListener('click', function() {
            const autoTranslate = includeKoreanCheckbox ? includeKoreanCheckbox.checked : false;
            loadNews(currentSymbol, false, autoTranslate);
        });
    }

    if (typeof window.dashboard !== 'undefined' && window.dashboard) {
        const originalSymbolChange = window.dashboard.currentSymbol;
        const symbolObserver = new MutationObserver(() => {
            const newSymbol = window.dashboard?.currentSymbol || 'AAPL';
            if (newSymbol !== currentSymbol) {
                currentSymbol = newSymbol;
                const autoTranslate = includeKoreanCheckbox ? includeKoreanCheckbox.checked : false;
                loadNews(newSymbol, false, autoTranslate);
                startNewsAutoRefresh(newSymbol, false, autoTranslate);
            }
        });
        
        setInterval(() => {
            const newSymbol = window.dashboard?.currentSymbol || 'AAPL';
            if (newSymbol !== currentSymbol) {
                currentSymbol = newSymbol;
                const autoTranslate = includeKoreanCheckbox ? includeKoreanCheckbox.checked : false;
                loadNews(newSymbol, false, autoTranslate);
                startNewsAutoRefresh(newSymbol, false, autoTranslate);
            }
        }, 1000);
    }
    
    window.updateCurrentSymbol = updateCurrentSymbol;

    const autoTranslate = includeKoreanCheckbox ? includeKoreanCheckbox.checked : false;
    loadNews(currentSymbol, false, autoTranslate);
    startNewsAutoRefresh(currentSymbol, false, autoTranslate);
});

