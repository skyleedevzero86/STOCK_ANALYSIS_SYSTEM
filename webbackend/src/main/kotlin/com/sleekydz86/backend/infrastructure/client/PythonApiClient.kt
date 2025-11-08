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
    @Value("\${python.api.base-url:http://localhost:9000}")
    private val baseUrl: String
) {
    private val logger = org.slf4j.LoggerFactory.getLogger(PythonApiClient::class.java)

    private val webClient = WebClient.builder()
        .baseUrl(baseUrl)
        .build()
    
    init {
        logger.debug("PythonApiClient 초기화 완료: baseUrl=$baseUrl")
        logger.debug("Python API용 WebClient 설정 완료: $baseUrl")
    }

    private val mapToStockData: (Map<*, *>) -> StockData = { data ->
        try {
            logger.debug("Python API 응답에서 주식 데이터 매핑 중. Keys: ${data.keys}, Data: $data")
            
            val symbol = (data["symbol"] as? String) ?: throw IllegalArgumentException("Missing or invalid symbol field: $data")
            
            val currentPrice = try {
                val priceValue = (data["currentPrice"] as? Number) ?: (data["price"] as? Number)
                if (priceValue == null) {
                    logger.error("데이터에서 가격 필드가 누락되었거나 null입니다: $data")
                    throw IllegalArgumentException("Missing or invalid price field")
                }
                priceValue.toDouble()
            } catch (e: Exception) {
                logger.error("데이터에서 가격 파싱 오류: $data", e)
                throw com.sleekydz86.backend.global.exception.DataProcessingException("Invalid price data format: ${e.message}", e)
            }
            
            val volume = try {
                val volumeValue = data["volume"]
                logger.debug("거래량 값: $volumeValue (타입: ${volumeValue?.javaClass?.name})")
                when (volumeValue) {
                    is Number -> volumeValue.toLong()
                    null -> {
                        logger.warn("거래량이 null입니다. 기본값 0L로 설정합니다")
                        0L
                    }
                    else -> {
                        logger.warn("거래량이 Number 타입이 아닙니다 (타입: ${volumeValue.javaClass.name}). 변환을 시도합니다")
                        (volumeValue as? Number)?.toLong() ?: 0L
                    }
                }
            } catch (e: Exception) {
                logger.error("데이터에서 거래량 파싱 오류: $data", e)
                throw com.sleekydz86.backend.global.exception.DataProcessingException("Invalid volume data format: ${e.message}", e)
            }
            
            val changePercent = try {
                val changePercentValue = (data["changePercent"] as? Number) ?: (data["change_percent"] as? Number)
                if (changePercentValue == null) {
                    logger.error("데이터에서 변동률 필드가 누락되었거나 null입니다: $data")
                    throw IllegalArgumentException("Missing or invalid changePercent field")
                }
                changePercentValue.toDouble()
            } catch (e: Exception) {
                logger.error("데이터에서 변동률 파싱 오류: $data", e)
                throw com.sleekydz86.backend.global.exception.DataProcessingException("Invalid changePercent data format: ${e.message}", e)
            }
            
            val confidenceScore = (data["confidenceScore"] as? Number ?: data["confidence_score"] as? Number)?.toDouble()
            
            logger.debug("주식 데이터 매핑 완료: symbol=$symbol, price=$currentPrice, volume=$volume, changePercent=$changePercent")
            
            StockData(
                symbol = symbol,
                currentPrice = currentPrice,
                volume = volume,
                changePercent = changePercent,
                timestamp = LocalDateTime.now(),
                confidenceScore = confidenceScore
            )
        } catch (e: Exception) {
            logger.error("Python API 응답에서 주식 데이터 매핑 오류. Data: $data", e)
            logger.error("예외 타입: ${e.javaClass.name}, 메시지: ${e.message}", e)
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
        logger.debug("실시간 데이터 요청 중: symbol=$symbol, url=$url")
        
        webClient.get()
            .uri("/api/realtime/{symbol}", symbol)
            .retrieve()
            .onStatus({ status -> status.is5xxServerError || status.is4xxClientError }, { response ->
                logger.debug("Python API 서버 HTTP 오류: ${response.statusCode()} (symbol: $symbol, url: $url)")
                response.bodyToMono(String::class.java)
                    .defaultIfEmpty("")
                    .flatMap { body ->
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류 (${response.statusCode()}): ${if (body.isNotEmpty()) body else "서버가 오류를 반환했습니다"}"
                        ))
                    }
            })
            .bodyToMono(Map::class.java)
            .doOnNext { data ->
                logger.debug("Python API로부터 응답 수신: symbol=$symbol, Response keys: ${data.keys}")
            }
            .flatMap { data ->
                try {
                    logger.debug("주식 데이터 파싱 중: symbol=$symbol")
                    val stockData = mapToStockData(data)
                    logger.debug("주식 데이터 파싱 완료: symbol=$symbol")
                    Mono.just(stockData)
                } catch (e: Exception) {
                    logger.debug("주식 데이터 응답 파싱 오류: symbol=$symbol", e)
                    Mono.error(
                        when (e) {
                            is com.sleekydz86.backend.global.exception.DataProcessingException -> e
                            else -> com.sleekydz86.backend.global.exception.DataProcessingException(
                                "Failed to parse stock data from Python API response: ${e.message}",
                                e
                            )
                        }
                    )
                }
            }
            .timeout(java.time.Duration.ofSeconds(10))
            .onErrorResume { error ->
                
                when (error) {
                    is java.util.concurrent.TimeoutException,
                    is org.springframework.web.reactive.function.client.WebClientException,
                    is java.net.ConnectException -> {
                        logger.debug("Python API 서버 연결 실패 (조용히 처리): $baseUrl (symbol: $symbol)")
                        Mono.just(
                            StockData(
                                symbol = symbol,
                                currentPrice = 0.0,
                                volume = 0L,
                                changePercent = 0.0,
                                timestamp = LocalDateTime.now(),
                                confidenceScore = 0.0
                            )
                        )
                    }
                    else -> {
                        logger.debug("Python API 오류 (더미 데이터 반환): $symbol - ${error.message}")
                        Mono.just(
                            StockData(
                                symbol = symbol,
                                currentPrice = 0.0,
                                volume = 0L,
                                changePercent = 0.0,
                                timestamp = LocalDateTime.now(),
                                confidenceScore = 0.0
                            )
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
        val url = "$baseUrl/api/analysis/$symbol"
        logger.debug("분석 데이터 요청 중: symbol=$symbol, url=$url")
        
        webClient.get()
            .uri("/api/analysis/{symbol}", symbol)
            .retrieve()
            .onStatus({ status -> status.is5xxServerError || status.is4xxClientError }, { response ->
                logger.debug("Python API 서버 HTTP 오류: ${response.statusCode()} (symbol: $symbol, url: $url)")
                response.bodyToMono(String::class.java)
                    .defaultIfEmpty("")
                    .flatMap { body ->
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류 (${response.statusCode()}): ${if (body.isNotEmpty()) body else "서버가 오류를 반환했습니다"}"
                        ))
                    }
            })
            .bodyToMono(Map::class.java)
            .doOnNext { data ->
                logger.debug("Python API로부터 분석 응답 수신: symbol=$symbol, Response keys: ${data.keys}")
            }
            .map(mapToTechnicalAnalysis)
            .timeout(java.time.Duration.ofSeconds(15))
            .onErrorResume { error ->
                
                when (error) {
                    is java.util.concurrent.TimeoutException,
                    is org.springframework.web.reactive.function.client.WebClientException,
                    is java.net.ConnectException -> {
                        logger.debug("Python API 서버 연결 실패 (조용히 처리): $baseUrl (symbol: $symbol)")
                        Mono.just(
                            TechnicalAnalysis(
                                symbol = symbol,
                                currentPrice = 0.0,
                                volume = 0L,
                                changePercent = 0.0,
                                trend = "neutral",
                                trendStrength = 0.0,
                                signals = TradingSignals(
                                    signal = "hold",
                                    confidence = 0.0,
                                    rsi = null,
                                    macd = null,
                                    macdSignal = null
                                ),
                                anomalies = emptyList(),
                                timestamp = LocalDateTime.now()
                            )
                        )
                    }
                    else -> {
                        logger.debug("Python API 오류 (더미 데이터 반환): $symbol - ${error.message}")
                        Mono.just(
                            TechnicalAnalysis(
                                symbol = symbol,
                                currentPrice = 0.0,
                                volume = 0L,
                                changePercent = 0.0,
                                trend = "neutral",
                                trendStrength = 0.0,
                                signals = TradingSignals(
                                    signal = "hold",
                                    confidence = 0.0,
                                    rsi = null,
                                    macd = null,
                                    macdSignal = null
                                ),
                                anomalies = emptyList(),
                                timestamp = LocalDateTime.now()
                            )
                        )
                    }
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
            .onErrorResume { error ->
                
                logger.debug("Python API 서버 연결 실패 (조용히 처리): $baseUrl - getAllAnalysis")
                Flux.empty()
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
            .onErrorResume { error ->
               
                logger.debug("Python API 서버 연결 실패 (조용히 처리): $baseUrl (symbol: $symbol, days: $days)")
                Mono.just(
                    HistoricalData(
                        symbol = symbol,
                        data = emptyList(),
                        period = days
                    )
                )
            }
    }

    val getSymbols: () -> Mono<List<String>> = {
        webClient.get()
            .uri("/api/symbols")
            .retrieve()
            .bodyToMono(Map::class.java)
            .map { data -> data["symbols"] as List<String> }
            .timeout(java.time.Duration.ofSeconds(10))
            .onErrorResume { error ->
               
                logger.debug("Python API 서버 연결 실패 (조용히 처리): $baseUrl - getSymbols")
                Mono.just(listOf("AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA"))
            }
    }

    fun sendEmail(toEmail: String, subject: String, content: String): Mono<Boolean> {
        return webClient.post()
            .uri { uriBuilder ->
                uriBuilder.path("/api/notifications/email")
                    .queryParam("to_email", toEmail)
                    .queryParam("subject", subject)
                    .queryParam("body", content)
                    .build()
            }
            .retrieve()
            .bodyToMono(Map::class.java)
            .map { response ->
                response["success"] as? Boolean ?: false
            }
            .onErrorResume { error ->
                logger.error("이메일 발송 실패: ${error.message}", error)
                Mono.just(false)
            }
    }

    fun sendSms(toPhone: String, message: String): Mono<Boolean> {
        return webClient.post()
            .uri { uriBuilder ->
                uriBuilder.path("/api/notifications/sms")
                    .queryParam("to_phone", toPhone)
                    .queryParam("message", message)
                    .build()
            }
            .retrieve()
            .bodyToMono(Map::class.java)
            .map { response ->
                response["success"] as? Boolean ?: false
            }
            .onErrorResume { error ->
                logger.error("문자 발송 실패: ${error.message}", error)
                Mono.just(false)
            }
    }

    fun getFromPhone(): Mono<String> {
        return webClient.get()
            .uri("/api/notifications/sms-config")
            .retrieve()
            .bodyToMono(Map::class.java)
            .map { response ->
                (response["fromPhone"] as? String) ?: ""
            }
            .onErrorResume { error ->
                logger.error("발신번호 조회 실패: ${error.message}", error)
                Mono.just("")
            }
    }

    private val mapToNews: (Map<*, *>) -> News = { newsMap ->
        News(
            title = newsMap["title"] as? String ?: "",
            description = newsMap["description"] as? String,
            url = newsMap["url"] as? String ?: "",
            source = newsMap["source"] as? String,
            publishedAt = newsMap["published_at"] as? String,
            symbol = newsMap["symbol"] as? String ?: "",
            provider = newsMap["provider"] as? String ?: "",
            sentiment = (newsMap["sentiment"] as? Number)?.toDouble(),
            titleKo = newsMap["title_ko"] as? String,
            descriptionKo = newsMap["description_ko"] as? String,
            contentKo = newsMap["content_ko"] as? String,
            content = newsMap["content"] as? String
        )
    }

    fun getStockNews(symbol: String, includeKorean: Boolean = false, autoTranslate: Boolean = true): Mono<List<News>> {
        return webClient.get()
            .uri { uriBuilder ->
                uriBuilder.path("/api/news/{symbol}")
                    .queryParam("include_korean", includeKorean)
                    .queryParam("auto_translate", autoTranslate)
                    .build(symbol)
            }
            .retrieve()
            .bodyToFlux(Map::class.java)
            .map(mapToNews)
            .collectList()
            .timeout(java.time.Duration.ofSeconds(15))
            .onErrorResume { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException,
                    is org.springframework.web.reactive.function.client.WebClientException,
                    is java.net.ConnectException -> {
                        logger.debug("Python API 서버 연결 실패 (조용히 처리): $baseUrl (symbol: $symbol)")
                        Mono.just(emptyList())
                    }
                    else -> {
                        logger.debug("뉴스 조회 실패 (조용히 처리): $symbol - ${error.message}")
                        Mono.just(emptyList())
                    }
                }
            }
    }
    
    fun getNewsByUrl(url: String): Mono<News> {
        return webClient.get()
            .uri { uriBuilder ->
                uriBuilder.path("/api/news/detail")
                    .queryParam("url", url)
                    .build()
            }
            .retrieve()
            .onStatus({ status -> status.is4xxClientError || status.is5xxServerError }, { response ->
                logger.debug("Python API 서버 HTTP 오류: ${response.statusCode()} (url: $url)")
                response.bodyToMono(String::class.java)
                    .defaultIfEmpty("")
                    .flatMap { body ->
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류 (${response.statusCode()}): ${if (body.isNotEmpty()) body else "서버가 오류를 반환했습니다"}"
                        ))
                    }
            })
            .bodyToMono(Map::class.java)
            .map(mapToNews)
            .timeout(java.time.Duration.ofSeconds(10))
            .onErrorResume { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException,
                    is org.springframework.web.reactive.function.client.WebClientException,
                    is java.net.ConnectException -> {
                        logger.debug("Python API 서버 연결 실패 (조용히 처리): $baseUrl (url: $url)")
                        Mono.error(error)
                    }
                    else -> {
                        logger.debug("뉴스 상세 조회 실패 (조용히 처리): $url - ${error.message}")
                        Mono.error(error)
                    }
                }
            }
    }

    fun searchNews(query: String, language: String = "en", maxResults: Int = 20): Mono<List<News>> {
        return webClient.get()
            .uri { uriBuilder ->
                uriBuilder.path("/api/news")
                    .queryParam("query", query)
                    .queryParam("language", language)
                    .queryParam("max_results", maxResults)
                    .build()
            }
            .retrieve()
            .bodyToFlux(Map::class.java)
            .map(mapToNews)
            .collectList()
            .timeout(java.time.Duration.ofSeconds(15))
            .onErrorResume { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException,
                    is org.springframework.web.reactive.function.client.WebClientException,
                    is java.net.ConnectException -> {
                        logger.debug("Python API 서버 연결 실패 (조용히 처리): $baseUrl (query: $query)")
                        Mono.just(emptyList())
                    }
                    else -> {
                        logger.debug("뉴스 검색 실패 (조용히 처리): $query - ${error.message}")
                        Mono.just(emptyList())
                    }
                }
            }
    }

    fun getMultipleStockNews(symbols: List<String>, includeKorean: Boolean = false): Mono<Map<String, List<News>>> {
        val symbolsParam = symbols.joinToString(",")
        return webClient.get()
            .uri { uriBuilder ->
                uriBuilder.path("/api/news/multiple")
                    .queryParam("symbols", symbolsParam)
                    .queryParam("include_korean", includeKorean)
                    .build()
            }
            .retrieve()
            .bodyToMono(Map::class.java)
            .map { response ->
                (response as Map<String, *>).mapValues { entry ->
                    (entry.value as? List<*>)?.map { it as Map<*, *> }?.map(mapToNews) ?: emptyList()
                }
            }
            .timeout(java.time.Duration.ofSeconds(20))
            .onErrorResume { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException,
                    is org.springframework.web.reactive.function.client.WebClientException,
                    is java.net.ConnectException -> {
                        logger.debug("Python API 서버 연결 실패 (조용히 처리): $baseUrl (symbols: $symbolsParam)")
                        Mono.just(emptyMap())
                    }
                    else -> {
                        logger.debug("다중 종목 뉴스 조회 실패 (조용히 처리): $symbolsParam - ${error.message}")
                        Mono.just(emptyMap())
                    }
                }
            }
    }
}