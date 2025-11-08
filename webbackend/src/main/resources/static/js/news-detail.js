(function() {
    'use strict';

    function getUrlParameter(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }

    function formatDate(dateString) {
        if (!dateString) return '';
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return dateString;
            }
            return date.toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateString;
        }
    }

    function getSentimentClass(sentiment) {
        if (sentiment === null || sentiment === undefined) return 'neutral';
        if (sentiment > 0.1) return 'positive';
        if (sentiment < -0.1) return 'negative';
        return 'neutral';
    }

    function getSentimentText(sentiment) {
        if (sentiment === null || sentiment === undefined) return '중립';
        if (sentiment > 0.1) return '긍정';
        if (sentiment < -0.1) return '부정';
        return '중립';
    }

    function loadNewsDetail() {
        const newsDetailContent = document.getElementById('newsDetailContent');
        if (!newsDetailContent) return;

        const encodedId = getUrlParameter('id');
        if (!encodedId || encodedId.trim() === '') {
            newsDetailContent.innerHTML = `
                <div class="error">
                    <p>뉴스 ID가 제공되지 않았습니다.</p>
                    <p style="margin-top: 10px; color: #666; font-size: 14px;">URL에 뉴스 ID가 포함되어 있지 않습니다. 뉴스 목록에서 뉴스를 선택해주세요.</p>
                    <a href="/" class="btn btn-primary" style="margin-top: 15px; display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">홈으로 돌아가기</a>
                </div>
            `;
            return;
        }

        const decodedUrl = decodeShortNewsId(encodedId);
        if (!decodedUrl || !decodedUrl.startsWith('http')) {
            newsDetailContent.innerHTML = `
                <div class="error">
                    <p>유효하지 않은 뉴스 URL입니다.</p>
                    <a href="/" class="btn btn-primary">홈으로 돌아가기</a>
                </div>
            `;
            return;
        }

        newsDetailContent.innerHTML = '<div class="loading">뉴스를 불러오는 중...</div>';

        const apiUrl = `/api/news/detail?url=${encodeURIComponent(decodedUrl)}`;

        axios.get(apiUrl, {
            timeout: 40000
        })
        .then(response => {
            const news = response.data;
            displayNewsDetail(news);
        })
        .catch(error => {
            let errorMessage = '뉴스 상세 정보를 불러올 수 없습니다.';

            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;

                if (status === 404) {
                    errorMessage = '뉴스를 찾을 수 없습니다.';
                } else if (status === 503) {
                    errorMessage = data?.message || data?.detail || '서비스가 일시적으로 사용 불가능합니다. 잠시 후 다시 시도해주세요.';
                } else if (status === 500) {
                    errorMessage = '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
                }
            } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
                errorMessage = '요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.';
            } else if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
                errorMessage = '네트워크 연결에 실패했습니다. 인터넷 연결을 확인해주세요.';
            }

            newsDetailContent.innerHTML = `
                <div class="error">
                    <p>${errorMessage}</p>
                    <div style="margin-top: 20px;">
                        <button onclick="loadNewsDetail()" class="btn btn-primary" style="margin-right: 10px;">다시 시도</button>
                        <a href="/" class="btn btn-secondary">홈으로 돌아가기</a>
                    </div>
                </div>
            `;
        });
    }

    function displayNewsDetail(news) {
        const newsDetailContent = document.getElementById('newsDetailContent');
        if (!newsDetailContent || !news) {
            newsDetailContent.innerHTML = `
                <div class="error">
                    <p>뉴스 정보를 표시할 수 없습니다.</p>
                    <a href="/" class="btn btn-primary">홈으로 돌아가기</a>
                </div>
            `;
            return;
        }

        const title = (news.titleKo || news.title_ko || news.title || '').trim();
        const titleOriginal = (news.titleOriginal || news.title_original || news.title || '').trim();
        let description = (news.descriptionKo || news.description_ko || news.description || '').trim();
        const descriptionOriginal = (news.descriptionOriginal || news.description_original || news.description || '').trim();
        const content = (news.contentKo || news.content_ko || news.content || '').trim();
        const contentOriginal = (news.contentOriginal || news.content_original || news.content || '').trim();
        
        if (description === title || description === titleOriginal) {
            description = '';
        }
        
        if (description && description.length < 50) {
            description = '';
        }
        const source = news.source || '';
        const url = news.url || '';
        const publishedAt = formatDate(news.publishedAt || news.published_at || '');
        const sentiment = news.sentiment;
        const sentimentClass = getSentimentClass(sentiment);
        const sentimentText = getSentimentText(sentiment);
        const provider = news.provider || '';
        const symbol = news.symbol || '';
        
        const providerDisplay = provider && provider.toLowerCase() !== 'google' ? provider : '';

        let html = `
            <div class="news-detail-header">
                <a href="/" class="back-link">← 목록으로 돌아가기</a>
                <div class="news-meta">
                    ${providerDisplay ? `<span class="news-provider">${providerDisplay}</span>` : ''}
                    ${sentiment !== null && sentiment !== undefined ? `<span class="news-sentiment sentiment-${sentimentClass}">${sentimentText}</span>` : ''}
                    ${symbol ? `<span class="news-symbol">요약</span>` : ''}
                </div>
            </div>

            <article class="news-detail-article">
                <header class="news-detail-title">
                    <h1>${title || titleOriginal}</h1>
                    ${titleOriginal && title !== titleOriginal ? `<p class="news-original-title">${titleOriginal}</p>` : ''}
                </header>

                ${source || publishedAt || url ? `
                <div class="news-detail-info">
                    ${source ? `<div class="news-source"><strong>출처:</strong> ${source}</div>` : ''}
                    ${publishedAt ? `<div class="news-date"><strong>발행일:</strong> ${publishedAt}</div>` : ''}
                    ${url ? `<div class="news-link"><a href="${url}" target="_blank" rel="noopener noreferrer">원문 보기 →</a></div>` : ''}
                </div>
                ` : ''}

                ${description ? `
                    <div class="news-detail-description">
                        <p>${description}</p>
                        ${descriptionOriginal && description !== descriptionOriginal ? `<p class="news-original-text">${descriptionOriginal}</p>` : ''}
                    </div>
                ` : ''}

                ${content ? `
                    <div class="news-detail-content">
                        <h2>내용</h2>
                        <div class="news-content-text">${content.replace(/\n/g, '<br>')}</div>
                        ${contentOriginal && content !== contentOriginal ? `<div class="news-original-text">${contentOriginal.replace(/\n/g, '<br>')}</div>` : ''}
                    </div>
                ` : ''}

                ${!description && !content ? `
                    <div class="news-detail-no-content">
                        <p>뉴스 내용이 제공되지 않았습니다.</p>
                        ${url ? `<a href="${url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary">원문 보기</a>` : ''}
                    </div>
                ` : ''}
            </article>
        `;

        newsDetailContent.innerHTML = html;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadNewsDetail);
    } else {
        loadNewsDetail();
    }

    window.loadNewsDetail = loadNewsDetail;
})();
