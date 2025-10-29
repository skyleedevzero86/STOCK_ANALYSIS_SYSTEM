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

    private val withErrorHandling = Composition.lift(FunctionalUtils::withErrorHandling)
    private val withLogging = Composition.lift(FunctionalUtils::withLogging)
    private val withTimeout = Composition.lift(FunctionalUtils::withTimeout)

    val getRealtimeStockData: (String) -> Mono<StockData> =
        stockRepository::getRealtimeData
            .andThen(withErrorHandling)
            .andThen(withLogging)
            .andThen(withTimeout)

    val getAllRealtimeStockData: () -> Flux<StockData> =
        stockRepository::getAllRealtimeData
            .andThen { flux -> flux.withErrorHandling() }
            .andThen { flux -> flux.withLogging("RealtimeData") }
            .andThen { flux -> flux.withTimeout() }

    val getStockAnalysis: (String) -> Mono<TechnicalAnalysis> =
        stockRepository::getAnalysis
            .andThen(withErrorHandling)
            .andThen(withLogging)
            .andThen(withTimeout)

    val getAllStockAnalysis: () -> Flux<TechnicalAnalysis> =
        stockRepository::getAllAnalysis
            .andThen { flux -> flux.withErrorHandling() }
            .andThen { flux -> flux.withLogging("Analysis") }
            .andThen { flux -> flux.withTimeout() }

    val getStockHistoricalData: (String, Int) -> Mono<HistoricalData> =
        stockRepository::getHistoricalData
            .andThen(withErrorHandling)
            .andThen(withLogging)
            .andThen(withTimeout)

    val getAvailableSymbols: () -> Mono<List<String>> =
        stockRepository::getAvailableSymbols
            .andThen(withErrorHandling)
            .andThen(withLogging)
            .andThen(withTimeout)

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
