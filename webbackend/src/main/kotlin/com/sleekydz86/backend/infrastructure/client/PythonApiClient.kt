package com.sleekydz86.backend.infrastructure.client

import com.sleekydz86.backend.domain.model.*
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Component
import org.springframework.http.client.reactive.ReactorClientHttpConnector
import org.springframework.web.reactive.function.client.WebClient
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.netty.http.client.HttpClient
import reactor.util.retry.Retry
import java.time.Duration
import java.time.LocalDateTime

@Component
class PythonApiClient(
    @Value("\${python.api.base-url:http://localhost:9000}")
    private val baseUrl: String
) {
    private val logger = org.slf4j.LoggerFactory.getLogger(PythonApiClient::class.java)
    
    private val httpClient = HttpClient.create()
        .responseTimeout(Duration.ofSeconds(60))
        .doOnConnected { connection ->
            connection.addHandlerLast(io.netty.handler.timeout.ReadTimeoutHandler(60))
            connection.addHandlerLast(io.netty.handler.timeout.WriteTimeoutHandler(60))
        }
    
    private val webClient = WebClient.builder()
        .baseUrl(baseUrl)
        .clientConnector(ReactorClientHttpConnector(httpClient))
        .build()
    
    fun checkHealth(): Mono<Boolean> {
        return webClient.get()
            .uri("/api/health")
            .retrieve()
            .bodyToMono(Map::class.java)
            .map { response ->
                val status = response["status"] as? String
                status == "healthy" || status == "initializing"
            }
            .timeout(Duration.ofSeconds(5))
            .onErrorResume { error ->
                logger.warn("Python API 헬스 체크 실패: baseUrl={}, error={}", baseUrl, error.message)
                Mono.just(false)
            }
    }

    private val mapToStockData: (Map<*, *>) -> StockData = { data ->
        try {
            val symbol = (data["symbol"] as? String) ?: throw IllegalArgumentException("종목 필드가 없거나 잘못되었습니다: $data")
            
            val currentPrice = try {
                val priceValue = (data["currentPrice"] as? Number) ?: (data["price"] as? Number)
                if (priceValue == null) {
                    throw IllegalArgumentException("가격 필드가 없거나 잘못되었습니다")
                }
                priceValue.toDouble()
            } catch (e: Exception) {
                throw com.sleekydz86.backend.global.exception.DataProcessingException("가격 데이터 형식이 잘못되었습니다: ${e.message}", e)
            }
            
            val volume = try {
                val volumeValue = data["volume"]
                when (volumeValue) {
                    is Number -> volumeValue.toLong()
                    null -> 0L
                    else -> (volumeValue as? Number)?.toLong() ?: 0L
                }
            } catch (e: Exception) {
                throw com.sleekydz86.backend.global.exception.DataProcessingException("거래량 데이터 형식이 잘못되었습니다: ${e.message}", e)
            }
            
            val changePercent = try {
                val changePercentValue = (data["changePercent"] as? Number) ?: (data["change_percent"] as? Number)
                if (changePercentValue == null) {
                    throw IllegalArgumentException("변동률 필드가 없거나 잘못되었습니다")
                }
                changePercentValue.toDouble()
            } catch (e: Exception) {
                throw com.sleekydz86.backend.global.exception.DataProcessingException("변동률 데이터 형식이 잘못되었습니다: ${e.message}", e)
            }
            
            val confidenceScore = (data["confidenceScore"] as? Number ?: data["confidence_score"] as? Number)?.toDouble()
            
            StockData(
                symbol = symbol,
                currentPrice = currentPrice,
                volume = volume,
                changePercent = changePercent,
                timestamp = LocalDateTime.now(),
                confidenceScore = confidenceScore
            )
        } catch (e: Exception) {
            if (e is com.sleekydz86.backend.global.exception.DataProcessingException) {
                throw e
            }
            throw com.sleekydz86.backend.global.exception.DataProcessingException(
                "Python API에서 주식 데이터 파싱 실패: ${e.message}. 응답 데이터: $data",
                e
            )
        }
    }

    val getRealtimeData: (String) -> Mono<StockData> = { symbol ->
        webClient.get()
            .uri("/api/realtime/{symbol}", symbol)
            .retrieve()
            .onStatus({ status -> status.is5xxServerError || status.is4xxClientError }, { response ->
                response.bodyToMono(String::class.java)
                    .defaultIfEmpty("")
                    .flatMap { body ->
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류 (${response.statusCode()}): ${if (body.isNotEmpty()) body else "서버가 오류를 반환했습니다"}"
                        ))
                    }
            })
            .bodyToMono(Map::class.java)
            .flatMap { data ->
                try {
                    val stockData = mapToStockData(data)
                    Mono.just(stockData)
                } catch (e: Exception) {
                    Mono.error(
                        when (e) {
                            is com.sleekydz86.backend.global.exception.DataProcessingException -> e
                            else -> com.sleekydz86.backend.global.exception.DataProcessingException(
                                "Python API 응답에서 주식 데이터 파싱 실패: ${e.message}",
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
        webClient.get()
            .uri("/api/analysis/{symbol}", symbol)
            .retrieve()
            .onStatus({ status -> status.is5xxServerError || status.is4xxClientError }, { response ->
                response.bodyToMono(String::class.java)
                    .defaultIfEmpty("")
                    .flatMap { body ->
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류 (${response.statusCode()}): ${if (body.isNotEmpty()) body else "서버가 오류를 반환했습니다"}"
                        ))
                    }
            })
            .bodyToMono(Map::class.java)
            .map(mapToTechnicalAnalysis)
            .timeout(java.time.Duration.ofSeconds(15))
            .onErrorResume { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException,
                    is org.springframework.web.reactive.function.client.WebClientException,
                    is java.net.ConnectException -> {
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
            .onStatus({ status -> status.is4xxClientError || status.is5xxServerError }, { response ->
                response.bodyToMono(String::class.java)
                    .defaultIfEmpty("")
                    .flatMap { body ->
                        val statusCode = response.statusCode().value()
                        logger.warn("Python API 오류 ({}): {} 종목: {}", statusCode, body, symbol)
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 오류 ($statusCode): ${if (body.isNotEmpty()) body else "서버가 오류를 반환했습니다"}"
                        ))
                    }
            })
            .bodyToFlux(Map::class.java)
            .map(mapToNews)
            .collectList()
            .retryWhen(
                Retry.backoff(2, Duration.ofSeconds(1))
                    .filter { error ->
                        val cause = error.cause
                        when {
                            error is reactor.netty.http.client.PrematureCloseException -> true
                            error is org.springframework.web.reactive.function.client.WebClientRequestException -> {
                                cause is reactor.netty.http.client.PrematureCloseException || 
                                cause is java.net.ConnectException ||
                                error.message?.contains("Connection prematurely closed") == true ||
                                error.message?.contains("Connection refused") == true
                            }
                            error is org.springframework.web.reactive.function.client.WebClientException -> {
                                cause is reactor.netty.http.client.PrematureCloseException ||
                                cause is java.net.ConnectException
                            }
                            error is java.net.ConnectException -> true
                            error is java.util.concurrent.TimeoutException -> true
                            else -> false
                        }
                    }
                    .doBeforeRetry { retrySignal ->
                        val failure = retrySignal.failure()
                        logger.info("뉴스 조회 재시도: symbol={}, 시도 횟수={}, 오류={}, 원인={}", 
                            symbol,
                            retrySignal.totalRetries() + 1, 
                            failure.message,
                            failure.cause?.message ?: "없음")
                    }
            )
            .timeout(java.time.Duration.ofSeconds(20))
            .doOnError { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException -> {
                        logger.warn("뉴스 조회 타임아웃: symbol={}, timeout=25초, baseUrl={}", symbol, baseUrl)
                    }
                    is java.net.ConnectException -> {
                        logger.warn("Python API 연결 실패: symbol={}, baseUrl={}. Python API 서버가 실행 중인지 확인하세요.", symbol, baseUrl)
                    }
                    is reactor.netty.http.client.PrematureCloseException -> {
                        logger.warn("Python API 연결 조기 종료: symbol={}, baseUrl={}", symbol, baseUrl)
                    }
                    is org.springframework.web.reactive.function.client.WebClientRequestException -> {
                        val cause = error.cause
                        when {
                            cause is java.net.ConnectException -> {
                                logger.warn("Python API 연결 실패: symbol={}, baseUrl={}. Python API 서버가 실행 중인지 확인하세요. (시작 명령: python start_python_api.py 또는 python api_server_enhanced.py)", symbol, baseUrl)
                            }
                            else -> {
                                logger.warn("WebClient 오류: symbol={}, error={}", symbol, error.message)
                            }
                        }
                    }
                    else -> {
                        logger.warn("뉴스 조회 오류: symbol={}, error={}", symbol, error.message)
                    }
                }
            }
            .onErrorResume { error ->
                when {
                    error.message?.contains("Retries exhausted") == true || 
                    error.javaClass.simpleName == "RetryExhaustedException" -> {
                        val cause = error.cause
                        when {
                            cause is java.net.ConnectException -> {
                                logger.warn("종목 {} 뉴스 조회 실패: 재시도 모두 실패, {}에 연결할 수 없습니다. 빈 목록을 반환합니다. Python API 서버를 시작하세요: python start_python_api.py", symbol, baseUrl)
                            }
                            cause is org.springframework.web.reactive.function.client.WebClientRequestException -> {
                                val innerCause = cause.cause
                                if (innerCause is java.net.ConnectException) {
                                    logger.warn("종목 {} 뉴스 조회 실패: 재시도 모두 실패, {}에 연결할 수 없습니다. 빈 목록을 반환합니다. Python API 서버를 시작하세요: python start_python_api.py", symbol, baseUrl)
                                } else {
                                    logger.warn("종목 {} 뉴스 조회 실패: 재시도 모두 실패, {}. 빈 목록을 반환합니다.", symbol, cause.message)
                                }
                            }
                            else -> {
                                logger.warn("종목 {} 뉴스 조회 실패: 재시도 모두 실패, {}. 빈 목록을 반환합니다.", symbol, error.message)
                            }
                        }
                        Mono.just(emptyList())
                    }
                    error is java.net.ConnectException -> {
                        logger.warn("종목 {} 뉴스 조회 실패: {}에 연결할 수 없습니다. 빈 목록을 반환합니다. Python API 서버를 시작하세요: python start_python_api.py", symbol, baseUrl)
                        Mono.just(emptyList())
                    }
                    error is org.springframework.web.reactive.function.client.WebClientRequestException -> {
                        val cause = error.cause
                        if (cause is java.net.ConnectException) {
                            logger.warn("종목 {} 뉴스 조회 실패: {}에 연결할 수 없습니다. 빈 목록을 반환합니다. Python API 서버를 시작하세요: python start_python_api.py", symbol, baseUrl)
                        } else {
                            logger.warn("종목 {} 뉴스 조회 실패: {}. 빈 목록을 반환합니다.", symbol, error.message)
                        }
                        Mono.just(emptyList())
                    }
                    error is java.util.concurrent.TimeoutException -> {
                        logger.warn("종목 {} 뉴스 조회 타임아웃: 25초 후 타임아웃. 빈 목록을 반환합니다.", symbol)
                        Mono.just(emptyList())
                    }
                    else -> {
                        logger.warn("종목 {} 뉴스 조회 실패: {}. 빈 목록을 반환합니다.", symbol, error.message)
                        Mono.just(emptyList())
                    }
                }
            }
    }
    
    fun getNewsByUrl(url: String): Mono<News> {
        val logger = org.slf4j.LoggerFactory.getLogger(PythonApiClient::class.java)
        logger.info("뉴스 상세 조회 요청: url={}", url.take(100))
        
        return webClient.get()
            .uri { uriBuilder ->
                uriBuilder.path("/api/news/detail")
                    .queryParam("url", url)
                    .build()
            }
            .retrieve()
            .onStatus({ status -> status.is4xxClientError || status.is5xxServerError }, { response ->
                response.bodyToMono(String::class.java)
                    .defaultIfEmpty("")
                    .flatMap { body ->
                        val errorMsg = "Python API 서버 오류 (${response.statusCode()}): ${if (body.isNotEmpty()) body else "서버가 오류를 반환했습니다"}"
                        logger.warn("Python API 오류 응답: status={}, body={}, url={}", response.statusCode(), body, url.take(100))
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(errorMsg))
                    }
            })
            .bodyToMono(Any::class.java)
            .flatMap { response ->
                try {
                    val newsMap = when (response) {
                        is Map<*, *> -> response as Map<String, Any>
                        is List<*> -> {
                            if (response.isNotEmpty()) {
                                val firstItem = response[0]
                                if (firstItem is Map<*, *>) {
                                    firstItem as Map<String, Any>
                                } else {
                                    throw IllegalArgumentException("배열의 첫 번째 요소가 Map이 아닙니다")
                                }
                            } else {
                                throw IllegalArgumentException("빈 배열이 반환되었습니다")
                            }
                        }
                        else -> throw IllegalArgumentException("예상치 못한 응답 형식: ${response.javaClass}")
                    }
                    Mono.just(mapToNews(newsMap))
                } catch (e: Exception) {
                    logger.error("뉴스 상세 응답 파싱 오류: url={}, error={}, responseType={}", url.take(100), e.message, response?.javaClass?.simpleName)
                    Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                        "뉴스 상세 응답 파싱 오류: ${e.message}", e
                    ))
                }
            }
            .retryWhen(
                Retry.backoff(3, Duration.ofSeconds(2))
                    .filter { error ->
                        val cause = error.cause
                        when {
                            error is reactor.netty.http.client.PrematureCloseException -> true
                            error is org.springframework.web.reactive.function.client.WebClientRequestException -> {
                                cause is reactor.netty.http.client.PrematureCloseException || 
                                cause is java.net.ConnectException ||
                                error.message?.contains("Connection prematurely closed") == true
                            }
                            error is org.springframework.web.reactive.function.client.WebClientException -> {
                                cause is reactor.netty.http.client.PrematureCloseException ||
                                cause is java.net.ConnectException
                            }
                            error is java.net.ConnectException -> true
                            error is java.util.concurrent.TimeoutException -> true
                            else -> false
                        }
                    }
                    .doBeforeRetry { retrySignal ->
                        val failure = retrySignal.failure()
                        logger.info("뉴스 상세 조회 재시도: 시도 횟수={}, 오류={}, 원인={}, url={}", 
                            retrySignal.totalRetries() + 1, 
                            failure.message,
                            failure.cause?.message ?: "없음",
                            url.take(100))
                    }
            )
            .timeout(Duration.ofSeconds(45))
            .doOnError { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException -> {
                        logger.warn("뉴스 상세 조회 타임아웃: url={}, timeout=45초", url.take(100))
                    }
                    is java.net.ConnectException -> {
                        logger.warn("Python API 연결 실패: url={}, baseUrl={}", url.take(100), baseUrl)
                    }
                    is reactor.netty.http.client.PrematureCloseException -> {
                        logger.warn("Python API 연결 조기 종료: url={}, baseUrl={}", url.take(100), baseUrl)
                    }
                    is org.springframework.web.reactive.function.client.WebClientException -> {
                        logger.warn("WebClient 오류: url={}, error={}", url.take(100), error.message)
                    }
                    else -> {
                        logger.warn("뉴스 상세 조회 오류: url={}, error={}", url.take(100), error.message)
                    }
                }
            }
            .onErrorResume { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException -> {
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 요청 시간 초과 (45초). 서버가 응답하지 않습니다.", error
                        ))
                    }
                    is java.net.ConnectException -> {
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요. (baseUrl: $baseUrl)", error
                        ))
                    }
                    is reactor.netty.http.client.PrematureCloseException -> {
                        Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                            "Python API 서버 연결이 조기에 종료되었습니다. 서버 상태를 확인해주세요. (baseUrl: $baseUrl)", error
                        ))
                    }
                    is org.springframework.web.reactive.function.client.WebClientRequestException -> {
                        val cause = error.cause
                        when {
                            cause is reactor.netty.http.client.PrematureCloseException -> {
                                Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                                    "Python API 서버 연결이 조기에 종료되었습니다. 서버 상태를 확인해주세요. (baseUrl: $baseUrl)", error
                                ))
                            }
                            cause is java.net.ConnectException -> {
                                Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                                    "Python API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요. (baseUrl: $baseUrl)", error
                                ))
                            }
                            else -> {
                                Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                                    "Python API 통신 오류: ${error.message}", error
                                ))
                            }
                        }
                    }
                    is org.springframework.web.reactive.function.client.WebClientException -> {
                        val cause = error.cause
                        when {
                            cause is reactor.netty.http.client.PrematureCloseException -> {
                                Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                                    "Python API 서버 연결이 조기에 종료되었습니다. 서버 상태를 확인해주세요. (baseUrl: $baseUrl)", error
                                ))
                            }
                            else -> {
                                Mono.error(com.sleekydz86.backend.global.exception.ExternalApiException(
                                    "Python API 통신 오류: ${error.message}", error
                                ))
                            }
                        }
                    }
                    else -> {
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
                        Mono.just(emptyList())
                    }
                    else -> {
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
            .retryWhen(
                Retry.backoff(2, Duration.ofSeconds(1))
                    .filter { error ->
                        val cause = error.cause
                        when {
                            error is reactor.netty.http.client.PrematureCloseException -> true
                            error is org.springframework.web.reactive.function.client.WebClientRequestException -> {
                                cause is reactor.netty.http.client.PrematureCloseException || 
                                cause is java.net.ConnectException ||
                                error.message?.contains("Connection prematurely closed") == true ||
                                error.message?.contains("Connection refused") == true
                            }
                            error is org.springframework.web.reactive.function.client.WebClientException -> {
                                cause is reactor.netty.http.client.PrematureCloseException ||
                                cause is java.net.ConnectException
                            }
                            error is java.net.ConnectException -> true
                            error is java.util.concurrent.TimeoutException -> true
                            else -> false
                        }
                    }
                    .doBeforeRetry { retrySignal ->
                        val failure = retrySignal.failure()
                        logger.info("다중 종목 뉴스 조회 재시도: symbols={}, 시도 횟수={}, 오류={}, 원인={}", 
                            symbolsParam,
                            retrySignal.totalRetries() + 1, 
                            failure.message,
                            failure.cause?.message ?: "없음")
                    }
            )
            .timeout(java.time.Duration.ofSeconds(20))
            .doOnError { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException -> {
                        logger.warn("다중 종목 뉴스 조회 타임아웃: symbols={}, timeout=20초, baseUrl={}", symbolsParam, baseUrl)
                    }
                    is java.net.ConnectException -> {
                        logger.warn("Python API 연결 실패: symbols={}, baseUrl={}. Python API 서버가 실행 중인지 확인하세요.", symbolsParam, baseUrl)
                    }
                    is org.springframework.web.reactive.function.client.WebClientRequestException -> {
                        val cause = error.cause
                        if (cause is java.net.ConnectException) {
                            logger.warn("Python API 연결 실패: symbols={}, baseUrl={}. Python API 서버가 실행 중인지 확인하세요. (시작 명령: python start_python_api.py)", symbolsParam, baseUrl)
                        }
                    }
                }
            }
            .onErrorResume { error ->
                when {
                    error.message?.contains("Retries exhausted") == true || 
                    error.javaClass.simpleName == "RetryExhaustedException" -> {
                        val cause = error.cause
                        when {
                            cause is java.net.ConnectException -> {
                                logger.warn("다중 종목 뉴스 조회 실패: 재시도 모두 실패, 종목={}, {}에 연결할 수 없습니다. 빈 맵을 반환합니다. Python API 서버를 시작하세요: python start_python_api.py", symbolsParam, baseUrl)
                            }
                            cause is org.springframework.web.reactive.function.client.WebClientRequestException -> {
                                val innerCause = cause.cause
                                if (innerCause is java.net.ConnectException) {
                                    logger.warn("다중 종목 뉴스 조회 실패: 재시도 모두 실패, 종목={}, {}에 연결할 수 없습니다. 빈 맵을 반환합니다. Python API 서버를 시작하세요: python start_python_api.py", symbolsParam, baseUrl)
                                } else {
                                    logger.warn("다중 종목 뉴스 조회 실패: 재시도 모두 실패, 종목={}, {}. 빈 맵을 반환합니다.", symbolsParam, cause.message)
                                }
                            }
                            else -> {
                                logger.warn("다중 종목 뉴스 조회 실패: 재시도 모두 실패, 종목={}, {}. 빈 맵을 반환합니다.", symbolsParam, error.message)
                            }
                        }
                        Mono.just(emptyMap())
                    }
                    error is java.util.concurrent.TimeoutException -> {
                        logger.warn("다중 종목 뉴스 조회 실패: 종목={}, 타임아웃. 빈 맵을 반환합니다.", symbolsParam)
                        Mono.just(emptyMap())
                    }
                    error is org.springframework.web.reactive.function.client.WebClientException -> {
                        logger.warn("다중 종목 뉴스 조회 실패: 종목={}, 오류={}. 빈 맵을 반환합니다.", symbolsParam, error.message)
                        Mono.just(emptyMap())
                    }
                    error is java.net.ConnectException -> {
                        logger.warn("다중 종목 뉴스 조회 실패: 종목={}, {}에 연결할 수 없습니다. 빈 맵을 반환합니다. Python API 서버를 시작하세요: python start_python_api.py", symbolsParam, baseUrl)
                        Mono.just(emptyMap())
                    }
                    error is org.springframework.web.reactive.function.client.WebClientRequestException -> {
                        val cause = error.cause
                        if (cause is java.net.ConnectException) {
                            logger.warn("다중 종목 뉴스 조회 실패: 종목={}, {}에 연결할 수 없습니다. 빈 맵을 반환합니다. Python API 서버를 시작하세요: python start_python_api.py", symbolsParam, baseUrl)
                        } else {
                            logger.warn("다중 종목 뉴스 조회 실패: 종목={}, 오류={}. 빈 맵을 반환합니다.", symbolsParam, error.message)
                        }
                        Mono.just(emptyMap())
                    }
                    else -> {
                        logger.warn("다중 종목 뉴스 조회 실패: 종목={}, 오류={}. 빈 맵을 반환합니다.", symbolsParam, error.message)
                        Mono.just(emptyMap())
                    }
                }
            }
    }

    fun getSectorsAnalysis(): Mono<List<Map<String, Any>>> {
        return webClient.get()
            .uri("/api/sectors")
            .retrieve()
            .bodyToFlux(Map::class.java)
            .map { it as Map<String, Any> }
            .collectList()
            .timeout(java.time.Duration.ofSeconds(30))
            .onErrorResume { error ->
                logger.warn("섹터별 분석 조회 실패: {}", error.message)
                Mono.just(emptyList())
            }
    }
}