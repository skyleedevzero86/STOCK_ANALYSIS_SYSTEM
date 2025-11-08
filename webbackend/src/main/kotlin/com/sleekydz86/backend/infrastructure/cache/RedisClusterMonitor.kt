package com.sleekydz86.backend.infrastructure.cache

import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import org.slf4j.LoggerFactory
import java.time.Duration
import java.time.LocalDateTime

@Component
class RedisClusterMonitor(
    private val distributedCacheService: DistributedCacheService,
    private val cacheManager: CacheManager,
    private val redisClusterHealthIndicator: RedisClusterHealthIndicator
) {
    private val logger = LoggerFactory.getLogger(RedisClusterMonitor::class.java)

    @Scheduled(fixedRate = 30000)
    fun monitorClusterHealth() {
        if (!distributedCacheService.isRedisConnected()) {
            return
        }

        try {
            redisClusterHealthIndicator.health()
                .let { health ->
                    val healthInfo = mapOf(
                        "status" to health.status.code,
                        "details" to health.details,
                        "timestamp" to LocalDateTime.now().toString()
                    )

                    redisClusterHealthIndicator.updateClusterInfo(healthInfo)
                        .onErrorResume { error ->
                            logger.debug("Redis 클러스터 상태 모니터링 실패", error)
                            Mono.just(false)
                        }
                        .subscribe()
                }
        } catch (e: Exception) {
            logger.debug("클러스터 상태 모니터링 오류: ${e.message}", e)
        }
    }

    @Scheduled(fixedRate = 60000)
    fun monitorCacheMetrics() {
        if (!distributedCacheService.isRedisConnected()) {
            return
        }

        try {
            cacheManager.getCacheMetrics()
                .flatMap { metrics ->
                    val updatedMetrics = metrics.toMutableMap()
                    updatedMetrics["monitor_timestamp"] = LocalDateTime.now().toString()
                    try {
                        updatedMetrics["cluster_health"] = redisClusterHealthIndicator.health().status.code
                    } catch (e: Exception) {
                        updatedMetrics["cluster_health"] = "DOWN"
                    }

                    cacheManager.updateCacheMetrics("monitor", System.currentTimeMillis())
                        .then(Mono.just(updatedMetrics))
                }
                .onErrorResume { error ->
                    logger.debug("캐시 메트릭 모니터링 실패", error)
                    Mono.just(mutableMapOf<String, Any>())
                }
                .subscribe()
        } catch (e: Exception) {
            logger.debug("캐시 메트릭 모니터링 오류: ${e.message}", e)
        }
    }

    @Scheduled(fixedRate = 300000)
    fun optimizeCache() {
        if (!distributedCacheService.isRedisConnected()) {
            return
        }

        try {
            cacheManager.optimizeCache()
                .onErrorResume { error ->
                    logger.debug("캐시 최적화 실패", error)
                    Mono.just(false)
                }
                .subscribe()
        } catch (e: Exception) {
            logger.debug("캐시 최적화 오류: ${e.message}", e)
        }
    }

    @Scheduled(fixedRate = 600000)
    fun cleanupExpiredCache() {
        if (!distributedCacheService.isRedisConnected()) {
            return
        }

        try {
            cacheManager.clearExpiredCache()
                .onErrorResume { error ->
                    logger.debug("캐시 정리 실패", error)
                    Mono.just(0L)
                }
                .subscribe()
        } catch (e: Exception) {
            logger.debug("캐시 정리 오류: ${e.message}", e)
        }
    }

    fun getClusterStatus(): Mono<Map<String, Any>> {
        return redisClusterHealthIndicator.getClusterInfo()
            .flatMap { clusterInfo ->
                cacheManager.getCacheHealth()
                    .map { cacheHealth ->
                        mapOf(
                            "cluster" to clusterInfo,
                            "cache" to cacheHealth,
                            "timestamp" to LocalDateTime.now().toString()
                        )
                    }
            }
    }

    fun getPerformanceMetrics(): Mono<Map<String, Any>> {
        return cacheManager.getCacheMetrics()
            .flatMap { cacheMetrics ->
                cacheManager.getCacheHitRate()
                    .map { hitRate ->
                        mapOf(
                            "cache_metrics" to cacheMetrics,
                            "hit_rate" to hitRate,
                            "performance_score" to calculatePerformanceScore(cacheMetrics, hitRate),
                            "timestamp" to LocalDateTime.now().toString()
                        )
                    }
            }
    }

    private fun calculatePerformanceScore(metrics: Map<String, Any>, hitRate: Double): Double {
        val avgDuration = metrics["avg_duration"] as? Double ?: 0.0
        val totalOperations = metrics["total_operations"] as? Int ?: 0

        val hitRateScore = hitRate * 100
        val durationScore = if (avgDuration > 0) (1000.0 / avgDuration) * 100 else 0.0
        val operationScore = if (totalOperations > 0) (totalOperations / 1000.0) * 100 else 0.0

        return (hitRateScore + durationScore + operationScore) / 3.0
    }

    fun getClusterNodes(): Mono<List<String>> {
        return redisClusterHealthIndicator.getClusterNodes()
    }

    fun setClusterNodes(nodes: List<String>): Mono<Boolean> {
        return redisClusterHealthIndicator.setClusterNodes(nodes)
    }

    fun getClusterStats(): Mono<Map<String, Any>> {
        return redisClusterHealthIndicator.getClusterStats()
    }

    fun updateClusterStats(stats: Map<String, Any>): Mono<Boolean> {
        return redisClusterHealthIndicator.updateClusterStats(stats)
    }
}