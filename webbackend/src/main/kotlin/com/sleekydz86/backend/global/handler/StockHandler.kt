package com.sleekydz86.backend.global.handler

import com.sleekydz86.backend.domain.model.TechnicalAnalysis
import com.sleekydz86.backend.domain.model.TradingSignals
import com.sleekydz86.backend.domain.model.Anomaly
import java.time.LocalDateTime
import com.sleekydz86.backend.domain.service.StockAnalysisService
import com.sleekydz86.backend.global.exception.DataProcessingException
import com.sleekydz86.backend.global.exception.ExternalApiException
import com.sleekydz86.backend.global.exception.InvalidSymbolException
import com.sleekydz86.backend.global.exception.ReactiveExceptionHandler
import com.sleekydz86.backend.global.exception.StockNotFoundException
import com.sleekydz86.backend.global.exception.WebSocketException
import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.reactive.function.server.ServerRequest
import org.springframework.web.reactive.function.server.ServerResponse
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration
import org.slf4j.LoggerFactory

@Component
class StockHandler(
    private val stockAnalysisService: StockAnalysisService
) {
    private val logger = LoggerFactory.getLogger(StockHandler::class.java)

    fun getAvailableSymbols(request: ServerRequest): Mono<ServerResponse> =
        stockAnalysisService.getAvailableSymbols()
            .flatMap { symbols ->
                ServerResponse.ok()
                    .bodyValue(mapOf("symbols" to symbols))
            }
            .timeout(Duration.ofSeconds(10))
            .onErrorResume { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException ->
                        ReactiveExceptionHandler.handleExternalApiError(request, error)
                    is ExternalApiException ->
                        ReactiveExceptionHandler.handleExternalApiError(request, error)
                    is DataProcessingException ->
                        ReactiveExceptionHandler.handleDataProcessingError(request, error)
                    else ->
                        ReactiveExceptionHandler.handleGenericError(request, error)
                }
            }

    fun getRealtimeData(request: ServerRequest): Mono<ServerResponse> {
        val symbol = try {
            request.pathVariable("symbol")
        } catch (e: Exception) {
            logger.error("경로에서 심볼 추출 예외 발생", e)
            return ReactiveExceptionHandler.handleInvalidSymbol(
                request, 
                InvalidSymbolException("Invalid path parameter")
            )
        }
        
        logger.debug("실시간 데이터 조회 중: symbol=$symbol")
        
        if (symbol.isBlank() || !symbol.matches(Regex("[A-Z]{1,5}"))) {
            return ReactiveExceptionHandler.handleInvalidSymbol(
                request, 
                InvalidSymbolException("Invalid stock symbol format")
            )
        }

        return stockAnalysisService.getRealtimeStockData(symbol)
            .flatMap { data ->
                logger.debug("데이터 조회 완료: symbol=$symbol")
                ServerResponse.ok().bodyValue(data)
            }
            .timeout(Duration.ofSeconds(15))
            .onErrorResume { error ->
                
                logger.debug("실시간 데이터 조회 오류: symbol=$symbol - ${error.message}")
                when (error) {
                    is StockNotFoundException -> {
                        ReactiveExceptionHandler.handleStockNotFound(request, error)
                    }
                    is InvalidSymbolException -> {
                        ReactiveExceptionHandler.handleInvalidSymbol(request, error)
                    }
                    is java.util.concurrent.TimeoutException,
                    is ExternalApiException,
                    is org.springframework.web.reactive.function.client.WebClientException -> {
                       
                        logger.debug("Python API 연결 실패 (조용히 처리): $symbol")
                        ServerResponse.ok().bodyValue(
                            com.sleekydz86.backend.domain.model.StockData(
                                symbol = symbol,
                                currentPrice = 0.0,
                                volume = 0L,
                                changePercent = 0.0,
                                timestamp = java.time.LocalDateTime.now(),
                                confidenceScore = 0.0
                            )
                        )
                    }
                    is DataProcessingException -> {
                        logger.debug("데이터 처리 예외 발생: symbol=$symbol", error)
                        ReactiveExceptionHandler.handleDataProcessingError(request, error)
                    }
                    else -> {
                        logger.debug("예상치 못한 오류 타입: ${error.javaClass.name}, 메시지: ${error.message}")
                        ReactiveExceptionHandler.handleGenericError(request, error)
                    }
                }
            }
    }

    fun getAllRealtimeData(request: ServerRequest): Mono<ServerResponse> =
        stockAnalysisService.getAllRealtimeStockData()
            .collectList()
            .flatMap { data ->
                ServerResponse.ok().bodyValue(data)
            }
            .timeout(Duration.ofSeconds(30))
            .onErrorResume { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException ->
                        ReactiveExceptionHandler.handleExternalApiError(request, error)
                    is ExternalApiException ->
                        ReactiveExceptionHandler.handleExternalApiError(request, error)
                    is DataProcessingException ->
                        ReactiveExceptionHandler.handleDataProcessingError(request, error)
                    else ->
                        ReactiveExceptionHandler.handleGenericError(request, error)
                }
            }

    fun getAnalysis(request: ServerRequest): Mono<ServerResponse> =
        try {
            val symbol = request.pathVariable("symbol")
            if (symbol.isBlank() || !symbol.matches(Regex("[A-Z]{1,5}"))) {
                throw InvalidSymbolException("Invalid stock symbol format")
            }

            stockAnalysisService.getStockAnalysis(symbol)
                .flatMap { analysis ->
                    ServerResponse.ok().bodyValue(analysis)
                }
                .timeout(Duration.ofSeconds(20))
                .onErrorResume { error ->
                    
                    when (error) {
                        is StockNotFoundException ->
                            ReactiveExceptionHandler.handleStockNotFound(request, error)
                        is InvalidSymbolException ->
                            ReactiveExceptionHandler.handleInvalidSymbol(request, error)
                        is java.util.concurrent.TimeoutException,
                        is ExternalApiException,
                        is org.springframework.web.reactive.function.client.WebClientException -> {
                            
                            logger.debug("Python API 연결 실패 (조용히 처리): $symbol - getAnalysis")
                            ServerResponse.ok().bodyValue(
                                com.sleekydz86.backend.domain.model.TechnicalAnalysis(
                                    symbol = symbol,
                                    currentPrice = 0.0,
                                    volume = 0L,
                                    changePercent = 0.0,
                                    trend = "neutral",
                                    trendStrength = 0.0,
                                    signals = com.sleekydz86.backend.domain.model.TradingSignals(
                                        signal = "hold",
                                        confidence = 0.0,
                                        rsi = null,
                                        macd = null,
                                        macdSignal = null
                                    ),
                                    anomalies = emptyList(),
                                    timestamp = java.time.LocalDateTime.now()
                                )
                            )
                        }
                        is DataProcessingException ->
                            ReactiveExceptionHandler.handleDataProcessingError(request, error)
                        else ->
                            ReactiveExceptionHandler.handleGenericError(request, error)
                    }
                }
        } catch (e: Exception) {
            ReactiveExceptionHandler.handleInvalidSymbol(request, e)
        }

    fun getAllAnalysis(request: ServerRequest): Mono<ServerResponse> =
        stockAnalysisService.getAllStockAnalysis()
            .collectList()
            .flatMap { analysis ->
                ServerResponse.ok().bodyValue(analysis)
            }
            .timeout(Duration.ofSeconds(45))
            .onErrorResume { error ->
                when (error) {
                    is java.util.concurrent.TimeoutException ->
                        ReactiveExceptionHandler.handleExternalApiError(request, error)
                    is ExternalApiException ->
                        ReactiveExceptionHandler.handleExternalApiError(request, error)
                    is DataProcessingException ->
                        ReactiveExceptionHandler.handleDataProcessingError(request, error)
                    else ->
                        ReactiveExceptionHandler.handleGenericError(request, error)
                }
            }

    fun getHistoricalData(request: ServerRequest): Mono<ServerResponse> =
        try {
            val symbol = request.pathVariable("symbol")
            if (symbol.isBlank() || !symbol.matches(Regex("[A-Z]{1,5}"))) {
                throw InvalidSymbolException("Invalid stock symbol format")
            }

            val days = try {
                request.queryParam("days")
                    .map { it.toInt() }
                    .orElse(30)
                    .let { d -> if (d in 1..365) d else 30 }
            } catch (e: NumberFormatException) {
                30
            }

            stockAnalysisService.getStockHistoricalData(symbol, days)
                .flatMap { data ->
                    ServerResponse.ok().bodyValue(data)
                }
                .timeout(Duration.ofSeconds(25))
                .onErrorResume { error ->
                    when (error) {
                        is StockNotFoundException ->
                            ReactiveExceptionHandler.handleStockNotFound(request, error)
                        is InvalidSymbolException ->
                            ReactiveExceptionHandler.handleInvalidSymbol(request, error)
                        is java.util.concurrent.TimeoutException ->
                            ReactiveExceptionHandler.handleExternalApiError(request, error)
                        is ExternalApiException ->
                            ReactiveExceptionHandler.handleExternalApiError(request, error)
                        is DataProcessingException ->
                            ReactiveExceptionHandler.handleDataProcessingError(request, error)
                        else ->
                            ReactiveExceptionHandler.handleGenericError(request, error)
                    }
                }
        } catch (e: Exception) {
            ReactiveExceptionHandler.handleInvalidSymbol(request, e)
        }

    fun getRealtimeStream(request: ServerRequest): Mono<ServerResponse> =
        ServerResponse.ok()
            .contentType(MediaType.TEXT_EVENT_STREAM)
            .body(
                stockAnalysisService.getRealtimeAnalysisStream()
                    .onErrorResume { error ->
                        when (error) {
                            is WebSocketException ->
                                Flux.just(TechnicalAnalysis(
                                    symbol = "ERROR",
                                    currentPrice = 0.0,
                                    volume = 0L,
                                    changePercent = 0.0,
                                    trend = "ERROR",
                                    trendStrength = 0.0,
                                    signals = TradingSignals(
                                        signal = "ERROR",
                                        confidence = 0.0,
                                        rsi = null,
                                        macd = null,
                                        macdSignal = null
                                    ),
                                    anomalies = listOf(
                                        Anomaly(
                                            type = "WebSocket Error",
                                            severity = "HIGH",
                                            message = error.message ?: "WebSocket connection error",
                                            timestamp = LocalDateTime.now()
                                        )
                                    ),
                                    timestamp = LocalDateTime.now()
                                ))
                            else ->
                                Flux.error(error)
                        }
                    }
                    .timeout(Duration.ofMinutes(5)),
                TechnicalAnalysis::class.java
            )
}
