package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.domain.model.HistoricalData
import com.sleekydz86.backend.domain.model.StockData
import com.sleekydz86.backend.domain.model.TechnicalAnalysis
import com.sleekydz86.backend.global.circuitbreaker.CircuitBreakerManager
import com.sleekydz86.backend.global.exception.CircuitBreakerOpenException
import com.sleekydz86.backend.global.exception.ExternalApiException
import com.sleekydz86.backend.global.exception.InvalidSymbolException
import com.sleekydz86.backend.infrastructure.client.PythonApiClient
import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.Parameter
import io.swagger.v3.oas.annotations.responses.ApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import io.swagger.v3.oas.annotations.tags.Tag
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

@RestController
@RequestMapping("/api/stocks")
@Tag(name = "주식 API", description = "주식 데이터 조회 및 기술적 분석 API")
class StockController(
    private val pythonApiClient: PythonApiClient,
    private val circuitBreakerManager: CircuitBreakerManager
) {

    @GetMapping("/symbols")
    @Operation(summary = "사용 가능한 심볼 목록 조회", description = "분석 가능한 주식 심볼 목록을 반환합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 심볼 목록을 조회했습니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun getSymbols(): Mono<List<String>> {
        return circuitBreakerManager.executeWithCircuitBreaker("symbols") {
            pythonApiClient.getSymbols()
        }
            .timeout(Duration.ofSeconds(10))
            .onErrorResume { error: Throwable ->
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
    @Operation(summary = "실시간 주식 데이터 조회", description = "특정 심볼의 실시간 주식 데이터를 조회합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 실시간 데이터를 조회했습니다"),
            ApiResponse(responseCode = "400", description = "잘못된 심볼 형식입니다"),
            ApiResponse(responseCode = "401", description = "인증이 필요합니다"),
            ApiResponse(responseCode = "403", description = "접근 권한이 없습니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun getRealtimeData(
        @Parameter(description = "주식 심볼 (예: AAPL, GOOGL, MSFT)", required = true)
        @PathVariable symbol: String
    ): Mono<StockData> {
        if (symbol.isBlank() || !symbol.matches(Regex("[A-Z]{1,5}"))) {
            return Mono.error(InvalidSymbolException("Invalid stock symbol format"))
        }

        return circuitBreakerManager.executeWithCircuitBreaker("realtime") {
            pythonApiClient.getRealtimeData(symbol)
        }
            .timeout(Duration.ofSeconds(15))
            .onErrorResume { error: Throwable ->
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
    @Operation(summary = "주식 기술적 분석 조회", description = "특정 심볼의 기술적 분석 결과를 조회합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 분석 데이터를 조회했습니다"),
            ApiResponse(responseCode = "400", description = "잘못된 심볼 형식입니다"),
            ApiResponse(responseCode = "401", description = "인증이 필요합니다"),
            ApiResponse(responseCode = "403", description = "접근 권한이 없습니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun getAnalysis(
        @Parameter(description = "주식 심볼 (예: AAPL, GOOGL, MSFT)", required = true)
        @PathVariable symbol: String
    ): Mono<TechnicalAnalysis> {
        if (symbol.isBlank() || !symbol.matches(Regex("[A-Z]{1,5}"))) {
            return Mono.error(InvalidSymbolException("Invalid stock symbol format"))
        }

        return circuitBreakerManager.executeWithCircuitBreaker("analysis") {
            pythonApiClient.getAnalysis(symbol)
        }
            .timeout(Duration.ofSeconds(20))
            .onErrorResume { error: Throwable ->
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
    @Operation(summary = "전체 주식 분석 조회", description = "모든 주식의 기술적 분석 결과를 스트림으로 조회합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 분석 데이터를 조회했습니다"),
            ApiResponse(responseCode = "401", description = "인증이 필요합니다"),
            ApiResponse(responseCode = "403", description = "접근 권한이 없습니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun getAllAnalysis(): Flux<TechnicalAnalysis> {
        return circuitBreakerManager.executeFluxWithCircuitBreaker("allAnalysis") {
            pythonApiClient.getAllAnalysis()
        }
            .timeout(Duration.ofSeconds(45))
            .onErrorResume { error: Throwable ->
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
    @Operation(summary = "과거 주식 데이터 조회", description = "특정 심볼의 과거 주식 데이터를 조회합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 과거 데이터를 조회했습니다"),
            ApiResponse(responseCode = "400", description = "잘못된 심볼 형식 또는 일수입니다"),
            ApiResponse(responseCode = "401", description = "인증이 필요합니다"),
            ApiResponse(responseCode = "403", description = "접근 권한이 없습니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun getHistoricalData(
        @Parameter(description = "주식 심볼 (예: AAPL, GOOGL, MSFT)", required = true)
        @PathVariable symbol: String,
        @Parameter(description = "조회할 일수 (1-365, 기본값: 30)", required = false)
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
            .onErrorResume { error: Throwable ->
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
