package com.sleekydz86.backend.infrastructure.client

import com.sleekydz86.backend.domain.model.*
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Component
import org.springframework.web.reactive.function.client.WebClient
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.LocalDateTime

@Component
class PythonApiClient(
    @Value("\${python.api.base-url:http://localhost:8000}")
    private val baseUrl: String
) {
    private val logger = org.slf4j.LoggerFactory.getLogger(PythonApiClient::class.java)

    private val webClient = WebClient.builder()
        .baseUrl(baseUrl)
        .build()

    private val mapToStockData: (Map<*, *>) -> StockData = { data ->
        StockData(
            symbol = data["symbol"] as String,
            currentPrice = (data["currentPrice"] as? Number ?: data["price"] as Number).toDouble(),
            volume = (data["volume"] as Number).toLong(),
            changePercent = (data["changePercent"] as? Number ?: data["change_percent"] as Number).toDouble(),
            timestamp = LocalDateTime.now(),
            confidenceScore = (data["confidenceScore"] as? Number ?: data["confidence_score"] as? Number)?.toDouble()
        )
    }

    val getRealtimeData: (String) -> Mono<StockData> = { symbol ->
        logger.debug("Requesting realtime data for symbol: $symbol from $baseUrl")
        webClient.get()
            .uri("/api/realtime/{symbol}", symbol)
            .retrieve()
            .bodyToMono(Map::class.java)
            .map(mapToStockData)
            .timeout(java.time.Duration.ofSeconds(10))
            .doOnError { error ->
                logger.error("Failed to get realtime data for symbol: $symbol from $baseUrl", error)
            }
            .onErrorMap { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException -> {
                        logger.error("Python API 서버 연결 시간 초과: $baseUrl (symbol: $symbol)")
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 시간 초과: ${baseUrl}. 서버가 실행 중인지 확인하세요.",
                            error
                        )
                    }
                    is org.springframework.web.reactive.function.client.WebClientException -> {
                        logger.error("Python API 서버 연결 실패: $baseUrl (symbol: $symbol). 서버가 실행 중인지 확인하세요.")
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 실패: ${baseUrl}. 서버가 실행 중인지 확인하세요. (서버 시작: python start_python_api.py 또는 uvicorn api_server:app --port 9000)",
                            error
                        )
                    }
                    else -> {
                        logger.error("Python API 서버 오류: ${error.message} (symbol: $symbol)")
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류: ${error.message}",
                            error
                        )
                    }
                }
            }
    }

    private val mapToTradingSignals: (Map<*, *>) -> TradingSignals = { signalsData ->
        TradingSignals(
            signal = signalsData["signal"] as String,
            confidence = (signalsData["confidence"] as Number).toDouble(),
            rsi = (signalsData["rsi"] as? Number)?.toDouble(),
            macd = (signalsData["macd"] as? Number)?.toDouble(),
            macdSignal = (signalsData["macd_signal"] as? Number)?.toDouble()
        )
    }

    private val mapToAnomaly: (Map<*, *>) -> Anomaly = { anomalyMap ->
        Anomaly(
            type = anomalyMap["type"] as String,
            severity = anomalyMap["severity"] as String,
            message = anomalyMap["message"] as String,
            timestamp = LocalDateTime.parse(anomalyMap["timestamp"] as String)
        )
    }

    private val mapToChartPattern: (Map<*, *>) -> ChartPattern = { patternMap ->
        ChartPattern(
            type = patternMap["type"] as String,
            confidence = (patternMap["confidence"] as Number).toDouble(),
            signal = patternMap["signal"] as String,
            description = patternMap["description"] as? String
        )
    }

    private val mapToSupportResistanceLevel: (Map<*, *>) -> SupportResistanceLevel = { levelMap ->
        SupportResistanceLevel(
            level = (levelMap["level"] as Number).toDouble(),
            touches = (levelMap["touches"] as Number).toInt(),
            strength = (levelMap["strength"] as Number).toDouble()
        )
    }

    private val mapToSupportResistance: (Map<*, *>) -> SupportResistance = { srMap ->
        val supportData = (srMap["support"] as List<*>).map { it as Map<*, *> }.map(mapToSupportResistanceLevel)
        val resistanceData = (srMap["resistance"] as List<*>).map { it as Map<*, *> }.map(mapToSupportResistanceLevel)
        SupportResistance(support = supportData, resistance = resistanceData)
    }

    private val mapToFibonacciLevels: (Map<*, *>) -> FibonacciLevels = { fibMap ->
        val levelsMap = (fibMap["levels"] as Map<*, *>).mapKeys { it.key.toString() }.mapValues { (it.value as Number).toDouble() }
        FibonacciLevels(
            levels = levelsMap,
            nearestLevel = fibMap["nearest_level"] as String,
            distanceToNearest = (fibMap["distance_to_nearest"] as Number).toDouble()
        )
    }

    private val mapToTechnicalAnalysis: (Map<*, *>) -> TechnicalAnalysis = { data ->
        val signalsData = data["signals"] as Map<*, *>
        val anomaliesData = data["anomalies"] as List<*>

        TechnicalAnalysis(
            symbol = data["symbol"] as String,
            currentPrice = (data["currentPrice"] as? Number ?: data["current_price"] as Number).toDouble(),
            volume = (data["volume"] as Number).toLong(),
            changePercent = (data["changePercent"] as? Number ?: data["change_percent"] as Number).toDouble(),
            trend = data["trend"] as String,
            trendStrength = (data["trendStrength"] as? Number ?: data["trend_strength"] as Number).toDouble(),
            signals = mapToTradingSignals(signalsData),
            anomalies = anomaliesData.map { it as Map<*, *> }.map(mapToAnomaly),
            timestamp = LocalDateTime.parse(data["timestamp"] as String),
            marketRegime = data["marketRegime"] as? String ?: data["market_regime"] as? String,
            patterns = (data["patterns"] as? List<*>)?.map { it as Map<*, *> }?.map(mapToChartPattern),
            supportResistance = (data["supportResistance"] as? Map<*, *> ?: data["support_resistance"] as? Map<*, *>)?.let(mapToSupportResistance),
            fibonacciLevels = (data["fibonacciLevels"] as? Map<*, *> ?: data["fibonacci_levels"] as? Map<*, *>)?.let(mapToFibonacciLevels),
            riskScore = (data["riskScore"] as? Number ?: data["risk_score"] as? Number)?.toDouble(),
            confidence = (data["confidence"] as? Number)?.toDouble()
        )
    }

    val getAnalysis: (String) -> Mono<TechnicalAnalysis> = { symbol ->
        webClient.get()
            .uri("/api/analysis/{symbol}", symbol)
            .retrieve()
            .bodyToMono(Map::class.java)
            .map(mapToTechnicalAnalysis)
            .timeout(java.time.Duration.ofSeconds(15))
            .onErrorMap { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 시간 초과: ${baseUrl}",
                            error
                        )
                    is org.springframework.web.reactive.function.client.WebClientException ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 실패. 서버가 실행 중인지 확인하세요: ${baseUrl}",
                            error
                        )
                    else ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류: ${error.message}",
                            error
                        )
                }
            }
    }

    val getAllAnalysis: () -> Flux<TechnicalAnalysis> = {
        webClient.get()
            .uri("/api/analysis/all")
            .retrieve()
            .bodyToFlux(Map::class.java)
            .map(mapToTechnicalAnalysis)
            .timeout(java.time.Duration.ofSeconds(20))
            .onErrorMap { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 시간 초과: ${baseUrl}",
                            error
                        )
                    is org.springframework.web.reactive.function.client.WebClientException ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 실패. 서버가 실행 중인지 확인하세요: ${baseUrl}",
                            error
                        )
                    else ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류: ${error.message}",
                            error
                        )
                }
            }
    }

    private val mapToChartDataPoint: (Map<*, *>) -> ChartDataPoint = { pointMap ->
        ChartDataPoint(
            date = pointMap["date"] as String,
            close = (pointMap["close"] as Number).toDouble(),
            volume = (pointMap["volume"] as Number).toLong(),
            rsi = (pointMap["rsi"] as? Number)?.toDouble(),
            macd = (pointMap["macd"] as? Number)?.toDouble(),
            bbUpper = (pointMap["bb_upper"] as? Number)?.toDouble(),
            bbLower = (pointMap["bb_lower"] as? Number)?.toDouble(),
            sma20 = (pointMap["sma_20"] as? Number)?.toDouble()
        )
    }

    private val mapToHistoricalData: (Map<*, *>) -> HistoricalData = { data ->
        val chartData = (data["data"] as List<*>)
            .map { it as Map<*, *> }
            .map(mapToChartDataPoint)

        HistoricalData(
            symbol = data["symbol"] as String,
            data = chartData,
            period = data["period"] as Int
        )
    }

    val getHistoricalData: (String, Int) -> Mono<HistoricalData> = { symbol, days ->
        webClient.get()
            .uri("/api/historical/{symbol}?days={days}", symbol, days)
            .retrieve()
            .bodyToMono(Map::class.java)
            .map(mapToHistoricalData)
            .timeout(java.time.Duration.ofSeconds(15))
            .onErrorMap { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 시간 초과: ${baseUrl}",
                            error
                        )
                    is org.springframework.web.reactive.function.client.WebClientException ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 실패. 서버가 실행 중인지 확인하세요: ${baseUrl}",
                            error
                        )
                    else ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류: ${error.message}",
                            error
                        )
                }
            }
    }

    val getSymbols: () -> Mono<List<String>> = {
        webClient.get()
            .uri("/api/symbols")
            .retrieve()
            .bodyToMono(Map::class.java)
            .map { data -> data["symbols"] as List<String> }
            .timeout(java.time.Duration.ofSeconds(10))
            .onErrorMap { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 시간 초과: ${baseUrl}",
                            error
                        )
                    is org.springframework.web.reactive.function.client.WebClientException ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 실패. 서버가 실행 중인지 확인하세요: ${baseUrl}",
                            error
                        )
                    else ->
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류: ${error.message}",
                            error
                        )
                }
            }
    }

    fun sendEmail(toEmail: String, subject: String, content: String): Mono<Boolean> {
        return webClient.post()
            .uri("/api/notifications/email")
            .bodyValue(mapOf(
                "to_email" to toEmail,
                "subject" to subject,
                "body" to content
            ))
            .retrieve()
            .bodyToMono(Map::class.java)
            .map { response ->
                response["success"] as? Boolean ?: false
            }
            .onErrorReturn(false)
    }
}