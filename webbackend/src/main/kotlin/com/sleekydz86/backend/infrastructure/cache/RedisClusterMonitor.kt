package com.sleekydz86.backend.infrastructure.cache

import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import java.time.Duration
import java.time.LocalDateTime

@Component
class RedisClusterMonitor(
    private val distributedCacheService: DistributedCacheService,
    private val cacheManager: CacheManager,
    private val redisClusterHealthIndicator: RedisClusterHealthIndicator
) {

    @Scheduled(fixedRate = 30000)
    fun monitorClusterHealth() {
        redisClusterHealthIndicator.health()
            .let { health ->
                val healthInfo = mapOf(
                    "status" to health.status.code,
                    "details" to health.details,
                    "timestamp" to LocalDateTime.now().toString()
                )

                redisClusterHealthIndicator.updateClusterInfo(healthInfo)
                    .subscribe()
            }
    }

    @Scheduled(fixedRate = 60000)
    fun monitorCacheMetrics() {
        cacheManager.getCacheMetrics()
            .flatMap { metrics ->
                val updatedMetrics = metrics.toMutableMap()
                updatedMetrics["monitor_timestamp"] = LocalDateTime.now().toString()
                updatedMetrics["cluster_health"] = redisClusterHealthIndicator.health().status.code

                cacheManager.updateCacheMetrics("monitor", System.currentTimeMillis())
                    .then(Mono.just(updatedMetrics))
            }
            .subscribe()
    }

    @Scheduled(fixedRate = 300000)
    fun optimizeCache() {
        cacheManager.optimizeCache()
            .subscribe()
    }

    @Scheduled(fixedRate = 600000)
    fun cleanupExpiredCache() {
        cacheManager.clearExpiredCache()
            .subscribe()
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