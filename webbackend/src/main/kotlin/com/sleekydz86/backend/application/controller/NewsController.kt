package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.domain.model.News
import com.sleekydz86.backend.global.circuitbreaker.CircuitBreakerManager
import com.sleekydz86.backend.global.exception.CircuitBreakerOpenException
import com.sleekydz86.backend.global.exception.ExternalApiException
import com.sleekydz86.backend.infrastructure.client.PythonApiClient
import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.Parameter
import io.swagger.v3.oas.annotations.responses.ApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import io.swagger.v3.oas.annotations.tags.Tag
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

@RestController
@RequestMapping("/api/news")
@Tag(name = "뉴스 API", description = "주식 관련 뉴스 조회 및 검색 API")
class NewsController(
    private val pythonApiClient: PythonApiClient,
    private val circuitBreakerManager: CircuitBreakerManager,
    private val deepLTranslationService: com.sleekydz86.backend.infrastructure.service.DeepLTranslationService
) {

    @GetMapping("/{symbol}")
    @Operation(summary = "주식 뉴스 조회", description = "특정 심볼과 관련된 뉴스를 조회합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 뉴스를 조회했습니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun getStockNews(
        @Parameter(description = "주식 심볼 (예: AAPL, GOOGL)", required = true)
        @PathVariable symbol: String,
        @Parameter(description = "한글 번역 포함 여부 (기본값: true)", required = false)
        @RequestParam(defaultValue = "true") includeKorean: Boolean,
        @Parameter(description = "자동 번역 사용 여부 (기본값: true)", required = false)
        @RequestParam(defaultValue = "true") autoTranslate: Boolean
    ): Mono<List<News>> {
        val logger = org.slf4j.LoggerFactory.getLogger(NewsController::class.java)
        
        return circuitBreakerManager.executeWithCircuitBreaker("news") {
            pythonApiClient.getStockNews(symbol.uppercase(), includeKorean, false)
        }
            .timeout(Duration.ofSeconds(45))
            .flatMap { newsList ->
                if (autoTranslate && deepLTranslationService.isAvailable() && newsList.isNotEmpty()) {
                    translateNewsWithDeepL(newsList)
                } else {
                    Mono.just(newsList)
                }
            }
            .onErrorResume { error: Throwable ->
                when (error) {
                    is CircuitBreakerOpenException -> {
                        logger.warn("Circuit breaker open for news: $symbol")
                        Mono.just(emptyList())
                    }
                    is java.util.concurrent.TimeoutException -> {
                        logger.warn("Timeout fetching news for: $symbol")
                        Mono.just(emptyList())
                    }
                    else -> {
                        logger.error("Error fetching news for $symbol: ${error.message}", error)
                        Mono.just(emptyList())
                    }
                }
            }
    }
    
    private fun translateNewsWithDeepL(newsList: List<News>): Mono<List<News>> {
        val logger = org.slf4j.LoggerFactory.getLogger(NewsController::class.java)
        
        val newsToTranslate = newsList.filter { news ->
            val needsTitle = (news.titleKo.isNullOrBlank() || news.titleKo == news.title) && !isKoreanText(news.title)
            val needsDesc = news.description != null && 
                (news.descriptionKo.isNullOrBlank() || news.descriptionKo == news.description) && 
                !isKoreanText(news.description)
            needsTitle || needsDesc
        }
        
        if (newsToTranslate.isEmpty()) {
            return Mono.just(newsList)
        }
        
        return Flux.fromIterable(newsToTranslate)
            .flatMap { news ->
                val needsTitle = (news.titleKo.isNullOrBlank() || news.titleKo == news.title) && !isKoreanText(news.title)
                val needsDesc = news.description != null && 
                    (news.descriptionKo.isNullOrBlank() || news.descriptionKo == news.description) && 
                    !isKoreanText(news.description)
                
                val titleMono = if (needsTitle) {
                    deepLTranslationService.translateToKorean(news.title)
                } else {
                    Mono.just(news.titleKo ?: news.title)
                }
                
                val descriptionMono = if (needsDesc) {
                    deepLTranslationService.translateToKorean(news.description!!)
                } else {
                    Mono.just(news.descriptionKo ?: news.description ?: "")
                }
                
                Mono.zip(titleMono, descriptionMono)
                    .map { tuple ->
                        news.copy(
                            titleKo = if (needsTitle) tuple.t1 else (news.titleKo ?: news.title),
                            descriptionKo = if (needsDesc) tuple.t2 else (news.descriptionKo ?: news.description)
                        )
                    }
                    .timeout(Duration.ofSeconds(8))
                    .onErrorReturn(news)
            }
            .collectList()
            .map { translated ->
                val translatedMap = translated.associateBy { it.url }
                newsList.map { news ->
                    translatedMap[news.url] ?: news
                }
            }
            .timeout(Duration.ofSeconds(20))
            .onErrorReturn(newsList)
    }
    
    private fun isKoreanText(text: String): Boolean {
        if (text.isBlank()) return false
        val koreanCharCount = text.count { it in '\uAC00'..'\uD7A3' }
        val totalCharCount = text.count { it.isLetterOrDigit() || it.isWhitespace() }
        if (totalCharCount == 0) return false
        val koreanRatio = koreanCharCount.toDouble() / totalCharCount
        return koreanRatio > 0.3
    }
    
    @GetMapping("/detail")
    @Operation(summary = "뉴스 상세 조회", description = "URL을 통해 특정 뉴스의 상세 내용을 조회합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 뉴스 상세를 조회했습니다"),
            ApiResponse(responseCode = "404", description = "뉴스를 찾을 수 없습니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun getNewsDetail(
        @Parameter(description = "뉴스 URL", required = true)
        @RequestParam url: String,
        @Parameter(description = "자동 번역 사용 여부 (기본값: true)", required = false)
        @RequestParam(defaultValue = "true") autoTranslate: Boolean
    ): Mono<News> {
        val logger = org.slf4j.LoggerFactory.getLogger(NewsController::class.java)
        logger.info("뉴스 상세 조회 요청: url={}, autoTranslate={}", url.take(100), autoTranslate)
        
        return circuitBreakerManager.executeWithCircuitBreaker("newsDetail") {
            val decodedUrl = try {
                java.net.URLDecoder.decode(url, "UTF-8")
            } catch (e: Exception) {
                logger.warn("URL 디코딩 실패, 원본 URL 사용: url={}, error={}", url.take(100), e.message)
                url
            }
            pythonApiClient.getNewsByUrl(decodedUrl)
        }
            .timeout(Duration.ofSeconds(30))
            .flatMap { news ->
                if (autoTranslate && deepLTranslationService.isAvailable()) {
                    translateNewsDetailWithDeepL(news)
                } else {
                    Mono.just(news)
                }
            }
            .doOnError { error ->
                logger.error("뉴스 상세 조회 실패: url={}, error={}", url.take(100), error.message, error)
            }
            .onErrorResume { error: Throwable ->
                when (error) {
                    is CircuitBreakerOpenException -> {
                        logger.warn("Circuit breaker가 열려있음: newsDetail")
                        Mono.error(ExternalApiException("서비스가 일시적으로 사용 불가능합니다. 잠시 후 다시 시도해주세요.", error))
                    }
                    is java.util.concurrent.TimeoutException -> {
                        logger.warn("뉴스 상세 조회 타임아웃: url={}", url.take(100))
                        Mono.error(ExternalApiException("요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.", error))
                    }
                    is ExternalApiException -> {
                        Mono.error(error)
                    }
                    else -> {
                        logger.error("예상치 못한 오류: url={}, error={}", url.take(100), error.message, error)
                        Mono.error(ExternalApiException("뉴스 상세 정보를 가져오는데 실패했습니다: ${error.message}", error))
                    }
                }
            }
    }
    
    private fun translateNewsDetailWithDeepL(news: News): Mono<News> {
        val needsTitle = (news.titleKo.isNullOrBlank() || news.titleKo == news.title) && !isKoreanText(news.title)
        val needsDesc = news.description != null && 
            (news.descriptionKo.isNullOrBlank() || news.descriptionKo == news.description) && 
            !isKoreanText(news.description)
        val needsContent = news.content != null && 
            (news.contentKo.isNullOrBlank() || news.contentKo == news.content) && 
            !isKoreanText(news.content)
        
        if (!needsTitle && !needsDesc && !needsContent) {
            return Mono.just(news)
        }
        
        val titleMono = if (needsTitle) {
            deepLTranslationService.translateToKorean(news.title)
        } else {
            Mono.just(news.titleKo ?: news.title)
        }
        
        val descriptionMono = if (needsDesc) {
            deepLTranslationService.translateToKorean(news.description!!)
        } else {
            Mono.just(news.descriptionKo ?: news.description ?: "")
        }
        
        val contentMono = if (needsContent) {
            deepLTranslationService.translateToKorean(news.content!!)
        } else {
            Mono.just(news.contentKo ?: news.content ?: "")
        }
        
        return Mono.zip(titleMono, descriptionMono, contentMono)
            .map { tuple ->
                news.copy(
                    titleKo = if (needsTitle) tuple.t1 else (news.titleKo ?: news.title),
                    descriptionKo = if (needsDesc) tuple.t2 else (news.descriptionKo ?: news.description),
                    contentKo = if (needsContent) tuple.t3 else (news.contentKo ?: news.content)
                )
            }
            .timeout(Duration.ofSeconds(12))
            .onErrorReturn(news)
    }

    @GetMapping("/search")
    @Operation(summary = "뉴스 검색", description = "키워드로 뉴스를 검색합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 뉴스를 검색했습니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun searchNews(
        @Parameter(description = "검색 키워드", required = true)
        @RequestParam query: String,
        @Parameter(description = "언어 코드 (기본값: en)", required = false)
        @RequestParam(defaultValue = "en") language: String,
        @Parameter(description = "최대 결과 수 (1-100, 기본값: 20)", required = false)
        @RequestParam(defaultValue = "20") maxResults: Int
    ): Mono<List<News>> {
        val validMaxResults = if (maxResults in 1..100) maxResults else 20
        return circuitBreakerManager.executeWithCircuitBreaker("newsSearch") {
            pythonApiClient.searchNews(query, language, validMaxResults)
        }
            .timeout(Duration.ofSeconds(15))
            .onErrorResume { error: Throwable ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Mono.error(ExternalApiException("서비스가 일시적으로 사용 불가능합니다", error))
                    is java.util.concurrent.TimeoutException ->
                        Mono.error(ExternalApiException("요청 시간이 초과되었습니다", error))
                    else ->
                        Mono.error(ExternalApiException("뉴스 검색에 실패했습니다", error))
                }
            }
    }

    @GetMapping("/multiple")
    @Operation(summary = "다중 주식 뉴스 조회", description = "여러 심볼의 뉴스를 한 번에 조회합니다 (최대 10개)")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 뉴스를 조회했습니다"),
            ApiResponse(responseCode = "400", description = "심볼 개수가 10개를 초과합니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun getMultipleStockNews(
        @Parameter(description = "쉼표로 구분된 심볼 목록 (예: AAPL,GOOGL,MSFT)", required = true)
        @RequestParam symbols: String,
        @Parameter(description = "한글 번역 포함 여부 (기본값: false)", required = false)
        @RequestParam(defaultValue = "false") includeKorean: Boolean
    ): Mono<Map<String, List<News>>> {
        val symbolList = symbols.split(",").map { it.trim().uppercase() }
        if (symbolList.size > 10) {
            return Mono.error(IllegalArgumentException("요청당 최대 10개의 심볼만 허용됩니다"))
        }
        return circuitBreakerManager.executeWithCircuitBreaker("multipleNews") {
            pythonApiClient.getMultipleStockNews(symbolList, includeKorean)
        }
            .timeout(Duration.ofSeconds(20))
            .onErrorResume { error: Throwable ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Mono.error(ExternalApiException("서비스가 일시적으로 사용 불가능합니다", error))
                    is java.util.concurrent.TimeoutException ->
                        Mono.error(ExternalApiException("요청 시간이 초과되었습니다", error))
                    else ->
                        Mono.error(ExternalApiException("다중 주식 뉴스를 가져오는데 실패했습니다", error))
                }
            }
    }
}

