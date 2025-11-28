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

    fun getRealtimeStockData(symbol: String): Mono<StockData> {
        return stockRepository.getRealtimeData(symbol)
            .withErrorHandling()
            .withLogging()
            .withTimeout()
    }

    fun getAllRealtimeStockData(): Flux<StockData> {
        return stockRepository.getAllRealtimeData()
            .withErrorHandling()
            .withLogging("RealtimeData")
            .withTimeout()
    }

    fun getStockAnalysis(symbol: String): Mono<TechnicalAnalysis> {
        return stockRepository.getAnalysis(symbol)
            .withErrorHandling()
            .withLogging()
            .withTimeout()
    }

    fun getAllStockAnalysis(): Flux<TechnicalAnalysis> {
        return stockRepository.getAllAnalysis()
            .withErrorHandling()
            .withLogging("Analysis")
            .timeout(Duration.ofSeconds(90))
    }

    fun getStockHistoricalData(symbol: String, days: Int): Mono<HistoricalData> {
        return stockRepository.getHistoricalData(symbol, days)
            .withErrorHandling()
            .withLogging()
            .withTimeout()
    }

    fun getAvailableSymbols(): Mono<List<String>> {
        return stockRepository.getAvailableSymbols()
            .withErrorHandling()
            .withLogging()
            .withTimeout()
    }

    fun getRealtimeAnalysisStream(): Flux<TechnicalAnalysis> {
        val logger = org.slf4j.LoggerFactory.getLogger(StockAnalysisService::class.java)
        return Flux.interval(Duration.ofSeconds(5))
            .flatMap { 
                getAllStockAnalysis()
                    .onErrorResume { error ->
                        when (error) {
                            is java.util.concurrent.TimeoutException -> {
                                logger.warn("개별 분석 스트림 타임아웃 (계속 진행): ${error.message}")
                            }
                            else -> {
                                logger.warn("개별 분석 스트림 오류 (계속 진행): ${error.message}")
                            }
                        }
                        Flux.empty()
                    }
            }
            .onBackpressureLatest()
            .withErrorHandling()
            .withLogging("RealtimeStream")
    }

    fun getRealtimeAnalysisStreamWithRetry(): Flux<TechnicalAnalysis> {
        return getRealtimeAnalysisStream()
            .withRetry(maxAttempts = 3, delay = Duration.ofSeconds(2))
    }
}
