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
    
    init {
        logger.info("PythonApiClient initialized with baseUrl: $baseUrl")
        logger.debug("WebClient configured for Python API at: $baseUrl")
    }

    private val mapToStockData: (Map<*, *>) -> StockData = { data ->
        try {
            logger.debug("Mapping stock data from Python API response. Keys: ${data.keys}, Data: $data")
            
            val symbol = (data["symbol"] as? String) ?: throw IllegalArgumentException("Missing or invalid symbol field: $data")
            
            val currentPrice = try {
                val priceValue = (data["currentPrice"] as? Number) ?: (data["price"] as? Number)
                if (priceValue == null) {
                    logger.error("Price field missing or null in data: $data")
                    throw IllegalArgumentException("Missing or invalid price field")
                }
                priceValue.toDouble()
            } catch (e: Exception) {
                logger.error("Error parsing price from data: $data", e)
                throw com.sleekydz86.backend.global.exception.DataProcessingException("Invalid price data format: ${e.message}", e)
            }
            
            val volume = try {
                val volumeValue = data["volume"]
                logger.debug("Volume value: $volumeValue (type: ${volumeValue?.javaClass?.name})")
                when (volumeValue) {
                    is Number -> volumeValue.toLong()
                    null -> {
                        logger.warn("Volume is null, defaulting to 0L")
                        0L
                    }
                    else -> {
                        logger.warn("Volume is not a Number (type: ${volumeValue.javaClass.name}), attempting conversion")
                        (volumeValue as? Number)?.toLong() ?: 0L
                    }
                }
            } catch (e: Exception) {
                logger.error("Error parsing volume from data: $data", e)
                throw com.sleekydz86.backend.global.exception.DataProcessingException("Invalid volume data format: ${e.message}", e)
            }
            
            val changePercent = try {
                val changePercentValue = (data["changePercent"] as? Number) ?: (data["change_percent"] as? Number)
                if (changePercentValue == null) {
                    logger.error("ChangePercent field missing or null in data: $data")
                    throw IllegalArgumentException("Missing or invalid changePercent field")
                }
                changePercentValue.toDouble()
            } catch (e: Exception) {
                logger.error("Error parsing changePercent from data: $data", e)
                throw com.sleekydz86.backend.global.exception.DataProcessingException("Invalid changePercent data format: ${e.message}", e)
            }
            
            val confidenceScore = (data["confidenceScore"] as? Number ?: data["confidence_score"] as? Number)?.toDouble()
            
            logger.debug("Successfully mapped stock data: symbol=$symbol, price=$currentPrice, volume=$volume, changePercent=$changePercent")
            
            StockData(
                symbol = symbol,
                currentPrice = currentPrice,
                volume = volume,
                changePercent = changePercent,
                timestamp = LocalDateTime.now(),
                confidenceScore = confidenceScore
            )
        } catch (e: Exception) {
            logger.error("Error mapping stock data from Python API response. Data: $data", e)
            logger.error("Exception type: ${e.javaClass.name}, message: ${e.message}", e)
            if (e is com.sleekydz86.backend.global.exception.DataProcessingException) {
                throw e
            }
            throw com.sleekydz86.backend.global.exception.DataProcessingException(
                "Failed to parse stock data from Python API: ${e.message}. Response data: $data",
                e
            )
        }
    }

    val getRealtimeData: (String) -> Mono<StockData> = { symbol ->
        val url = "$baseUrl/api/realtime/$symbol"
        logger.info("Requesting realtime data for symbol: $symbol from $url")
        
        webClient.get()
            .uri("/api/realtime/{symbol}", symbol)
            .retrieve()
            .onStatus({ status -> status.is5xxServerError || status.is4xxClientError }, { response ->
                logger.error("Python API 서버 HTTP 오류: ${response.statusCode()} (symbol: $symbol, url: $url)")
                response.bodyToMono(String::class.java)
                    .defaultIfEmpty("")
                    .doOnNext { body ->
                        logger.error("Python API error response body: $body")
                    }
                    .flatMap { body ->
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류 (${response.statusCode()}): ${if (body.isNotEmpty()) body else "서버가 오류를 반환했습니다"}. Python API 서버 로그를 확인하세요."
                        ))
                    }
            })
            .bodyToMono(Map::class.java)
            .doOnNext { data ->
                logger.info("Received response from Python API for symbol $symbol. Response keys: ${data.keys}")
                logger.debug("Full response data: $data")
            }
            .flatMap { data ->
                try {
                    logger.debug("Parsing stock data for symbol: $symbol")
                    val stockData = mapToStockData(data)
                    logger.info("Successfully parsed stock data for symbol: $symbol")
                    Mono.just(stockData)
                } catch (e: Exception) {
                    logger.error("Error parsing stock data response for symbol: $symbol", e)
                    logger.error("Exception type: ${e.javaClass.name}, message: ${e.message}")
                    logger.error("Response data that failed to parse: $data")
                    logger.error("Response data type: ${data.javaClass.name}")
                    logger.error("Response data keys: ${data.keys}")
                    Mono.error(
                        when (e) {
                            is com.sleekydz86.backend.global.exception.DataProcessingException -> e
                            else -> com.sleekydz86.backend.global.exception.DataProcessingException(
                                "Failed to parse stock data from Python API response: ${e.message}. Response data: $data",
                                e
                            )
                        }
                    )
                }
            }
            .timeout(java.time.Duration.ofSeconds(10))
            .doOnError { error ->
                logger.error("Failed to get realtime data for symbol: $symbol from $baseUrl", error)
                logger.error("Error type: ${error.javaClass.name}, message: ${error.message}")
                if (error.cause != null) {
                    logger.error("Error cause: ${error.cause?.javaClass?.name}, message: ${error.cause?.message}", error.cause)
                }
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
                        logger.error("Python API 서버 연결 실패: $baseUrl (symbol: $symbol)", error)
                        logger.error("WebClientException details: ${error.message}")
                        com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결 실패: ${baseUrl}. 서버가 실행 중인지 확인하세요. (서버 시작: python start_python_api.py 또는 uvicorn api_server:app --port 9000). Error: ${error.message}",
                            error
                        )
                    }
                    is com.fasterxml.jackson.databind.JsonMappingException,
                    is com.fasterxml.jackson.core.JsonParseException -> {
                        logger.error("JSON 파싱 오류: $baseUrl (symbol: $symbol)", error)
                        com.sleekydz86.backend.global.exception.DataProcessingException(
                            "Python API 서버 응답 형식 오류: JSON 파싱 실패. Error: ${error.message}",
                            error
                        )
                    }
                    is com.sleekydz86.backend.global.exception.DataProcessingException -> {
                        logger.error("DataProcessingException for symbol: $symbol", error)
                        error
                    }
                    else -> {
                        // 이미 ExternalApiException으로 변환된 경우 그대로 반환
                        if (error is com.sleekydz86.backend.global.exception.ExternalApiException) {
                            error
                        } else {
                            logger.error("Unexpected Python API 서버 오류: ${error.message} (symbol: $symbol, type: ${error.javaClass.name})", error)
                            com.sleekydz86.backend.global.exception.ExternalApiException(
                                "Python API 서버 오류: ${error.message ?: error.javaClass.simpleName}",
                                error
                            )
                        }
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