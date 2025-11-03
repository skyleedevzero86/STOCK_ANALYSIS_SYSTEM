package com.sleekydz86.backend.application.service

import com.sleekydz86.backend.domain.model.HistoricalData
import com.sleekydz86.backend.domain.model.StockData
import com.sleekydz86.backend.domain.model.TechnicalAnalysis
import com.sleekydz86.backend.domain.service.StockAnalysisService
import com.sleekydz86.backend.infrastructure.cache.CacheAnnotation
import com.sleekydz86.backend.infrastructure.cache.CacheManager
import com.sleekydz86.backend.infrastructure.cache.CacheType
import com.sleekydz86.backend.infrastructure.cache.StockCacheService
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration

@Service
class CachedStockAnalysisService(
    private val stockAnalysisService: StockAnalysisService,
    private val stockCacheService: StockCacheService,
    private val cacheManager: CacheManager
) {

    @Cacheable(type = CacheType.STOCK_DATA, ttl = 5)
    fun getRealtimeStockData(symbol: String): Mono<StockData> {
        return stockCacheService.getStockData(symbol)
            .switchIfEmpty(
                stockAnalysisService.getRealtimeStockData(symbol)
                    .flatMap { stockData ->
                        stockCacheService.setStockData(symbol, stockData, Duration.ofMinutes(5))
                            .then(cacheManager.updateCacheHitRate(false))
                            .then(Mono.just(stockData))
                    }
            )
            .flatMap { stockData ->
                cacheManager.updateCacheHitRate(true)
                    .then(cacheManager.updateCacheStats("get_realtime_data", symbol))
                    .then(Mono.just(stockData))
            }
    }

    @Cacheable(type = CacheType.STOCK_ANALYSIS, ttl = 15)
    fun getStockAnalysis(symbol: String): Mono<TechnicalAnalysis> {
        return stockCacheService.getStockAnalysis(symbol)
            .switchIfEmpty(
                stockAnalysisService.getStockAnalysis(symbol)
                    .flatMap { analysis ->
                        stockCacheService.setStockAnalysis(symbol, analysis, Duration.ofMinutes(15))
                            .then(cacheManager.updateCacheHitRate(false))
                            .then(Mono.just(analysis))
                    }
            )
            .flatMap { analysis ->
                cacheManager.updateCacheHitRate(true)
                    .then(cacheManager.updateCacheStats("get_analysis", symbol))
                    .then(Mono.just(analysis))
            }
    }

    @Cacheable(type = CacheType.HISTORICAL_DATA, ttl = 60)
    fun getStockHistoricalData(symbol: String, days: Int): Mono<HistoricalData> {
        return stockCacheService.getHistoricalData(symbol, days)
            .switchIfEmpty(
                stockAnalysisService.getStockHistoricalData(symbol, days)
                    .flatMap { historicalData ->
                        stockCacheService.setHistoricalData(symbol, days, historicalData, Duration.ofHours(1))
                            .then(cacheManager.updateCacheHitRate(false))
                            .then(Mono.just(historicalData))
                    }
            )
            .flatMap { historicalData ->
                cacheManager.updateCacheHitRate(true)
                    .then(cacheManager.updateCacheStats("get_historical_data", symbol))
                    .then(Mono.just(historicalData))
            }
    }

    @Cacheable(type = CacheType.SYMBOLS, ttl = 360)
    fun getAvailableSymbols(): Mono<List<String>> {
        return stockCacheService.getAvailableSymbols()
            .switchIfEmpty(
                stockAnalysisService.getAvailableSymbols()
                    .flatMap { symbols ->
                        stockCacheService.setAvailableSymbols(symbols, Duration.ofHours(6))
                            .then(cacheManager.updateCacheHitRate(false))
                            .then(Mono.just(symbols))
                    }
            )
            .flatMap { symbols ->
                cacheManager.updateCacheHitRate(true)
                    .then(cacheManager.updateCacheStats("get_symbols"))
                    .then(Mono.just(symbols))
            }
    }

    @Cacheable(type = CacheType.ALL_STOCK_DATA, ttl = 5)
    fun getAllRealtimeStockData(): Flux<StockData> {
        return stockCacheService.getAllStockData()
            .switchIfEmpty(
                stockAnalysisService.getAllRealtimeStockData()
                    .collectList()
                    .flatMap { stockDataList ->
                        stockCacheService.setAllStockData(stockDataList, Duration.ofMinutes(5))
                            .then(cacheManager.updateCacheHitRate(false))
                            .then(Flux.fromIterable(stockDataList))
                    }
            )
            .flatMap { stockData ->
                cacheManager.updateCacheHitRate(true)
                    .then(cacheManager.updateCacheStats("get_all_realtime_data"))
                    .then(Mono.just(stockData))
            }
    }

    @Cacheable(type = CacheType.ALL_STOCK_ANALYSIS, ttl = 15)
    fun getAllStockAnalysis(): Flux<TechnicalAnalysis> {
        return stockCacheService.getAllStockAnalysis()
            .switchIfEmpty(
                stockAnalysisService.getAllStockAnalysis()
                    .collectList()
                    .flatMap { analysisList ->
                        stockCacheService.setAllStockAnalysis(analysisList, Duration.ofMinutes(15))
                            .then(cacheManager.updateCacheHitRate(false))
                            .then(Flux.fromIterable(analysisList))
                    }
            )
            .flatMap { analysis ->
                cacheManager.updateCacheHitRate(true)
                    .then(cacheManager.updateCacheStats("get_all_analysis"))
                    .then(Mono.just(analysis))
            }
    }

    fun invalidateStockCache(symbol: String): Mono<Boolean> {
        return stockCacheService.invalidateStockData(symbol)
            .then(stockCacheService.invalidateHistoricalData(symbol))
            .then(cacheManager.updateCacheStats("invalidate_cache", symbol))
    }

    fun invalidateAllCache(): Mono<Boolean> {
        return stockCacheService.invalidateAllStockData()
            .then(cacheManager.invalidateAllCache())
            .then(cacheManager.updateCacheStats("invalidate_all_cache"))
    }

    fun getCacheHealth(): Mono<Map<String, Any>> {
        return cacheManager.getCacheHealth()
    }

    fun getCacheMetrics(): Mono<Map<String, Any>> {
        return cacheManager.getCacheMetrics()
    }

    fun getCacheStats(): Mono<Map<String, Any>> {
        return cacheManager.getCacheStats()
    }

    fun warmUpCache(): Mono<Boolean> {
        return cacheManager.warmUpCache()
    }

    fun optimizeCache(): Mono<Boolean> {
        return cacheManager.optimizeCache()
    }
}