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
import org.slf4j.LoggerFactory

@RestController
@RequestMapping("/api/stocks")
@Tag(name = "주식 API", description = "주식 데이터 조회 및 기술적 분석 API")
class StockController(
    private val pythonApiClient: PythonApiClient,
    private val circuitBreakerManager: CircuitBreakerManager
) {
    private val logger = LoggerFactory.getLogger(StockController::class.java)

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

    @GetMapping("/top-performers")
    @Operation(summary = "최고 성과 종목 추천", description = "가장 높은 수익률, RSI, MACD 신호를 가진 종목을 추천합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 최고 성과 종목을 조회했습니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun getTopPerformers(
        @Parameter(description = "최대 반환 개수 (기본값: 3)", required = false)
        @RequestParam(defaultValue = "3") limit: Int
    ): Mono<List<Map<String, Any>>> {
        logger.info("최고 성과 종목 조회 시작: limit={}", limit)
        return circuitBreakerManager.executeFluxWithCircuitBreaker("allAnalysis") {
            pythonApiClient.getAllAnalysis()
        }
            .timeout(Duration.ofSeconds(70))
            .collectList()
            .doOnNext { analysisList ->
                logger.info("최고 성과 종목 조회: {}개 분석 데이터 수신", analysisList.size)
            }
            .map { analysisList: List<TechnicalAnalysis> ->
                if (analysisList.isEmpty()) {
                    logger.warn("최고 성과 종목 조회: 분석 데이터가 비어있습니다. Python API 응답을 확인하세요.")
                    return@map emptyList<Map<String, Any>>()
                }
                
                logger.info("최고 성과 종목 점수 계산 시작: {}개 종목", analysisList.size)
                val scored = analysisList.map { analysis: TechnicalAnalysis ->
                    val score = calculatePerformanceScore(analysis)
                    mapOf<String, Any>(
                        "symbol" to analysis.symbol,
                        "currentPrice" to analysis.currentPrice,
                        "changePercent" to analysis.changePercent,
                        "rsi" to (analysis.signals.rsi ?: 0.0),
                        "macd" to (analysis.signals.macd ?: 0.0),
                        "confidence" to analysis.signals.confidence,
                        "trendStrength" to analysis.trendStrength,
                        "signal" to analysis.signals.signal,
                        "score" to score
                    )
                }
                val topPerformers = scored.sortedByDescending { item -> item["score"] as Double }.take(limit)
                logger.info("최고 성과 종목 조회 완료: {}개 반환", topPerformers.size)
                topPerformers
            }
            .onErrorResume { error: Throwable ->
                logger.error("최고 성과 종목 조회 실패: error={}, message={}", error.javaClass.simpleName, error.message, error)
                when (error) {
                    is CircuitBreakerOpenException -> {
                        logger.error("Circuit Breaker가 열려있습니다. Python API 서버 상태를 확인하세요.")
                        Mono.just(emptyList<Map<String, Any>>())
                    }
                    is java.util.concurrent.TimeoutException -> {
                        logger.error("최고 성과 종목 조회 타임아웃 (60초 초과)")
                        Mono.just(emptyList<Map<String, Any>>())
                    }
                    else -> {
                        logger.error("최고 성과 종목 조회 예상치 못한 오류", error)
                        Mono.just(emptyList<Map<String, Any>>())
                    }
                }
            }
    }

    private fun calculatePerformanceScore(analysis: TechnicalAnalysis): Double {
        val changeScore = analysis.changePercent * 10.0
        val rsiScore = when {
            analysis.signals.rsi != null && analysis.signals.rsi!! in 50.0..70.0 -> 20.0
            analysis.signals.rsi != null && analysis.signals.rsi!! > 70.0 -> 10.0
            else -> 0.0
        }
        val macdScore = when {
            analysis.signals.macd != null && analysis.signals.macdSignal != null -> {
                if (analysis.signals.macd!! > analysis.signals.macdSignal!!) 15.0 else 0.0
            }
            else -> 0.0
        }
        val confidenceScore = analysis.signals.confidence * 10.0
        val trendScore = analysis.trendStrength * 15.0
        val signalScore = when (analysis.signals.signal.lowercase()) {
            "buy", "strong_buy" -> 20.0
            "hold" -> 5.0
            else -> 0.0
        }
        return changeScore + rsiScore + macdScore + confidenceScore + trendScore + signalScore
    }

    @GetMapping("/sectors")
    @Operation(summary = "섹터별 분석", description = "섹터별로 그룹화된 종목 분석 결과를 조회합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 섹터별 분석을 조회했습니다"),
            ApiResponse(responseCode = "503", description = "서비스가 일시적으로 사용 불가능합니다")
        ]
    )
    fun getSectorsAnalysis(): Mono<List<Map<String, Any>>> {
        return circuitBreakerManager.executeWithCircuitBreaker("sectors") {
            pythonApiClient.getSectorsAnalysis()
        }
            .timeout(Duration.ofSeconds(50))
            .onErrorResume { error: Throwable ->
                when (error) {
                    is CircuitBreakerOpenException ->
                        Mono.error(ExternalApiException("Service temporarily unavailable", error))
                    is java.util.concurrent.TimeoutException -> {
                        logger.warn("섹터 분석 타임아웃: 더미 데이터를 반환합니다.")
                        Mono.just(emptyList<Map<String, Any>>())
                    }
                    else ->
                        Mono.error(ExternalApiException("Failed to fetch sectors analysis", error))
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
