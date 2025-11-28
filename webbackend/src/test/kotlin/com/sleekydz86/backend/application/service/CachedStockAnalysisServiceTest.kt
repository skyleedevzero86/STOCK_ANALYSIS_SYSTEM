package com.sleekydz86.backend.application.service

import com.sleekydz86.backend.domain.model.*
import com.sleekydz86.backend.domain.service.StockAnalysisService
import com.sleekydz86.backend.infrastructure.cache.CacheManager
import com.sleekydz86.backend.infrastructure.cache.StockCacheService
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.test.StepVerifier
import java.time.Duration
import java.time.LocalDateTime

class CachedStockAnalysisServiceTest {

    private lateinit var stockAnalysisService: StockAnalysisService
    private lateinit var stockCacheService: StockCacheService
    private lateinit var cacheManager: CacheManager
    private lateinit var cachedStockAnalysisService: CachedStockAnalysisService

    @BeforeEach
    fun setUp() {
        stockAnalysisService = mockk()
        stockCacheService = mockk()
        cacheManager = mockk()
        cachedStockAnalysisService = CachedStockAnalysisService(
            stockAnalysisService,
            stockCacheService,
            cacheManager
        )
    }

    @Test
    @DisplayName("?�시�?주식 ?�이??조회 - 캐시???�이?��? ?�을 ??캐시 ?�이??반환")
    fun `getRealtimeStockData - should return cached data when available`() {

        val symbol = "AAPL"
        val cachedStockData = StockData(
            symbol = symbol,
            currentPrice = 150.0,
            volume = 1000000L,
            changePercent = 2.5,
            timestamp = LocalDateTime.now()
        )

        every { stockCacheService.getStockData(symbol) } returns Mono.just(cachedStockData)
        every { cacheManager.updateCacheHitRate(true) } returns Mono.just(true)
        every { cacheManager.updateCacheStats(any(), any()) } returns Mono.just(true)

        val result = cachedStockAnalysisService.getRealtimeStockData(symbol)

        StepVerifier.create(result)
            .expectNext(cachedStockData)
            .verifyComplete()
        verify(exactly = 1) { stockCacheService.getStockData(symbol) }
        verify(exactly = 0) { stockAnalysisService.getRealtimeStockData(any()) }
    }

