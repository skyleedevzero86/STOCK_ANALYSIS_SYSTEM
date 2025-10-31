package com.sleekydz86.backend.infrastructure.cache

import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration
import java.time.LocalDateTime

@Service
class StockCacheService(
    private val distributedCacheService: DistributedCacheService
) {

    private val STOCK_DATA_PREFIX = "stock:data:"
    private val STOCK_ANALYSIS_PREFIX = "stock:analysis:"
    private val STOCK_HISTORICAL_PREFIX = "stock:historical:"
    private val STOCK_SYMBOLS_KEY = "stock:symbols"
    private val STOCK_REALTIME_PREFIX = "stock:realtime:"

    fun getStockData(symbol: String): Mono<StockData> {
        val key = "$STOCK_DATA_PREFIX$symbol"
        return distributedCacheService.get(key, StockData::class.java)
    }

    fun setStockData(symbol: String, stockData: StockData, ttl: Duration = Duration.ofMinutes(5)): Mono<Boolean> {
        val key = "$STOCK_DATA_PREFIX$symbol"
        return distributedCacheService.set(key, stockData, ttl)
    }

    fun getStockAnalysis(symbol: String): Mono<TechnicalAnalysis> {
        val key = "$STOCK_ANALYSIS_PREFIX$symbol"
        return distributedCacheService.get(key, TechnicalAnalysis::class.java)
    }

    fun setStockAnalysis(symbol: String, analysis: TechnicalAnalysis, ttl: Duration = Duration.ofMinutes(15)): Mono<Boolean> {
        val key = "$STOCK_ANALYSIS_PREFIX$symbol"
        return distributedCacheService.set(key, analysis, ttl)
    }

    fun getHistoricalData(symbol: String, days: Int): Mono<HistoricalData> {
        val key = "$STOCK_HISTORICAL_PREFIX$symbol:$days"
        return distributedCacheService.get(key, HistoricalData::class.java)
    }

    fun setHistoricalData(symbol: String, days: Int, historicalData: HistoricalData, ttl: Duration = Duration.ofHours(1)): Mono<Boolean> {
        val key = "$STOCK_HISTORICAL_PREFIX$symbol:$days"
        return distributedCacheService.set(key, historicalData, ttl)
    }

    fun getAvailableSymbols(): Mono<List<String>> {
        return distributedCacheService.get(STOCK_SYMBOLS_KEY, List::class.java)
            .map { it as List<String> }
    }

    fun setAvailableSymbols(symbols: List<String>, ttl: Duration = Duration.ofHours(6)): Mono<Boolean> {
        return distributedCacheService.set(STOCK_SYMBOLS_KEY, symbols, ttl)
    }

    fun getAllStockData(): Flux<StockData> {
        return distributedCacheService.getOrSetFlux(
            "stock:all:data",
            StockData::class.java,
            { Flux.empty() },
            Duration.ofMinutes(5)
        )
    }

    fun setAllStockData(stockDataList: List<StockData>, ttl: Duration = Duration.ofMinutes(5)): Mono<Boolean> {
        return distributedCacheService.set("stock:all:data", stockDataList, ttl)
    }

    fun getAllStockAnalysis(): Flux<TechnicalAnalysis> {
        return distributedCacheService.getOrSetFlux(
            "stock:all:analysis",
            TechnicalAnalysis::class.java,
            { Flux.empty() },
            Duration.ofMinutes(15)
        )
    }

    fun setAllStockAnalysis(analysisList: List<TechnicalAnalysis>, ttl: Duration = Duration.ofMinutes(15)): Mono<Boolean> {
        return distributedCacheService.set("stock:all:analysis", analysisList, ttl)
    }

    fun getRealtimeData(symbol: String): Mono<StockData> {
        val key = "$STOCK_REALTIME_PREFIX$symbol"
        return distributedCacheService.get(key, StockData::class.java)
    }

    fun setRealtimeData(symbol: String, stockData: StockData, ttl: Duration = Duration.ofSeconds(30)): Mono<Boolean> {
        val key = "$STOCK_REALTIME_PREFIX$symbol"
        return distributedCacheService.set(key, stockData, ttl)
    }

    fun invalidateStockData(symbol: String): Mono<Boolean> {
        val dataKey = "$STOCK_DATA_PREFIX$symbol"
        val analysisKey = "$STOCK_ANALYSIS_PREFIX$symbol"
        val realtimeKey = "$STOCK_REALTIME_PREFIX$symbol"

        return distributedCacheService.delete(dataKey)
            .then(distributedCacheService.delete(analysisKey))
            .then(distributedCacheService.delete(realtimeKey))
    }

    fun invalidateHistoricalData(symbol: String): Mono<Boolean> {
        val pattern = "$STOCK_HISTORICAL_PREFIX$symbol:*"
        return distributedCacheService.deletePattern(pattern)
            .map { it > 0 }
    }

    fun invalidateAllStockData(): Mono<Boolean> {
        return distributedCacheService.deletePattern("stock:*")
            .map { it > 0 }
    }

    fun getCacheStats(): Mono<Map<String, Any>> {
        return distributedCacheService.get("cache:stats", Map::class.java)
            .map { it as Map<String, Any> }
            .switchIfEmpty(Mono.just(emptyMap()))
    }

    fun updateCacheStats(operation: String, symbol: String? = null): Mono<Boolean> {
        val statsKey = "cache:stats"
        val timestamp = LocalDateTime.now().toString()

        return distributedCacheService.get(statsKey, Map::class.java)
            .switchIfEmpty(Mono.just(emptyMap<String, Any>()))
            .flatMap { currentStats ->
                val updatedStats = currentStats.toMutableMap()
                updatedStats["last_operation"] = operation
                updatedStats["last_symbol"] = symbol
                updatedStats["last_update"] = timestamp
                updatedStats["operation_count"] = (updatedStats["operation_count"] as? Int ?: 0) + 1

                distributedCacheService.set(statsKey, updatedStats, Duration.ofHours(24))
            }
    }

    fun getCacheHitRate(): Mono<Double> {
        return distributedCacheService.get("cache:hit_rate", Double::class.java)
            .switchIfEmpty(Mono.just(0.0))
    }

    fun updateCacheHitRate(hit: Boolean): Mono<Boolean> {
        val hitRateKey = "cache:hit_rate"
        val hitCountKey = "cache:hit_count"
        val missCountKey = "cache:miss_count"

        return if (hit) {
            distributedCacheService.increment(hitCountKey)
                .then(distributedCacheService.get(hitRateKey, Double::class.java)
                    .switchIfEmpty(Mono.just(0.0))
                    .flatMap { currentRate ->
                        distributedCacheService.get(hitCountKey, Long::class.java)
                            .switchIfEmpty(Mono.just(0L))
                            .flatMap { hits ->
                                distributedCacheService.get(missCountKey, Long::class.java)
                                    .switchIfEmpty(Mono.just(0L))
                                    .flatMap { misses ->
                                        val total = hits + misses
                                        val newRate = if (total > 0) hits.toDouble() / total else 0.0
                                        distributedCacheService.set(hitRateKey, newRate, Duration.ofHours(24))
                                    }
                            }
                    })
        } else {
            distributedCacheService.increment(missCountKey)
                .then(distributedCacheService.get(hitRateKey, Double::class.java)
                    .switchIfEmpty(Mono.just(0.0))
                    .flatMap { currentRate ->
                        distributedCacheService.get(hitCountKey, Long::class.java)
                            .switchIfEmpty(Mono.just(0L))
                            .flatMap { hits ->
                                distributedCacheService.get(missCountKey, Long::class.java)
                                    .switchIfEmpty(Mono.just(0L))
                                    .flatMap { misses ->
                                        val total = hits + misses
                                        val newRate = if (total > 0) hits.toDouble() / total else 0.0
                                        distributedCacheService.set(hitRateKey, newRate, Duration.ofHours(24))
                                    }
                            }
                    })
        }
    }
}