package com.sleekydz86.backend.application.controller

import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

@RestController
@RequestMapping("/api/stocks")
class StockController(
    private val pythonApiClient: PythonApiClient,
    private val circuitBreakerManager: CircuitBreakerManager
) {

    @GetMapping("/symbols")
    fun getSymbols(): Mono<List<String>> {
        return circuitBreakerManager.executeWithCircuitBreaker("symbols") {
            pythonApiClient.getSymbols()
        }
            .timeout(Duration.ofSeconds(10))
            .onErrorResume { error ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Mono.error(ExternalApiException("Service temporarily unavailable", error))
                    is java.util.concurrent.TimeoutException ->
                        Mono.error(ExternalApiException("Request timeout", error))
                    else ->
                        Mono.error(ExternalApiException("Failed to fetch symbols", error))
                }
            }
    }

    @GetMapping("/realtime/{symbol}")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    fun getRealtimeData(@PathVariable symbol: String): Mono<StockData> {
        if (symbol.isBlank() || !symbol.matches(Regex("[A-Z]{1,5}"))) {
            return Mono.error(InvalidSymbolException("Invalid stock symbol format"))
        }

        return circuitBreakerManager.executeWithCircuitBreaker("realtime") {
            pythonApiClient.getRealtimeData(symbol)
        }
            .timeout(Duration.ofSeconds(15))
            .onErrorResume { error ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Mono.error(ExternalApiException("Service temporarily unavailable", error))
                    is java.util.concurrent.TimeoutException ->
                        Mono.error(ExternalApiException("Request timeout", error))
                    else ->
                        Mono.error(ExternalApiException("Failed to fetch realtime data for $symbol", error))
                }
            }
    }

    @GetMapping("/analysis/{symbol}")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    fun getAnalysis(@PathVariable symbol: String): Mono<TechnicalAnalysis> {
        if (symbol.isBlank() || !symbol.matches(Regex("[A-Z]{1,5}"))) {
            return Mono.error(InvalidSymbolException("Invalid stock symbol format"))
        }

        return circuitBreakerManager.executeWithCircuitBreaker("analysis") {
            pythonApiClient.getAnalysis(symbol)
        }
            .timeout(Duration.ofSeconds(20))
            .onErrorResume { error ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Mono.error(ExternalApiException("Service temporarily unavailable", error))
                    is java.util.concurrent.TimeoutException ->
                        Mono.error(ExternalApiException("Request timeout", error))
                    else ->
                        Mono.error(ExternalApiException("Failed to fetch analysis for $symbol", error))
                }
            }
    }

    @GetMapping("/analysis")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    fun getAllAnalysis(): Flux<TechnicalAnalysis> {
        return circuitBreakerManager.executeFluxWithCircuitBreaker("allAnalysis") {
            pythonApiClient.getAllAnalysis()
        }
            .timeout(Duration.ofSeconds(45))
            .onErrorResume { error ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Flux.error(ExternalApiException("Service temporarily unavailable", error))
                    is java.util.concurrent.TimeoutException ->
                        Flux.error(ExternalApiException("Request timeout", error))
                    else ->
                        Flux.error(ExternalApiException("Failed to fetch all analysis", error))
                }
            }
    }

    @GetMapping("/historical/{symbol}")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    fun getHistoricalData(
        @PathVariable symbol: String,
        @RequestParam(defaultValue = "30") days: Int
    ): Mono<HistoricalData> {
        if (symbol.isBlank() || !symbol.matches(Regex("[A-Z]{1,5}"))) {
            return Mono.error(InvalidSymbolException("Invalid stock symbol format"))
        }

        val validDays = if (days in 1..365) days else 30

        return circuitBreakerManager.executeWithCircuitBreaker("historical") {
            pythonApiClient.getHistoricalData(symbol, validDays)
        }
            .timeout(Duration.ofSeconds(25))
            .onErrorResume { error ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Mono.error(ExternalApiException("Service temporarily unavailable", error))
                    is java.util.concurrent.TimeoutException ->
                        Mono.error(ExternalApiException("Request timeout", error))
                    else ->
                        Mono.error(ExternalApiException("Failed to fetch historical data for $symbol", error))
                }
            }
    }

    @GetMapping("/circuit-breaker/status")
    fun getCircuitBreakerStatus(): Mono<Map<String, Map<String, Any>>> {
        return Mono.just(circuitBreakerManager.getAllCircuitBreakerStatus())
    }

    @PostMapping("/circuit-breaker/reset/{name}")
    fun resetCircuitBreaker(@PathVariable name: String): Mono<String> {
        circuitBreakerManager.resetCircuitBreaker(name)
        return Mono.just("Circuit breaker '$name' reset successfully")
    }
}
