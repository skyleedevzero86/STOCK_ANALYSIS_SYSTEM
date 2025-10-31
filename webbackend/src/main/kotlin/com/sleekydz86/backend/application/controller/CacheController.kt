package com.sleekydz86.backend.application.controller

import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration

@RestController
@RequestMapping("/api/cache")
class CacheController(
    private val cachedStockAnalysisService: CachedStockAnalysisService,
    private val cacheManager: CacheManager
) {

    @GetMapping("/health")
    fun getCacheHealth(): Mono<Map<String, Any>> {
        return cachedStockAnalysisService.getCacheHealth()
    }

    @GetMapping("/metrics")
    fun getCacheMetrics(): Mono<Map<String, Any>> {
        return cachedStockAnalysisService.getCacheMetrics()
    }

    @GetMapping("/stats")
    fun getCacheStats(): Mono<Map<String, Any>> {
        return cachedStockAnalysisService.getCacheStats()
    }

    @GetMapping("/hit-rate")
    fun getCacheHitRate(): Mono<Double> {
        return cacheManager.getCacheHitRate()
    }

    @GetMapping("/size")
    fun getCacheSize(): Mono<Long> {
        return cacheManager.getCacheSize()
    }

    @GetMapping("/keys")
    fun getCacheKeys(@RequestParam(defaultValue = "stock:*") pattern: String): Flux<String> {
        return cacheManager.getCacheKeys(pattern)
    }

    @PostMapping("/warm-up")
    fun warmUpCache(): Mono<Boolean> {
        return cachedStockAnalysisService.warmUpCache()
    }

    @PostMapping("/optimize")
    fun optimizeCache(): Mono<Boolean> {
        return cachedStockAnalysisService.optimizeCache()
    }

    @DeleteMapping("/invalidate/{symbol}")
    fun invalidateStockCache(@PathVariable symbol: String): Mono<Boolean> {
        return cachedStockAnalysisService.invalidateStockCache(symbol)
    }

    @DeleteMapping("/invalidate/all")
    fun invalidateAllCache(): Mono<Boolean> {
        return cachedStockAnalysisService.invalidateAllCache()
    }

    @DeleteMapping("/clear")
    fun clearCache(@RequestParam(defaultValue = "stock:*") pattern: String): Mono<Long> {
        return cacheManager.invalidateCache(pattern)
    }

    @GetMapping("/ttl/{key}")
    fun getCacheTTL(@PathVariable key: String): Mono<Long> {
        return cacheManager.getCacheTTL(key)
    }

    @PostMapping("/ttl/{key}")
    fun setCacheTTL(@PathVariable key: String, @RequestParam ttl: Long): Mono<Boolean> {
        return cacheManager.setCacheTTL(key, Duration.ofMillis(ttl))
    }
}