    @Test
    @DisplayName("?�시�?주식 ?�이??조회 - 캐시???�을 ???�비?�에??조회 ??캐시???�??)
    fun `getRealtimeStockData - should fetch from service and cache when not in cache`() {

        val symbol = "AAPL"
        val stockData = StockData(
            symbol = symbol,
            currentPrice = 150.0,
            volume = 1000000L,
            changePercent = 2.5,
            timestamp = LocalDateTime.now()
        )

        every { stockCacheService.getStockData(symbol) } returns Mono.empty()
        every { stockAnalysisService.getRealtimeStockData(symbol) } returns Mono.just(stockData)
        every { stockCacheService.setStockData(symbol, stockData, Duration.ofMinutes(5)) } returns Mono.just(true)
        every { cacheManager.updateCacheHitRate(false) } returns Mono.just(true)
        every { cacheManager.updateCacheHitRate(true) } returns Mono.just(true)
        every { cacheManager.updateCacheStats(any(), any()) } returns Mono.just(true)

        val result = cachedStockAnalysisService.getRealtimeStockData(symbol)

        StepVerifier.create(result)
            .expectNext(stockData)
            .verifyComplete()
        verify(exactly = 1) { stockCacheService.getStockData(symbol) }
        verify(exactly = 1) { stockAnalysisService.getRealtimeStockData(symbol) }
        verify(exactly = 1) { stockCacheService.setStockData(symbol, stockData, Duration.ofMinutes(5)) }
    }

    @Test
    @DisplayName("주식 분석 조회 - 캐시???�이?��? ?�을 ??캐시 ?�이??반환")
    fun `getStockAnalysis - should return cached analysis when available`() {

        val symbol = "AAPL"
        val cachedAnalysis = TechnicalAnalysis(
            symbol = symbol,
            currentPrice = 150.0,
            volume = 1000000L,
            changePercent = 2.5,
            trend = "UPWARD",
            trendStrength = 0.8,
            signals = TradingSignals(signal = "BUY", confidence = 0.85, rsi = 65.0, macd = 1.2, macdSignal = 1.0),
            anomalies = emptyList(),
            timestamp = LocalDateTime.now()
        )

        every { stockCacheService.getStockAnalysis(symbol) } returns Mono.just(cachedAnalysis)
        every { cacheManager.updateCacheHitRate(true) } returns Mono.just(true)
        every { cacheManager.updateCacheStats(any(), any()) } returns Mono.just(true)

        val result = cachedStockAnalysisService.getStockAnalysis(symbol)

        StepVerifier.create(result)
            .expectNext(cachedAnalysis)
            .verifyComplete()
        verify(exactly = 1) { stockCacheService.getStockAnalysis(symbol) }
        verify(exactly = 0) { stockAnalysisService.getStockAnalysis(any()) }
    }

    @Test
    @DisplayName("캐시 무효??- ?�정 ?�볼??캐시 무효??)
    fun `invalidateStockCache - should invalidate cache for symbol`() {

        val symbol = "AAPL"

        every { stockCacheService.invalidateStockData(symbol) } returns Mono.just(true)
        every { stockCacheService.invalidateHistoricalData(symbol) } returns Mono.just(true)
        every { cacheManager.updateCacheStats(any(), any()) } returns Mono.just(true)

        val result = cachedStockAnalysisService.invalidateStockCache(symbol)

        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { stockCacheService.invalidateStockData(symbol) }
        verify(exactly = 1) { stockCacheService.invalidateHistoricalData(symbol) }
    }

    @Test
    @DisplayName("?�체 캐시 무효??- 모든 캐시 무효??)
    fun `invalidateAllCache - should invalidate all cache`() {

        every { stockCacheService.invalidateAllStockData() } returns Mono.just(true)
        every { cacheManager.invalidateAllCache() } returns Mono.just(true)
        every { cacheManager.updateCacheStats(any()) } returns Mono.just(true)

        val result = cachedStockAnalysisService.invalidateAllCache()

        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { stockCacheService.invalidateAllStockData() }
        verify(exactly = 1) { cacheManager.invalidateAllCache() }
    }

    @Test
    @DisplayName("캐시 ?�스 조회 - 캐시 ?�태 ?�보 반환")
    fun `getCacheHealth - should return cache health information`() {

        val healthData = mapOf(
            "status" to "healthy",
            "hit_rate" to 0.85,
            "cache_size" to 100L
        )

        every { cacheManager.getCacheHealth() } returns Mono.just(healthData)

        val result = cachedStockAnalysisService.getCacheHealth()

        StepVerifier.create(result)
            .expectNext(healthData)
            .verifyComplete()
        verify(exactly = 1) { cacheManager.getCacheHealth() }
    }

    @Test
    @DisplayName("캐시 메트�?조회 - 캐시 메트�??�보 반환")
    fun `getCacheMetrics - should return cache metrics`() {

        val metrics = mapOf<String, Any>(
            "hit_rate" to 0.85,
            "miss_rate" to 0.15,
            "total_requests" to 1000
        )

        every { cacheManager.getCacheMetrics() } returns Mono.just(metrics)

        val result = cachedStockAnalysisService.getCacheMetrics()

        StepVerifier.create(result)
            .expectNext(metrics)
            .verifyComplete()
        verify(exactly = 1) { cacheManager.getCacheMetrics() }
    }

    @Test
    @DisplayName("캐시 ?�계 조회 - 캐시 ?�계 ?�보 반환")
    fun `getCacheStats - should return cache statistics`() {

        val stats = mapOf<String, Any>(
            "total_operations" to 1000,
            "cache_hits" to 850,
            "cache_misses" to 150
        )

        every { cacheManager.getCacheStats() } returns Mono.just(stats)

        val result = cachedStockAnalysisService.getCacheStats()

        StepVerifier.create(result)
            .expectNext(stats)
            .verifyComplete()
        verify(exactly = 1) { cacheManager.getCacheStats() }
    }

    @Test
    @DisplayName("캐시 ?�밍??- 캐시 미리 로드")
    fun `warmUpCache - should warm up cache`() {

        every { cacheManager.warmUpCache() } returns Mono.just(true)

        val result = cachedStockAnalysisService.warmUpCache()

        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { cacheManager.warmUpCache() }
    }

    @Test
    @DisplayName("캐시 최적??- 캐시 최적???�행")
    fun `optimizeCache - should optimize cache`() {

        every { cacheManager.optimizeCache() } returns Mono.just(true)

        val result = cachedStockAnalysisService.optimizeCache()

        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { cacheManager.optimizeCache() }
    }
}
