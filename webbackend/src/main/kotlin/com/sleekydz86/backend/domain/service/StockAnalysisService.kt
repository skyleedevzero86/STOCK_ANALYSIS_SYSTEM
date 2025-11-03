package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.functional.*
import com.sleekydz86.backend.domain.model.*
import com.sleekydz86.backend.domain.repository.StockRepository
import org.springframework.stereotype.Service
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

@Service
class StockAnalysisService(
    private val stockRepository: StockRepository
) {

    val getRealtimeStockData: (String) -> Mono<StockData> = { symbol ->
        stockRepository.getRealtimeData(symbol)
            .withErrorHandling()
            .withLogging()
            .withTimeout()
    }

    val getAllRealtimeStockData: () -> Flux<StockData> = {
        stockRepository.getAllRealtimeData()
            .withErrorHandling()
            .withLogging("RealtimeData")
            .withTimeout()
    }

    val getStockAnalysis: (String) -> Mono<TechnicalAnalysis> = { symbol ->
        stockRepository.getAnalysis(symbol)
            .withErrorHandling()
            .withLogging()
            .withTimeout()
    }

    val getAllStockAnalysis: () -> Flux<TechnicalAnalysis> = {
        stockRepository.getAllAnalysis()
            .withErrorHandling()
            .withLogging("Analysis")
            .withTimeout()
    }

    val getStockHistoricalData: (String, Int) -> Mono<HistoricalData> = { symbol, days ->
        stockRepository.getHistoricalData(symbol, days)
            .withErrorHandling()
            .withLogging()
            .withTimeout()
    }

    val getAvailableSymbols: () -> Mono<List<String>> = {
        stockRepository.getAvailableSymbols()
            .withErrorHandling()
            .withLogging()
            .withTimeout()
    }

    val getRealtimeAnalysisStream: () -> Flux<TechnicalAnalysis> = {
        Flux.interval(Duration.ofSeconds(5))
            .flatMap { getAllStockAnalysis() }
            .withErrorHandling()
            .withLogging("RealtimeStream")
    }

    val getRealtimeAnalysisStreamWithRetry: () -> Flux<TechnicalAnalysis> = {
        getRealtimeAnalysisStream()
            .withRetry(maxAttempts = 3, delay = Duration.ofSeconds(2))
    }
}
