package com.sleekydz86.backend.infrastructure.cache

import com.sleekydz86.backend.domain.model.StockData
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration
import java.time.LocalDateTime

@Component
class CacheManager(
    private val distributedCacheService: DistributedCacheService,
    private val stockCacheService: StockCacheService
) {

    fun warmUpCache(): Mono<Boolean> {
        return stockCacheService.getAvailableSymbols()
            .flatMap { symbols ->
                Flux.fromIterable(symbols)
                    .flatMap { symbol ->
                        stockCacheService.getStockData(symbol)
                            .switchIfEmpty(
                                Mono.just(
                                    StockData(
                                        symbol = symbol,
                                        currentPrice = 0.0,
                                        volume = 0L,
                                        changePercent = 0.0,
                                        timestamp = LocalDateTime.now()
                                    )
                                )
                                .flatMap { stockData ->
                                    stockCacheService.setStockData(symbol, stockData, Duration.ofMinutes(5))
                                        .then(Mono.just(stockData))
                                }
                            )
                    }
                    .then()
            }
            .then(Mono.just(true))
    }

    fun clearExpiredCache(): Mono<Long> {
        return distributedCacheService.deletePattern("stock:*:expired")
            .onErrorResume { error ->
                Mono.just(0L)
            }
    }

    fun getCacheMetrics(): Mono<Map<String, Any>> {
        return distributedCacheService.get("cache:metrics", Map::class.java)
            .map { it as Map<String, Any> }
            .switchIfEmpty(Mono.just(emptyMap()))
    }

    fun updateCacheMetrics(operation: String, duration: Long): Mono<Boolean> {
        val metricsKey = "cache:metrics"
        val timestamp = LocalDateTime.now().toString()

        return distributedCacheService.get(metricsKey, Map::class.java)
            .switchIfEmpty(Mono.just(emptyMap<String, Any>()))
            .flatMap { currentMetrics ->
                val updatedMetrics = currentMetrics.toMutableMap()
                updatedMetrics["last_operation"] = operation
                updatedMetrics["last_update"] = timestamp
                updatedMetrics["operation_duration"] = duration
                updatedMetrics["total_operations"] = (updatedMetrics["total_operations"] as? Int ?: 0) + 1

                val avgDuration = (updatedMetrics["avg_duration"] as? Double ?: 0.0)
                val totalOps = updatedMetrics["total_operations"] as Int
                val newAvgDuration = (avgDuration * (totalOps - 1) + duration) / totalOps
                updatedMetrics["avg_duration"] = newAvgDuration

                distributedCacheService.set(metricsKey, updatedMetrics, Duration.ofHours(24))
            }
    }

    fun getCacheSize(): Mono<Long> {
        return distributedCacheService.get("cache:size", Long::class.java)
            .switchIfEmpty(Mono.just(0L))
    }

    fun updateCacheSize(delta: Long): Mono<Boolean> {
        val sizeKey = "cache:size"
        return distributedCacheService.get(sizeKey, Long::class.java)
            .switchIfEmpty(Mono.just(0L))
            .flatMap { currentSize ->
                val newSize = currentSize + delta
                distributedCacheService.set(sizeKey, newSize, Duration.ofHours(24))
            }
    }

    fun getCacheHitRate(): Mono<Double> {
        return stockCacheService.getCacheHitRate()
    }

    fun updateCacheHitRate(hit: Boolean): Mono<Boolean> {
        return stockCacheService.updateCacheHitRate(hit)
    }

    fun invalidateCache(pattern: String): Mono<Long> {
        return distributedCacheService.deletePattern(pattern)
    }

    fun invalidateAllCache(): Mono<Boolean> {
        return stockCacheService.invalidateAllStockData()
    }

    fun getCacheKeys(pattern: String = "stock:*"): Flux<String> {
        return distributedCacheService.get("cache:keys:$pattern", List::class.java)
            .map { it as List<String> }
            .flatMapMany { Flux.fromIterable(it) }
            .switchIfEmpty(Flux.empty())
    }

    fun setCacheKeys(pattern: String, keys: List<String>): Mono<Boolean> {
        return distributedCacheService.set("cache:keys:$pattern", keys, Duration.ofMinutes(30))
    }

    fun getCacheTTL(key: String): Mono<Long> {
        return distributedCacheService.get("cache:ttl:$key", Long::class.java)
            .switchIfEmpty(Mono.just(0L))
    }

    fun setCacheTTL(key: String, ttl: Duration): Mono<Boolean> {
        return distributedCacheService.set("cache:ttl:$key", ttl.toMillis(), Duration.ofMinutes(30))
    }

    fun getCacheStats(): Mono<Map<String, Any>> {
        return stockCacheService.getCacheStats()
    }

    fun updateCacheStats(operation: String, symbol: String? = null): Mono<Boolean> {
        return stockCacheService.updateCacheStats(operation, symbol)
    }

    fun optimizeCache(): Mono<Boolean> {
        return clearExpiredCache()
            .then(updateCacheMetrics("optimization", System.currentTimeMillis()))
            .then(Mono.just(true))
            .onErrorResume { error ->
                Mono.just(false)
            }
    }

    fun getCacheHealth(): Mono<Map<String, Any>> {
        return getCacheMetrics()
            .flatMap { metrics ->
                getCacheHitRate()
                    .flatMap { hitRate ->
                        getCacheSize()
                            .map { size ->
                                mapOf(
                                    "status" to "healthy",
                                    "hit_rate" to hitRate,
                                    "cache_size" to size,
                                    "metrics" to metrics,
                                    "timestamp" to LocalDateTime.now().toString()
                                )
                            }
                    }
            }
    }
}