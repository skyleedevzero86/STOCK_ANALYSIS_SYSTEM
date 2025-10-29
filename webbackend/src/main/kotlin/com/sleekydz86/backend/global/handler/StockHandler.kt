package com.sleekydz86.backend.global.handler

import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.reactive.function.server.ServerRequest
import org.springframework.web.reactive.function.server.ServerResponse
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration

@Component
class StockHandler(
    private val stockAnalysisService: StockAnalysisService
) {

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

    fun getRealtimeData(request: ServerRequest): Mono<ServerResponse> =
        try {
            val symbol = request.pathVariable("symbol")
            if (symbol.isBlank() || !symbol.matches(Regex("[A-Z]{1,5}"))) {
                throw InvalidSymbolException("Invalid stock symbol format")
            }

            stockAnalysisService.getRealtimeStockData(symbol)
                .flatMap { data ->
                    ServerResponse.ok().bodyValue(data)
                }
                .timeout(Duration.ofSeconds(15))
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
                                    timestamp = System.currentTimeMillis(),
                                    rsi = 0.0,
                                    macd = 0.0,
                                    sma20 = 0.0,
                                    sma50 = 0.0,
                                    ema12 = 0.0,
                                    ema26 = 0.0,
                                    bollingerUpper = 0.0,
                                    bollingerLower = 0.0,
                                    bollingerMiddle = 0.0,
                                    volume = 0.0,
                                    price = 0.0,
                                    change = 0.0,
                                    changePercent = 0.0
                                ))
                            else ->
                                Flux.error(error)
                        }
                    }
                    .timeout(Duration.ofMinutes(5)),
                TechnicalAnalysis::class.java
            )
}
