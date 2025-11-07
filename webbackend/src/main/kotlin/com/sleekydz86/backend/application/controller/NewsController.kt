package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.domain.model.News
import com.sleekydz86.backend.global.circuitbreaker.CircuitBreakerManager
import com.sleekydz86.backend.global.exception.CircuitBreakerOpenException
import com.sleekydz86.backend.global.exception.ExternalApiException
import com.sleekydz86.backend.infrastructure.client.PythonApiClient
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono
import java.time.Duration

@RestController
@RequestMapping("/api/news")
class NewsController(
    private val pythonApiClient: PythonApiClient,
    private val circuitBreakerManager: CircuitBreakerManager
) {

    @GetMapping("/{symbol}")
    fun getStockNews(
        @PathVariable symbol: String,
        @RequestParam(defaultValue = "false") includeKorean: Boolean,
        @RequestParam(defaultValue = "true") autoTranslate: Boolean
    ): Mono<List<News>> {
        return circuitBreakerManager.executeWithCircuitBreaker("news") {
            pythonApiClient.getStockNews(symbol.uppercase(), includeKorean, autoTranslate)
        }
            .timeout(Duration.ofSeconds(15))
            .onErrorResume { error: Throwable ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Mono.error(ExternalApiException("Service temporarily unavailable", error))
                    is java.util.concurrent.TimeoutException ->
                        Mono.error(ExternalApiException("Request timeout", error))
                    else ->
                        Mono.error(ExternalApiException("Failed to fetch news for $symbol", error))
                }
            }
    }
    
    @GetMapping("/detail/{newsId}")
    fun getNewsDetail(
        @PathVariable newsId: String
    ): Mono<News> {
        return circuitBreakerManager.executeWithCircuitBreaker("newsDetail") {
            pythonApiClient.getNewsByUrl(java.net.URLDecoder.decode(newsId, "UTF-8"))
        }
            .timeout(Duration.ofSeconds(10))
            .onErrorResume { error: Throwable ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Mono.error(ExternalApiException("Service temporarily unavailable", error))
                    is java.util.concurrent.TimeoutException ->
                        Mono.error(ExternalApiException("Request timeout", error))
                    else ->
                        Mono.error(ExternalApiException("Failed to fetch news detail", error))
                }
            }
    }

    @GetMapping("/search")
    fun searchNews(
        @RequestParam query: String,
        @RequestParam(defaultValue = "en") language: String,
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
                        Mono.error(ExternalApiException("Service temporarily unavailable", error))
                    is java.util.concurrent.TimeoutException ->
                        Mono.error(ExternalApiException("Request timeout", error))
                    else ->
                        Mono.error(ExternalApiException("Failed to search news", error))
                }
            }
    }

    @GetMapping("/multiple")
    fun getMultipleStockNews(
        @RequestParam symbols: String,
        @RequestParam(defaultValue = "false") includeKorean: Boolean
    ): Mono<Map<String, List<News>>> {
        val symbolList = symbols.split(",").map { it.trim().uppercase() }
        if (symbolList.size > 10) {
            return Mono.error(IllegalArgumentException("Maximum 10 symbols allowed per request"))
        }
        return circuitBreakerManager.executeWithCircuitBreaker("multipleNews") {
            pythonApiClient.getMultipleStockNews(symbolList, includeKorean)
        }
            .timeout(Duration.ofSeconds(20))
            .onErrorResume { error: Throwable ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Mono.error(ExternalApiException("Service temporarily unavailable", error))
                    is java.util.concurrent.TimeoutException ->
                        Mono.error(ExternalApiException("Request timeout", error))
                    else ->
                        Mono.error(ExternalApiException("Failed to fetch multiple stock news", error))
                }
            }
    }
}

