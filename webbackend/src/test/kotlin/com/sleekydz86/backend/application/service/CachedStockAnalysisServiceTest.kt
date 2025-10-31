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
    @DisplayName("실시간 주식 데이터 조회 - 캐시에 데이터가 있을 때 캐시 데이터 반환")
    fun `getRealtimeStockData - should return cached data when available`() {
        //given
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

        //when
        val result = cachedStockAnalysisService.getRealtimeStockData(symbol)

        //then
        StepVerifier.create(result)
            .expectNext(cachedStockData)
            .verifyComplete()
        verify(exactly = 1) { stockCacheService.getStockData(symbol) }
        verify(exactly = 0) { stockAnalysisService.getRealtimeStockData(any()) }
    }

    @Test
    @DisplayName("실시간 주식 데이터 조회 - 캐시에 없을 때 서비스에서 조회 후 캐시에 저장")
    fun `getRealtimeStockData - should fetch from service and cache when not in cache`() {
        //given
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

        //when
        val result = cachedStockAnalysisService.getRealtimeStockData(symbol)

        //then
        StepVerifier.create(result)
            .expectNext(stockData)
            .verifyComplete()
        verify(exactly = 1) { stockCacheService.getStockData(symbol) }
        verify(exactly = 1) { stockAnalysisService.getRealtimeStockData(symbol) }
        verify(exactly = 1) { stockCacheService.setStockData(symbol, stockData, Duration.ofMinutes(5)) }
    }

    @Test
    @DisplayName("주식 분석 조회 - 캐시에 데이터가 있을 때 캐시 데이터 반환")
    fun `getStockAnalysis - should return cached analysis when available`() {
        //given
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

        //when
        val result = cachedStockAnalysisService.getStockAnalysis(symbol)

        //then
        StepVerifier.create(result)
            .expectNext(cachedAnalysis)
            .verifyComplete()
        verify(exactly = 1) { stockCacheService.getStockAnalysis(symbol) }
        verify(exactly = 0) { stockAnalysisService.getStockAnalysis(any()) }
    }

    @Test
    @DisplayName("캐시 무효화 - 특정 심볼의 캐시 무효화")
    fun `invalidateStockCache - should invalidate cache for symbol`() {
        //given
        val symbol = "AAPL"

        every { stockCacheService.invalidateStockData(symbol) } returns Mono.just(true)
        every { stockCacheService.invalidateHistoricalData(symbol) } returns Mono.just(true)
        every { cacheManager.updateCacheStats(any(), any()) } returns Mono.just(true)

        //when
        val result = cachedStockAnalysisService.invalidateStockCache(symbol)

        //then
        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { stockCacheService.invalidateStockData(symbol) }
        verify(exactly = 1) { stockCacheService.invalidateHistoricalData(symbol) }
    }

    @Test
    @DisplayName("전체 캐시 무효화 - 모든 캐시 무효화")
    fun `invalidateAllCache - should invalidate all cache`() {
        //given
        every { stockCacheService.invalidateAllStockData() } returns Mono.just(true)
        every { cacheManager.invalidateAllCache() } returns Mono.just(true)
        every { cacheManager.updateCacheStats(any()) } returns Mono.just(true)

        //when
        val result = cachedStockAnalysisService.invalidateAllCache()

        //then
        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { stockCacheService.invalidateAllStockData() }
        verify(exactly = 1) { cacheManager.invalidateAllCache() }
    }

    @Test
    @DisplayName("캐시 헬스 조회 - 캐시 상태 정보 반환")
    fun `getCacheHealth - should return cache health information`() {
        //given
        val healthData = mapOf(
            "status" to "healthy",
            "hit_rate" to 0.85,
            "cache_size" to 100L
        )

        every { cacheManager.getCacheHealth() } returns Mono.just(healthData)

        //when
        val result = cachedStockAnalysisService.getCacheHealth()

        //then
        StepVerifier.create(result)
            .expectNext(healthData)
            .verifyComplete()
        verify(exactly = 1) { cacheManager.getCacheHealth() }
    }

    @Test
    @DisplayName("캐시 메트릭 조회 - 캐시 메트릭 정보 반환")
    fun `getCacheMetrics - should return cache metrics`() {
        //given
        val metrics = mapOf<String, Any>(
            "hit_rate" to 0.85,
            "miss_rate" to 0.15,
            "total_requests" to 1000
        )

        every { cacheManager.getCacheMetrics() } returns Mono.just(metrics)

        //when
        val result = cachedStockAnalysisService.getCacheMetrics()

        //then
        StepVerifier.create(result)
            .expectNext(metrics)
            .verifyComplete()
        verify(exactly = 1) { cacheManager.getCacheMetrics() }
    }

    @Test
    @DisplayName("캐시 통계 조회 - 캐시 통계 정보 반환")
    fun `getCacheStats - should return cache statistics`() {
        //given
        val stats = mapOf<String, Any>(
            "total_operations" to 1000,
            "cache_hits" to 850,
            "cache_misses" to 150
        )

        every { cacheManager.getCacheStats() } returns Mono.just(stats)

        //when
        val result = cachedStockAnalysisService.getCacheStats()

        //then
        StepVerifier.create(result)
            .expectNext(stats)
            .verifyComplete()
        verify(exactly = 1) { cacheManager.getCacheStats() }
    }

    @Test
    @DisplayName("캐시 워밍업 - 캐시 미리 로드")
    fun `warmUpCache - should warm up cache`() {
        //given
        every { cacheManager.warmUpCache() } returns Mono.just(true)

        //when
        val result = cachedStockAnalysisService.warmUpCache()

        //then
        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { cacheManager.warmUpCache() }
    }

    @Test
    @DisplayName("캐시 최적화 - 캐시 최적화 수행")
    fun `optimizeCache - should optimize cache`() {
        //given
        every { cacheManager.optimizeCache() } returns Mono.just(true)

        //when
        val result = cachedStockAnalysisService.optimizeCache()

        //then
        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { cacheManager.optimizeCache() }
    }
}
